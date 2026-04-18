from __future__ import annotations

import glob
import json
import os
import pathlib
import shutil
import subprocess
from dataclasses import dataclass


def require_env(name: str) -> str:
    value = os.environ.get(name, '').strip()
    if not value:
        raise RuntimeError(f'{name} is required')
    return value


def optional_env(name: str, default: str = '') -> str:
    return os.environ.get(name, default).strip()


def ensure_dir(path: pathlib.Path) -> pathlib.Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_json_env(name: str, default: dict | None = None) -> dict:
    raw = os.environ.get(name, '').strip()
    if not raw:
        return default or {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f'{name} is not valid JSON: {exc}') from exc
    if not isinstance(value, dict):
        raise RuntimeError(f'{name} must decode to a JSON object')
    return value


@dataclass(frozen=True)
class RunnerContext:
    job_type: str
    job_id: str
    job_dir: pathlib.Path
    artifacts_dir: pathlib.Path
    payload_path: pathlib.Path
    dataset_dir: pathlib.Path | None = None
    model_path: pathlib.Path | None = None
    config_path: pathlib.Path | None = None
    input_path: pathlib.Path | None = None
    output_path: pathlib.Path | None = None
    repo_dir: pathlib.Path | None = None
    params: dict | None = None


def build_template_vars(context: RunnerContext) -> dict[str, str]:
    values = {
        'job_type': context.job_type,
        'job_id': context.job_id,
        'job_dir': str(context.job_dir),
        'artifacts_dir': str(context.artifacts_dir),
        'payload_path': str(context.payload_path),
        'repo_dir': str(context.repo_dir) if context.repo_dir else '',
        'dataset_dir': str(context.dataset_dir) if context.dataset_dir else '',
        'model_path': str(context.model_path) if context.model_path else '',
        'config_path': str(context.config_path) if context.config_path else '',
        'input_path': str(context.input_path) if context.input_path else '',
        'output_path': str(context.output_path) if context.output_path else '',
    }
    if context.params:
        for key, value in context.params.items():
            values[f'param_{key}'] = '' if value is None else str(value)
    return values


def run_command_template(template: str, context: RunnerContext, step_name: str, timeout_seconds: int) -> None:
    template = (template or '').strip()
    if not template:
        raise RuntimeError(f'Missing command template for {step_name}')
    command = template.format(**build_template_vars(context))
    result = subprocess.run(
        command,
        shell=True,
        cwd=str(context.repo_dir or context.job_dir),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f'{step_name} failed with exit code {result.returncode}. '
            f'stdout: {result.stdout.strip()} stderr: {result.stderr.strip()}'
        )


def resolve_source(pattern_or_path: str, context: RunnerContext, description: str) -> pathlib.Path:
    value = (pattern_or_path or '').strip()
    if not value:
        raise RuntimeError(f'{description} is not configured')
    resolved = value.format(**build_template_vars(context))
    matches = sorted(glob.glob(resolved))
    if not matches:
        raise RuntimeError(f'No file matched for {description}: {resolved}')
    return pathlib.Path(matches[-1])


def copy_artifact(source: pathlib.Path, destination: pathlib.Path) -> None:
    ensure_dir(destination.parent)
    shutil.copy2(source, destination)


def write_json(path: pathlib.Path, payload: dict) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')
