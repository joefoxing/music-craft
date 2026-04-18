from __future__ import annotations

import argparse
import os
import pathlib
import sys

from scripts.vc.common import RunnerContext, build_template_vars, optional_env, require_env


def _dummy_context(mode: str) -> RunnerContext:
    job_dir = pathlib.Path(optional_env('VC_JOB_DIR', '/tmp/vc-job'))
    artifacts_dir = pathlib.Path(optional_env('VC_ARTIFACTS_DIR', str(job_dir / 'artifacts')))
    payload_path = pathlib.Path(optional_env('VC_JOB_PAYLOAD_PATH', str(job_dir / 'job_payload.json')))
    repo_dir = pathlib.Path(optional_env('SOVITS_REPO_DIR', '/root/so-vits-svc'))
    dataset_dir = pathlib.Path(optional_env('VC_DATASET_DIR', str(job_dir / 'dataset')))
    model_path = pathlib.Path(optional_env('VC_MODEL_PATH', str(job_dir / 'model.pth')))
    config_path = pathlib.Path(optional_env('VC_CONFIG_PATH', str(job_dir / 'config.json')))
    input_path = pathlib.Path(optional_env('VC_INPUT_PATH', str(job_dir / 'input.wav')))
    output_path = pathlib.Path(optional_env('VC_OUTPUT_PATH', str(artifacts_dir / 'output.wav')))

    params = {
        'epochs': optional_env('VC_SMOKE_EPOCHS', '50'),
        'f0_method': optional_env('VC_SMOKE_F0_METHOD', 'dio'),
        'workspace_dir': optional_env('SOVITS_WORKSPACE_DIR', str(job_dir / 'workspace')),
        'speaker_name': optional_env('SOVITS_SPEAKER_NAME', 'target'),
        'sample_rate': optional_env('SOVITS_SAMPLE_RATE', '44100'),
        'config_type': optional_env('SOVITS_CONFIG_TYPE', 'so-vits-svc-4.0v1'),
        'dataset_raw_dir': optional_env('SOVITS_RAW_DATA_DIR', str(job_dir / 'workspace' / 'dataset_raw')),
        'processed_data_dir': optional_env('SOVITS_PROCESSED_DATA_DIR', str(job_dir / 'workspace' / 'dataset' / '44k')),
        'filelists_dir': optional_env('SOVITS_FILELISTS_DIR', str(job_dir / 'workspace' / 'filelists' / '44k')),
        'model_dir': optional_env('SOVITS_LOGS_DIR', str(job_dir / 'workspace' / 'logs' / '44k')),
        'config_output_path': optional_env('SOVITS_CONFIG_OUTPUT_PATH', str(job_dir / 'workspace' / 'configs' / '44k' / 'config.json')),
        'transpose': optional_env('SOVITS_INFER_TRANSPOSE', '0'),
    }

    return RunnerContext(
        job_type=mode,
        job_id=optional_env('VC_JOB_ID', 'smoke-job'),
        job_dir=job_dir,
        artifacts_dir=artifacts_dir,
        payload_path=payload_path,
        dataset_dir=dataset_dir if mode == 'training' else None,
        repo_dir=repo_dir,
        model_path=model_path if mode == 'conversion' else None,
        config_path=config_path if mode == 'conversion' else None,
        input_path=input_path if mode == 'conversion' else None,
        output_path=output_path if mode == 'conversion' else None,
        params=params,
    )


def _check_required_env(names: list[str]) -> list[str]:
    missing = []
    for name in names:
        try:
            require_env(name)
        except RuntimeError:
            missing.append(name)
    return missing


def _render_template(template: str, context: RunnerContext) -> str:
    return template.format(**build_template_vars(context))


def _validate_training(context: RunnerContext, check_paths: bool) -> list[str]:
    issues: list[str] = []
    required = [
        'VC_TRAIN_RUNNER_COMMAND',
        'SOVITS_REPO_DIR',
        'SOVITS_RESAMPLE_CMD_TEMPLATE',
        'SOVITS_CONFIG_CMD_TEMPLATE',
        'SOVITS_HUBERT_CMD_TEMPLATE',
        'SOVITS_TRAIN_CMD_TEMPLATE',
        'SOVITS_MODEL_SOURCE',
    ]
    missing = _check_required_env(required)
    if missing:
        issues.append('Missing training env vars: ' + ', '.join(missing))
        return issues

    templates = [
        'SOVITS_RESAMPLE_CMD_TEMPLATE',
        'SOVITS_CONFIG_CMD_TEMPLATE',
        'SOVITS_HUBERT_CMD_TEMPLATE',
        'SOVITS_TRAIN_CMD_TEMPLATE',
        'SOVITS_MODEL_SOURCE',
        'SOVITS_CONFIG_SOURCE',
        'SOVITS_METRICS_SOURCE',
    ]
    for name in templates:
        raw = optional_env(name)
        if not raw:
            continue
        try:
            rendered = _render_template(raw, context)
        except Exception as exc:
            issues.append(f'Failed to render {name}: {exc}')
            continue
        if not rendered.strip():
            issues.append(f'{name} rendered to an empty string')

    if check_paths:
        repo_dir = pathlib.Path(require_env('SOVITS_REPO_DIR'))
        if not repo_dir.exists():
            issues.append(f'SOVITS_REPO_DIR does not exist: {repo_dir}')
    return issues


def _validate_conversion(context: RunnerContext, check_paths: bool) -> list[str]:
    issues: list[str] = []
    required = [
        'VC_CONVERT_RUNNER_COMMAND',
        'SOVITS_REPO_DIR',
        'SOVITS_INFER_CMD_TEMPLATE',
    ]
    missing = _check_required_env(required)
    if missing:
        issues.append('Missing conversion env vars: ' + ', '.join(missing))
        return issues

    try:
        rendered = _render_template(require_env('SOVITS_INFER_CMD_TEMPLATE'), context)
        if not rendered.strip():
            issues.append('SOVITS_INFER_CMD_TEMPLATE rendered to an empty string')
    except Exception as exc:
        issues.append(f'Failed to render SOVITS_INFER_CMD_TEMPLATE: {exc}')

    if check_paths:
        repo_dir = pathlib.Path(require_env('SOVITS_REPO_DIR'))
        if not repo_dir.exists():
            issues.append(f'SOVITS_REPO_DIR does not exist: {repo_dir}')
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate VC/So-VITS runner environment and templates.')
    parser.add_argument('--mode', choices=['training', 'conversion', 'both'], default='both')
    parser.add_argument('--check-paths', action='store_true', help='Also check filesystem paths such as SOVITS_REPO_DIR.')
    args = parser.parse_args()

    failures: list[str] = []
    if args.mode in {'training', 'both'}:
        failures.extend(_validate_training(_dummy_context('training'), args.check_paths))
    if args.mode in {'conversion', 'both'}:
        failures.extend(_validate_conversion(_dummy_context('conversion'), args.check_paths))

    if failures:
        print('VC/So-VITS smoke test failed:')
        for failure in failures:
            print(f'- {failure}')
        return 1

    print('VC/So-VITS smoke test passed.')
    print(f'- mode: {args.mode}')
    print(f'- check_paths: {args.check_paths}')
    print(f'- repo: {optional_env("SOVITS_REPO_DIR", "/root/so-vits-svc")}')
    return 0


if __name__ == '__main__':
    sys.exit(main())