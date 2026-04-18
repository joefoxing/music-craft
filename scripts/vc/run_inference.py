from __future__ import annotations

import json
import pathlib

from scripts.vc.common import (
    RunnerContext,
    optional_env,
    require_env,
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


def _speaker_name_from_config(config_path: pathlib.Path) -> str:
    data = json.loads(config_path.read_text(encoding='utf-8'))
    speakers = data.get('spk') or {}
    if isinstance(speakers, dict) and speakers:
        return next(iter(speakers.keys()))
    raise RuntimeError(f'Could not determine speaker name from config: {config_path}')


def main() -> None:
    job_dir = pathlib.Path(require_env('VC_JOB_DIR'))
    artifacts_dir = pathlib.Path(require_env('VC_ARTIFACTS_DIR'))
    payload_path = pathlib.Path(require_env('VC_JOB_PAYLOAD_PATH'))
    repo_dir = pathlib.Path(require_env('SOVITS_REPO_DIR'))
    model_path = pathlib.Path(require_env('VC_MODEL_PATH'))
    config_path = pathlib.Path(require_env('VC_CONFIG_PATH'))
    input_path = pathlib.Path(require_env('VC_INPUT_PATH'))
    output_path = pathlib.Path(require_env('VC_OUTPUT_PATH'))

    if not repo_dir.exists():
        raise RuntimeError(f'SOVITS_REPO_DIR does not exist: {repo_dir}')
    if not model_path.exists():
        raise RuntimeError(f'VC_MODEL_PATH does not exist: {model_path}')
    if not config_path.exists():
        raise RuntimeError(f'VC_CONFIG_PATH does not exist: {config_path}')
    if not input_path.exists():
        raise RuntimeError(f'VC_INPUT_PATH does not exist: {input_path}')

    output_path.parent.mkdir(parents=True, exist_ok=True)

    speaker_name = optional_env('SOVITS_INFER_SPEAKER') or _speaker_name_from_config(config_path)
    transpose = optional_env('SOVITS_INFER_TRANSPOSE', '0')
    f0_method = _normalize_f0_method(optional_env('SOVITS_INFER_F0_METHOD', 'dio'))

    context = RunnerContext(
        job_type='conversion',
        job_id=require_env('VC_JOB_ID'),
        job_dir=job_dir,
        artifacts_dir=artifacts_dir,
        payload_path=payload_path,
        repo_dir=repo_dir,
        model_path=model_path,
        config_path=config_path,
        input_path=input_path,
        output_path=output_path,
        params={
            'speaker_name': speaker_name,
            'transpose': transpose,
            'f0_method': f0_method,
        },
    )

    run_command_template(
        require_env('SOVITS_INFER_CMD_TEMPLATE'),
        context,
        'So-VITS inference',
        _timeout('SOVITS_INFER_TIMEOUT_SEC', 1800),
    )

    if not output_path.exists():
        raise RuntimeError(f'So-VITS inference did not produce output: {output_path}')


if __name__ == '__main__':
    main()