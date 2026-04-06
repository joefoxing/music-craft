"""Dispatch voice training / conversion jobs to the Modal GPU backend.

Env vars
--------
VC_MODAL_TRAINING_URL   - Modal web endpoint URL for the training function.
VC_MODAL_CONVERSION_URL - Modal web endpoint URL for the conversion function.
VC_MODAL_AUTH_TOKEN     - Bearer token expected by the Modal endpoints (optional).
VC_WEBHOOK_SECRET       - Shared HMAC secret used by Modal to sign callbacks.
BASE_URL                - Public base URL of this Flask app (for Modal callback).
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

log = logging.getLogger(__name__)

_DISPATCH_TIMEOUT = 15  # seconds


def _training_url() -> str | None:
    return os.environ.get('VC_MODAL_TRAINING_URL', '').strip() or None


def _conversion_url() -> str | None:
    return os.environ.get('VC_MODAL_CONVERSION_URL', '').strip() or None


def _auth_token() -> str | None:
    return os.environ.get('VC_MODAL_AUTH_TOKEN', '').strip() or None


def _callback_base() -> str:
    return os.environ.get('BASE_URL', 'http://localhost:5000').rstrip('/')


class DispatchError(Exception):
    pass


def _post(url: str, payload: dict) -> dict:
    body = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=body,
        method='POST',
        headers={'Content-Type': 'application/json'},
    )
    token = _auth_token()
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    with urllib.request.urlopen(req, timeout=_DISPATCH_TIMEOUT) as resp:
        return json.loads(resp.read().decode('utf-8'))


def dispatch_training(job, dataset_files: list) -> str | None:
    """Dispatch a training job to Modal.

    Sends the job payload to ``VC_MODAL_TRAINING_URL``.
    Returns the ``modal_call_id`` string returned by Modal (may be None if
    the endpoint does not echo one back), or raises ``DispatchError`` on any
    HTTP / network failure.
    """
    url = _training_url()
    if not url:
        raise DispatchError('VC_MODAL_TRAINING_URL is not configured')

    payload = {
        'training_job_id': job.id,
        'user_id': job.user_id,
        'profile_id': job.voice_profile_id,
        'dataset_r2_keys': [f.r2_key for f in dataset_files],
        'output_prefix': (
            f'vc/users/{job.user_id}/profiles/{job.voice_profile_id}/models/'
        ),
        'params': job.params_json or {},
        'callback_url': f'{_callback_base()}/api/vc/webhooks/modal',
    }

    try:
        result = _post(url, payload)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='replace')
        raise DispatchError(f'Modal returned HTTP {exc.code}: {body}') from exc
    except urllib.error.URLError as exc:
        raise DispatchError(f'Could not reach Modal endpoint: {exc.reason}') from exc
    except Exception as exc:
        raise DispatchError(str(exc)) from exc

    return (
        result.get('call_id')
        or result.get('modal_call_id')
        or result.get('id')
    )


def dispatch_conversion(job, model_version) -> str | None:
    """Dispatch a conversion job to Modal.

    Sends the job payload to ``VC_MODAL_CONVERSION_URL``.
    Returns the ``modal_call_id`` string returned by Modal (may be None),
    or raises ``DispatchError`` on any HTTP / network failure.
    """
    url = _conversion_url()
    if not url:
        raise DispatchError('VC_MODAL_CONVERSION_URL is not configured')

    payload = {
        'conversion_job_id': job.id,
        'user_id': job.user_id,
        'profile_id': job.voice_profile_id,
        'model_version_id': model_version.id,
        'model_artifact_keys': {
            'r2_model_key': model_version.r2_model_key,
            'r2_config_key': model_version.r2_config_key,
        },
        'input_r2_key': job.input_r2_key,
        'output_r2_key': job.output_r2_key,
        'callback_url': f'{_callback_base()}/api/vc/webhooks/modal',
    }

    try:
        result = _post(url, payload)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='replace')
        raise DispatchError(f'Modal returned HTTP {exc.code}: {body}') from exc
    except urllib.error.URLError as exc:
        raise DispatchError(f'Could not reach Modal endpoint: {exc.reason}') from exc
    except Exception as exc:
        raise DispatchError(str(exc)) from exc

    return (
        result.get('call_id')
        or result.get('modal_call_id')
        or result.get('id')
    )
