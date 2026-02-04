from __future__ import annotations

import os
import uuid
import shutil
import datetime
import wave
import hmac
import hashlib
import json
from sqlalchemy.exc import IntegrityError

from flask import Blueprint, request, jsonify, current_app, url_for, send_file, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db, csrf
from app.models import GUID


vc_bp = Blueprint('vc', __name__, url_prefix='/api/vc')


def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


def _month_start(dt: datetime.datetime) -> datetime.datetime:
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _day_start(dt: datetime.datetime) -> datetime.datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _vc_storage_root() -> str:
    root = os.path.join(current_app.instance_path, 'vc_storage')
    os.makedirs(root, exist_ok=True)
    return root


def _key_to_path(r2_key: str) -> str:
    safe_rel = r2_key.lstrip('/').replace('..', '')
    path = os.path.join(_vc_storage_root(), safe_rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def _wav_duration_seconds(path: str) -> float | None:
    try:
        with wave.open(path, 'rb') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if not rate:
                return None
            return float(frames) / float(rate)
    except Exception:
        return None


def _get_limits() -> tuple[int, int]:
    trainings_per_month = int(os.environ.get('VC_TRAININGS_PER_MONTH', '3'))
    conversions_per_day = int(os.environ.get('VC_CONVERSIONS_PER_DAY', '3'))
    return trainings_per_month, conversions_per_day


def _webhook_secret() -> str:
    return os.environ.get('VC_WEBHOOK_SECRET', '')


def _normalize_job_type(job_type: str | None) -> str | None:
    if not job_type:
        return None
    jt = str(job_type).strip().lower()
    if jt in ['training', 'train', 'voice_training', 'voice-train']:
        return 'training'
    if jt in ['conversion', 'convert', 'inference', 'voice_conversion', 'voice-convert']:
        return 'conversion'
    return jt


def _normalize_status(status: str | None) -> str | None:
    if not status:
        return None
    s = str(status).strip().lower()
    if s in ['success', 'succeed', 'succeeded', 'completed', 'complete', 'done', 'ok']:
        return 'succeeded'
    if s in ['fail', 'failed', 'error']:
        return 'failed'
    if s in ['cancel', 'canceled', 'cancelled']:
        return 'canceled'
    if s in ['running', 'in_progress', 'in-progress', 'processing']:
        return 'running'
    if s in ['queued', 'pending']:
        return 'queued'
    return s


def _is_terminal(status: str | None) -> bool:
    return status in ['succeeded', 'failed', 'canceled']


def _status_rank(status: str | None) -> int:
    ranks = {
        None: 0,
        'queued': 1,
        'running': 2,
        'succeeded': 3,
        'failed': 3,
        'canceled': 3,
    }
    return ranks.get(status, 0)


def _should_apply_transition(current: str | None, incoming: str | None) -> bool:
    """Monotonic transitions only; never mutate after terminal state."""
    if incoming is None:
        return False
    if _is_terminal(current):
        return False
    return _status_rank(incoming) >= _status_rank(current)


def _verify_modal_webhook(req) -> tuple[str, dict]:
    """Verify webhook signature + timestamp; return (event_id, payload)."""
    secret = _webhook_secret()
    if not secret:
        abort(500)

    ts = req.headers.get('X-VC-Timestamp')
    sig = req.headers.get('X-VC-Signature')

    if not ts or not sig:
        abort(401)

    try:
        ts_int = int(ts)
    except Exception:
        abort(401)

    now_int = int(_now().timestamp())
    if abs(now_int - ts_int) > 300:
        abort(401)

    body = req.get_data() or b''
    signed_payload = f"{ts}.{body.decode('utf-8', errors='replace')}".encode('utf-8')
    expected = hmac.new(secret.encode('utf-8'), signed_payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        abort(401)

    payload = req.get_json(silent=True)
    if payload is None:
        try:
            payload = json.loads(body.decode('utf-8'))
        except Exception:
            abort(400)

    event_id = payload.get('event_id')
    if not event_id:
        abort(400)

    return str(event_id), payload


def _remaining_quotas(user_id: str) -> dict:
    from app.models import VoiceTrainingJob, VoiceConversionJob

    trainings_per_month, conversions_per_day = _get_limits()
    now = _now()

    month_used = VoiceTrainingJob.query.filter(
        VoiceTrainingJob.user_id == user_id,
        VoiceTrainingJob.status == 'succeeded',
        VoiceTrainingJob.finished_at >= _month_start(now),
    ).count()

    day_used = VoiceConversionJob.query.filter(
        VoiceConversionJob.user_id == user_id,
        VoiceConversionJob.status == 'succeeded',
        VoiceConversionJob.finished_at >= _day_start(now),
    ).count()

    return {
        'trainings_per_month': trainings_per_month,
        'conversions_per_day': conversions_per_day,
        'trainings_used': month_used,
        'conversions_used': day_used,
        'trainings_remaining': max(0, trainings_per_month - month_used),
        'conversions_remaining': max(0, conversions_per_day - day_used),
    }


@vc_bp.route('/profiles', methods=['GET'])
@login_required
def list_profiles():
    from app.models import VoiceProfile

    profiles = VoiceProfile.query.filter_by(user_id=current_user.id).order_by(VoiceProfile.created_at.desc()).all()
    return jsonify([{'id': p.id, 'name': p.name, 'status': p.status} for p in profiles])


@vc_bp.route('/profiles', methods=['POST'])
@login_required
def create_profile():
    from app.models import VoiceProfile

    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'name is required'}), 400

    profile = VoiceProfile(user_id=current_user.id, name=name, status='draft')
    db.session.add(profile)
    db.session.commit()
    return jsonify({'id': profile.id, 'name': profile.name, 'status': profile.status})


@vc_bp.route('/profiles/<profile_id>', methods=['GET'])
@login_required
def profile_detail(profile_id: str):
    from app.models import VoiceProfile, VoiceDatasetFile, VoiceTrainingJob, VoiceConversionJob, VoiceModelVersion

    profile = VoiceProfile.query.filter_by(id=profile_id, user_id=current_user.id).first()
    if not profile:
        return jsonify({'error': 'profile not found'}), 404

    files = VoiceDatasetFile.query.filter_by(voice_profile_id=profile.id).all()
    total_seconds = 0.0
    for f in files:
        if f.duration_sec:
            total_seconds += float(f.duration_sec)

    trainings_per_month, conversions_per_day = _get_limits()
    now = _now()

    month_used = VoiceTrainingJob.query.filter(
        VoiceTrainingJob.user_id == current_user.id,
        VoiceTrainingJob.status == 'succeeded',
        VoiceTrainingJob.finished_at >= _month_start(now),
    ).count()

    day_used = VoiceConversionJob.query.filter(
        VoiceConversionJob.user_id == current_user.id,
        VoiceConversionJob.status == 'succeeded',
        VoiceConversionJob.finished_at >= _day_start(now),
    ).count()

    active_model = None
    if profile.active_model_version_id:
        mv = VoiceModelVersion.query.filter_by(id=profile.active_model_version_id, voice_profile_id=profile.id).first()
        if mv and mv.status == 'ready':
            active_model = mv.id

    return jsonify({
        'id': profile.id,
        'name': profile.name,
        'status': profile.status,
        'dataset': {
            'total_files': len(files),
            'total_minutes': round(total_seconds / 60.0, 2),
        },
        'active_model': active_model,
        'trainings_remaining': max(0, trainings_per_month - month_used),
        'conversions_remaining': max(0, conversions_per_day - day_used),
    })


@vc_bp.route('/profiles/<profile_id>/dataset/upload-url', methods=['POST'])
@login_required
def dataset_upload_url(profile_id: str):
    from app.models import VoiceProfile, VoiceDatasetFile

    profile = VoiceProfile.query.filter_by(id=profile_id, user_id=current_user.id).first()
    if not profile:
        return jsonify({'error': 'profile not found'}), 404

    data = request.get_json(silent=True) or {}
    filename = secure_filename((data.get('filename') or 'dataset.wav').strip())
    size_bytes = int(data.get('size_bytes') or 0)
    mime = (data.get('mime') or '').strip() or None

    file_id = str(uuid.uuid4())
    r2_key = f"vc/users/{current_user.id}/profiles/{profile.id}/dataset/{file_id}/{filename}"

    dsf = VoiceDatasetFile(
        id=file_id,
        voice_profile_id=profile.id,
        r2_key=r2_key,
        filename=filename,
        duration_sec=None,
        size_bytes=size_bytes,
        sha256=None,
        mime=mime,
    )

    db.session.add(dsf)
    db.session.commit()

    upload_url = url_for('vc.put_object', upload_id=file_id, _external=False)
    return jsonify({'upload_url': upload_url, 'r2_key': r2_key, 'file_id': file_id})


@vc_bp.route('/uploads/<upload_id>', methods=['PUT'])
@csrf.exempt
@login_required
def put_object(upload_id: str):
    from app.models import VoiceDatasetFile

    dsf = VoiceDatasetFile.query.get(upload_id)
    if not dsf:
        return jsonify({'error': 'upload not found'}), 404

    profile = dsf.voice_profile
    if not profile or profile.user_id != current_user.id:
        return jsonify({'error': 'forbidden'}), 403

    path = _key_to_path(dsf.r2_key)
    body = request.get_data() or b''
    with open(path, 'wb') as f:
        f.write(body)

    return jsonify({'ok': True})


@vc_bp.route('/profiles/<profile_id>/dataset/commit', methods=['POST'])
@login_required
def dataset_commit(profile_id: str):
    from app.models import VoiceProfile, VoiceDatasetFile

    profile = VoiceProfile.query.filter_by(id=profile_id, user_id=current_user.id).first()
    if not profile:
        return jsonify({'error': 'profile not found'}), 404

    data = request.get_json(silent=True) or {}
    file_id = data.get('file_id')

    if not file_id:
        return jsonify({'error': 'file_id is required'}), 400

    dsf = VoiceDatasetFile.query.filter_by(id=file_id, voice_profile_id=profile.id).first()
    if not dsf:
        return jsonify({'error': 'dataset file not found'}), 404

    path = _key_to_path(dsf.r2_key)
    if not os.path.exists(path):
        return jsonify({'error': 'object not uploaded'}), 400

    duration = _wav_duration_seconds(path)
    if duration is not None:
        dsf.duration_sec = duration

    if 'size_bytes' in data:
        try:
            dsf.size_bytes = int(data.get('size_bytes') or dsf.size_bytes or 0)
        except Exception:
            pass

    db.session.commit()
    return jsonify({'ok': True, 'file_id': dsf.id})


@vc_bp.route('/dataset-files/<file_id>', methods=['DELETE'])
@login_required
def delete_dataset_file(file_id: str):
    from app.models import VoiceDatasetFile

    dsf = VoiceDatasetFile.query.get(file_id)
    if not dsf or not dsf.voice_profile or dsf.voice_profile.user_id != current_user.id:
        return jsonify({'error': 'not found'}), 404

    path = _key_to_path(dsf.r2_key)
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

    db.session.delete(dsf)
    db.session.commit()
    return jsonify({'ok': True})


@vc_bp.route('/profiles/<profile_id>/train', methods=['POST'])
@login_required
def start_training(profile_id: str):
    from app.models import VoiceProfile, VoiceTrainingJob, VoiceModelVersion

    profile = VoiceProfile.query.filter_by(id=profile_id, user_id=current_user.id).first()
    if not profile:
        return jsonify({'error': 'profile not found'}), 404

    quotas = _remaining_quotas(current_user.id)
    now = _now()

    if quotas['trainings_remaining'] <= 0:
        payload = {'error': 'training quota exceeded'}
        payload.update(quotas)
        return jsonify(payload), 429

    running = VoiceTrainingJob.query.filter(
        VoiceTrainingJob.user_id == current_user.id,
        VoiceTrainingJob.status.in_(['queued', 'running']),
    ).first()

    if running:
        return jsonify({'error': 'a training job is already running'}), 409

    data = request.get_json(silent=True) or {}
    params_json = {
        'epochs': data.get('epochs'),
        'f0_method': data.get('f0_method'),
    }

    job = VoiceTrainingJob(
        user_id=current_user.id,
        voice_profile_id=profile.id,
        status='queued',
        modal_call_id=None,
        params_json=params_json,
        error=None,
        created_at=now,
        started_at=now,
        finished_at=None,
    )

    db.session.add(job)
    db.session.flush()

    job.status = 'succeeded'
    job.finished_at = _now()

    model_version_id = str(uuid.uuid4())
    mv = VoiceModelVersion(
        id=model_version_id,
        voice_profile_id=profile.id,
        training_job_id=job.id,
        status='ready',
        r2_model_key=f"vc/users/{current_user.id}/profiles/{profile.id}/models/{model_version_id}/model.pth",
        r2_config_key=f"vc/users/{current_user.id}/profiles/{profile.id}/models/{model_version_id}/config.json",
        metrics_json={},
    )

    db.session.add(mv)
    profile.active_model_version_id = mv.id
    profile.status = 'ready'

    db.session.commit()

    return jsonify({'id': job.id, 'status': job.status})


@vc_bp.route('/training-jobs/<job_id>', methods=['GET'])
@login_required
def get_training_job(job_id: str):
    from app.models import VoiceTrainingJob

    job = VoiceTrainingJob.query.filter_by(id=job_id, user_id=current_user.id).first()
    if not job:
        return jsonify({'error': 'not found'}), 404

    return jsonify({
        'id': job.id,
        'status': job.status,
        'error': job.error,
        'created_at': job.created_at.isoformat() if job.created_at else None,
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'finished_at': job.finished_at.isoformat() if job.finished_at else None,
    })


@vc_bp.route('/profiles/<profile_id>/convert/upload-url', methods=['POST'])
@login_required
def conversion_upload_url(profile_id: str):
    from app.models import VoiceProfile

    profile = VoiceProfile.query.filter_by(id=profile_id, user_id=current_user.id).first()
    if not profile:
        return jsonify({'error': 'profile not found'}), 404

    data = request.get_json(silent=True) or {}
    filename = secure_filename((data.get('filename') or 'input.wav').strip())

    upload_id = str(uuid.uuid4())
    r2_key = f"vc/users/{current_user.id}/profiles/{profile.id}/conversions/{upload_id}/input/{filename}"

    upload_url = url_for('vc.put_conversion_input', upload_id=upload_id, _external=False)
    return jsonify({'upload_url': upload_url, 'r2_key': r2_key})


@vc_bp.route('/uploads/conversion-input/<upload_id>', methods=['PUT'])
@csrf.exempt
@login_required
def put_conversion_input(upload_id: str):
    data = request.get_data() or b''
    path = os.path.join(_vc_storage_root(), 'conversion_inputs', current_user.id, f"{upload_id}.bin")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)
    return jsonify({'ok': True})


@vc_bp.route('/profiles/<profile_id>/convert', methods=['POST'])
@login_required
def start_conversion(profile_id: str):
    from app.models import VoiceProfile, VoiceConversionJob, VoiceModelVersion

    profile = VoiceProfile.query.filter_by(id=profile_id, user_id=current_user.id).first()
    if not profile:
        return jsonify({'error': 'profile not found'}), 404

    if not profile.active_model_version_id:
        return jsonify({'error': 'no active model for this profile'}), 400

    mv = VoiceModelVersion.query.filter_by(id=profile.active_model_version_id, voice_profile_id=profile.id).first()
    if not mv or mv.status != 'ready':
        return jsonify({'error': 'active model not ready'}), 400

    quotas = _remaining_quotas(current_user.id)
    now = _now()

    if quotas['conversions_remaining'] <= 0:
        payload = {'error': 'conversion quota exceeded'}
        payload.update(quotas)
        return jsonify(payload), 429

    running = VoiceConversionJob.query.filter(
        VoiceConversionJob.user_id == current_user.id,
        VoiceConversionJob.status.in_(['queued', 'running']),
    ).first()

    if running:
        return jsonify({'error': 'a conversion job is already running'}), 409

    data = request.get_json(silent=True) or {}
    input_r2_key = (data.get('input_r2_key') or '').strip()
    if not input_r2_key:
        return jsonify({'error': 'input_r2_key is required'}), 400

    job_id = str(uuid.uuid4())
    output_r2_key = f"vc/users/{current_user.id}/profiles/{profile.id}/conversions/{job_id}/output.wav"

    job = VoiceConversionJob(
        id=job_id,
        user_id=current_user.id,
        voice_profile_id=profile.id,
        model_version_id=mv.id,
        status='queued',
        modal_call_id=None,
        input_r2_key=input_r2_key,
        output_r2_key=output_r2_key,
        input_duration_sec=None,
        error=None,
        created_at=now,
        finished_at=None,
    )

    db.session.add(job)
    db.session.flush()

    input_path = os.path.join(_vc_storage_root(), 'conversion_inputs', current_user.id)
    in_file = None
    try:
        for fn in os.listdir(input_path):
            if fn.startswith('') and fn.endswith('.bin'):
                pass
    except Exception:
        pass

    try:
        blob_id = input_r2_key.split('/conversions/', 1)[1].split('/', 1)[0]
        in_file = os.path.join(input_path, f"{blob_id}.bin")
    except Exception:
        in_file = None

    if not in_file or not os.path.exists(in_file):
        job.status = 'failed'
        job.error = 'input not uploaded'
        job.finished_at = _now()
        db.session.commit()
        return jsonify({'id': job.id, 'status': job.status, 'error': job.error}), 400

    out_path = _key_to_path(output_r2_key)

    try:
        shutil.copyfile(in_file, out_path)
        job.status = 'succeeded'
        job.finished_at = _now()
    except Exception as e:
        job.status = 'failed'
        job.error = str(e)
        job.finished_at = _now()

    db.session.commit()
    return jsonify({'id': job.id, 'status': job.status})


@vc_bp.route('/conversion-jobs/<job_id>', methods=['GET'])
@login_required
def get_conversion_job(job_id: str):
    from app.models import VoiceConversionJob

    job = VoiceConversionJob.query.filter_by(id=job_id, user_id=current_user.id).first()
    if not job:
        return jsonify({'error': 'not found'}), 404

    return jsonify({
        'id': job.id,
        'status': job.status,
        'error': job.error,
        'output_r2_key': job.output_r2_key,
        'created_at': job.created_at.isoformat() if job.created_at else None,
        'finished_at': job.finished_at.isoformat() if job.finished_at else None,
    })


@vc_bp.route('/conversion-jobs/<job_id>/download', methods=['GET'])
@login_required
def download_conversion(job_id: str):
    from app.models import VoiceConversionJob

    job = VoiceConversionJob.query.filter_by(id=job_id, user_id=current_user.id).first()
    if not job:
        return jsonify({'error': 'not found'}), 404

    if job.status != 'succeeded' or not job.output_r2_key:
        return jsonify({'error': 'output not ready'}), 400

    path = _key_to_path(job.output_r2_key)
    if not os.path.exists(path):
        return jsonify({'error': 'file missing'}), 404

    return send_file(path, mimetype='audio/wav', as_attachment=True, download_name='output.wav')


@vc_bp.route('/webhooks/modal', methods=['POST'])
@csrf.exempt
def modal_webhook():
    from app.models import WebhookEvent, VoiceTrainingJob, VoiceConversionJob, VoiceModelVersion

    event_id, payload = _verify_modal_webhook(request)

    existing = WebhookEvent.query.filter_by(source='modal', event_id=event_id).first()
    if existing:
        return jsonify({'ok': True, 'idempotent': True})

    try:
        db.session.add(WebhookEvent(source='modal', event_id=event_id))
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'ok': True, 'idempotent': True})

    job_type = _normalize_job_type(payload.get('job_type'))
    job_id = payload.get('job_id') or payload.get('training_job_id') or payload.get('conversion_job_id')
    status = _normalize_status(payload.get('status'))
    error = payload.get('error')

    if job_type == 'training':
        job = VoiceTrainingJob.query.filter_by(id=job_id).first()
        if job:
            if _should_apply_transition(job.status, status):
                job.status = status

            if status == 'running' and not job.started_at:
                job.started_at = _now()

            if _is_terminal(status):
                if not job.finished_at:
                    job.finished_at = _now()
                if error:
                    job.error = error

            if status == 'succeeded':
                artifact_keys = payload.get('artifact_keys') or {}
                if isinstance(artifact_keys, list):
                    artifact_keys = {}

                model_key = (
                    artifact_keys.get('r2_model_key')
                    or artifact_keys.get('model')
                    or payload.get('r2_model_key')
                )
                config_key = (
                    artifact_keys.get('r2_config_key')
                    or artifact_keys.get('config')
                    or payload.get('r2_config_key')
                )

                existing_mv = VoiceModelVersion.query.filter_by(training_job_id=job.id).first()
                if existing_mv:
                    if model_key and not existing_mv.r2_model_key:
                        existing_mv.r2_model_key = model_key
                    if config_key and not existing_mv.r2_config_key:
                        existing_mv.r2_config_key = config_key
                    if payload.get('metrics') and not existing_mv.metrics_json:
                        existing_mv.metrics_json = payload.get('metrics')
                    mv = existing_mv
                else:
                    model_version_id = str(uuid.uuid4())
                    mv = VoiceModelVersion(
                        id=model_version_id,
                        voice_profile_id=job.voice_profile_id,
                        training_job_id=job.id,
                        status='ready',
                        r2_model_key=model_key,
                        r2_config_key=config_key,
                        metrics_json=payload.get('metrics') or {},
                    )
                    db.session.add(mv)

                vp = job.voice_profile
                if vp:
                    vp.active_model_version_id = mv.id
                    vp.status = 'ready'

    elif job_type == 'conversion':
        job = VoiceConversionJob.query.filter_by(id=job_id).first()
        if job:
            if _should_apply_transition(job.status, status):
                job.status = status

            if _is_terminal(status):
                if not job.finished_at:
                    job.finished_at = _now()
                if error:
                    job.error = error

            output_key = payload.get('output_key') or payload.get('output_r2_key') or payload.get('output_key_r2')
            if output_key:
                job.output_r2_key = output_key

    db.session.commit()
    return jsonify({'ok': True})
