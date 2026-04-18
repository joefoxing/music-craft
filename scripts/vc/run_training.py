from __future__ import annotations

import pathlib
import re
import shutil

from scripts.vc.common import (
    RunnerContext,
    copy_artifact,
    ensure_dir,
    optional_env,
    require_env,
    read_json_env,
    resolve_source,
    run_command_template,
)


def _timeout(name: str, default: int) -> int:
    raw = optional_env(name, str(default))
    try:
        return int(raw)
    except Exception:
        return default


def _normalize_f0_method(value: str | None) -> str:
    raw = (value or '').strip().lower()
    if raw in {'rmvpe', 'fcpe', 'pm', ''}:
        return 'dio'
    if raw in {'crepe', 'crepe-tiny', 'parselmouth', 'dio', 'harvest'}:
        return raw
    return 'dio'


def _speaker_name(raw: str | None) -> str:
    candidate = re.sub(r'[^A-Za-z0-9_-]+', '-', (raw or '').strip()).strip('-')
    return candidate or 'target'


def _stage_dataset(dataset_dir: pathlib.Path, dataset_raw_dir: pathlib.Path, speaker_name: str) -> None:
    speaker_dir = ensure_dir(dataset_raw_dir / speaker_name)
    files = sorted(path for path in dataset_dir.iterdir() if path.is_file())
    if not files:
        raise RuntimeError(f'VC_DATASET_DIR does not contain any files: {dataset_dir}')

    for index, source in enumerate(files, start=1):
        suffix = source.suffix or '.wav'
        destination = speaker_dir / f'{index:04d}{suffix}'
        shutil.copy2(source, destination)


def main() -> None:
    job_dir = pathlib.Path(require_env('VC_JOB_DIR'))
    artifacts_dir = pathlib.Path(require_env('VC_ARTIFACTS_DIR'))
    dataset_dir = pathlib.Path(require_env('VC_DATASET_DIR'))
    payload_path = pathlib.Path(require_env('VC_JOB_PAYLOAD_PATH'))
    repo_dir = pathlib.Path(require_env('SOVITS_REPO_DIR'))
    params = read_json_env('VC_PARAMS_JSON', default={})

    if not repo_dir.exists():
        raise RuntimeError(f'SOVITS_REPO_DIR does not exist: {repo_dir}')
    if not dataset_dir.exists():
        raise RuntimeError(f'VC_DATASET_DIR does not exist: {dataset_dir}')

    workspace_dir = ensure_dir(pathlib.Path(optional_env('SOVITS_WORKSPACE_DIR', str(job_dir / 'workspace'))))
    speaker_name = _speaker_name(optional_env('SOVITS_SPEAKER_NAME', params.get('speaker_name') or 'target'))
    sample_rate = optional_env('SOVITS_SAMPLE_RATE', '44100')
    config_type = optional_env('SOVITS_CONFIG_TYPE', 'so-vits-svc-4.0v1')
    dataset_raw_dir = ensure_dir(pathlib.Path(optional_env('SOVITS_RAW_DATA_DIR', str(workspace_dir / 'dataset_raw'))))
    processed_data_dir = ensure_dir(pathlib.Path(optional_env('SOVITS_PROCESSED_DATA_DIR', str(workspace_dir / 'dataset' / '44k'))))
    filelists_dir = ensure_dir(pathlib.Path(optional_env('SOVITS_FILELISTS_DIR', str(workspace_dir / 'filelists' / '44k'))))
    config_output_path = pathlib.Path(optional_env('SOVITS_CONFIG_OUTPUT_PATH', str(workspace_dir / 'configs' / '44k' / 'config.json')))
    model_dir = ensure_dir(pathlib.Path(optional_env('SOVITS_LOGS_DIR', str(workspace_dir / 'logs' / '44k'))))

    _stage_dataset(dataset_dir, dataset_raw_dir, speaker_name)

    context = RunnerContext(
        job_type='training',
        job_id=require_env('VC_JOB_ID'),
        job_dir=job_dir,
        artifacts_dir=artifacts_dir,
        payload_path=payload_path,
        dataset_dir=dataset_dir,
        repo_dir=repo_dir,
        params=params,
    )

    resample_template = optional_env('SOVITS_RESAMPLE_CMD_TEMPLATE')
    config_template = optional_env('SOVITS_CONFIG_CMD_TEMPLATE')
    hubert_template = optional_env('SOVITS_HUBERT_CMD_TEMPLATE')
    train_template = require_env('SOVITS_TRAIN_CMD_TEMPLATE')

    extra_context = RunnerContext(
        job_type=context.job_type,
        job_id=context.job_id,
        job_dir=context.job_dir,
        artifacts_dir=context.artifacts_dir,
        payload_path=context.payload_path,
        dataset_dir=context.dataset_dir,
        repo_dir=context.repo_dir,
        params={
            **params,
            'workspace_dir': str(workspace_dir),
            'speaker_name': speaker_name,
            'sample_rate': sample_rate,
            'config_type': config_type,
            'dataset_raw_dir': str(dataset_raw_dir),
            'processed_data_dir': str(processed_data_dir),
            'filelists_dir': str(filelists_dir),
            'model_dir': str(model_dir),
            'config_output_path': str(config_output_path),
            'f0_method': _normalize_f0_method(params.get('f0_method')),
        },
    )

    if resample_template:
        run_command_template(resample_template, extra_context, 'So-VITS resample', _timeout('SOVITS_RESAMPLE_TIMEOUT_SEC', 1800))
    if config_template:
        run_command_template(config_template, extra_context, 'So-VITS config generation', _timeout('SOVITS_CONFIG_TIMEOUT_SEC', 1800))
    if hubert_template:
        run_command_template(hubert_template, extra_context, 'So-VITS HuBERT/F0 preprocessing', _timeout('SOVITS_HUBERT_TIMEOUT_SEC', 3600))

    run_command_template(train_template, extra_context, 'So-VITS training', _timeout('SOVITS_TRAIN_TIMEOUT_SEC', 10800))

    model_source = resolve_source(require_env('SOVITS_MODEL_SOURCE'), extra_context, 'SOVITS_MODEL_SOURCE')
    config_source = resolve_source(optional_env('SOVITS_CONFIG_SOURCE', str(config_output_path)), extra_context, 'SOVITS_CONFIG_SOURCE')
    metrics_source_value = optional_env('SOVITS_METRICS_SOURCE')

    copy_artifact(model_source, artifacts_dir / 'model.pth')
    copy_artifact(config_source, artifacts_dir / 'config.json')

    if metrics_source_value:
        metrics_source = resolve_source(metrics_source_value, extra_context, 'SOVITS_METRICS_SOURCE')
        copy_artifact(metrics_source, artifacts_dir / 'metrics.json')


if __name__ == '__main__':
    main()