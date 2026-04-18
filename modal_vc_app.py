"""Modal.com GPU worker for Voice Clone training and conversion.

This module provides two web endpoints:
  - POST /train — trains a voice model from dataset files in R2
  - POST /convert — runs voice conversion inference

Usage:
    modal deploy modal_vc_app.py

The Modal dashboard will print the deployed URLs after successful deployment.
Copy those to your Flask `.env` as VC_MODAL_TRAINING_URL and VC_MODAL_CONVERSION_URL.

Env vars (set via Modal secret "audiocraft-vc-secrets"):
    R2_ENDPOINT_URL       - Cloudflare R2 S3-compatible endpoint.
    R2_ACCESS_KEY_ID     - R2 access key ID.
    R2_SECRET_ACCESS_KEY - R2 secret access key.
    R2_BUCKET_NAME     - R2 bucket name (e.g. audiocraft-vc).
    VC_WEBHOOK_SECRET  - HMAC secret shared with Flask (for callbacks).
    VC_MODAL_AUTH_TOKEN - Bearer token for endpoint auth (optional).
        VC_TRAIN_RUNNER_COMMAND - Shell command that performs training in the temp job dir.
        VC_CONVERT_RUNNER_COMMAND - Shell command that performs conversion in the temp job dir.

Runner contract:
        Training command must write:
            artifacts/model.pth
            artifacts/config.json
        Optional:
            artifacts/metrics.json

        Conversion command must write:
            artifacts/output.wav

The worker exposes inputs to the runner via environment variables such as:
        VC_JOB_DIR, VC_JOB_PAYLOAD_PATH, VC_DATASET_DIR, VC_ARTIFACTS_DIR,
        VC_MODEL_PATH, VC_CONFIG_PATH, VC_INPUT_PATH, VC_OUTPUT_PATH, VC_PARAMS_JSON.

The repository includes a concrete So-VITS-SVC-oriented runner layer under
``scripts/vc`` that can be used as the default command target.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import pathlib
import subprocess
import time
import urllib.request
import uuid

import modal
from fastapi import Request, HTTPException

# ── Image: pin your ML stack here ─────────────────────────────────────────────
SOVITS_GIT_URL = "https://github.com/voicepaw/so-vits-svc-fork.git"
SOVITS_GIT_REF = "v4.2.30"

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "git",
        "ffmpeg",
        "libsndfile1",
        "libgl1",
    )
    .pip_install(
        "boto3>=1.34.0",
        "fastapi>=0.110.0",
        "torch==2.1.0",
        "torchaudio==2.1.0",
    )
    .run_commands(
        f"git clone {SOVITS_GIT_URL} /root/so-vits-svc",
        f"cd /root/so-vits-svc && git checkout {SOVITS_GIT_REF}",
        "cd /root/so-vits-svc && pip install .",
    )
    .env({"PYTHONPATH": "/root/app"})
    .add_local_dir("scripts", remote_path="/root/app/scripts")
)

app = modal.App("audiocraft-vc", image=image)

# ── Shared R2 helpers ───────────────────────────────────────────────────
def _r2_client():
    import boto3
    from botocore.config import Config
    return boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT_URL"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def _r2_download(key: str) -> bytes:
    resp = _r2_client().get_object(
        Bucket=os.environ["R2_BUCKET_NAME"],
        Key=key,
    )
    return resp["Body"].read()


def _r2_upload(key: str, data: bytes, content_type: str = "application/octet-stream"):
    _r2_client().put_object(
        Bucket=os.environ["R2_BUCKET_NAME"],
        Key=key,
        Body=data,
        ContentType=content_type,
    )


def _runner_command(env_name: str) -> str:
    value = os.environ.get(env_name, "").strip()
    if not value:
        raise RuntimeError(f"{env_name} is not configured")
    return value


def _runner_timeout(env_name: str, default_seconds: int) -> int:
    try:
        return int(os.environ.get(env_name, str(default_seconds)))
    except Exception:
        return default_seconds


def _run_runner(command: str, cwd: pathlib.Path, env_updates: dict[str, str], timeout_seconds: int) -> None:
    env = os.environ.copy()
    env.update({key: str(value) for key, value in env_updates.items() if value is not None})
    result = subprocess.run(
        command,
        shell=True,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Runner failed with exit code {result.returncode}. "
            f"stdout: {result.stdout.strip()} stderr: {result.stderr.strip()}"
        )


def _read_json_file(path: pathlib.Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Failed to parse JSON file {path.name}: {exc}") from exc


# ── Webhook helper ─────────────────────────────────────────────────
def _send_callback(callback_url: str, payload: dict):
    """Send a webhook POST to the Flask app with HMAC signature."""
    secret = os.environ.get("VC_WEBHOOK_SECRET", "")
    body = json.dumps(payload).encode()
    ts = str(int(time.time()))
    sig = hmac.new(secret.encode(), f"{ts}.{body.decode()}".encode(), hashlib.sha256).hexdigest()

    req = urllib.request.Request(
        callback_url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-VC-Timestamp": ts,
            "X-VC-Signature": sig,
        },
    )
    try:
        urllib.request.urlopen(req, timeout=30)
    except Exception as e:
        print(f"Webhook callback failed: {e}")


# ── Auth decorator (optional) ───────────────────────────────────────────
def _check_auth(request: Request):
    """Check Bearer token if VC_MODAL_AUTH_TOKEN is set."""
    token = os.environ.get("VC_MODAL_AUTH_TOKEN", "")
    if not token:
        return
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="Unauthorized")


# ── Secrets ──────────────────────────────────────────────────────
vc_secrets = modal.Secret.from_name("audiocraft-vc-secrets")


# ── Training endpoint ────────────────────────────────────────────────
@app.function(
    gpu="A10G",
    timeout=3600,
    secrets=[vc_secrets],
)
@modal.fastapi_endpoint(method="POST")
async def train(request: Request):
    """Run voice model training.

    Expected payload:
    {
        "training_job_id": "uuid",
        "dataset_r2_keys": ["vc/users/.../dataset/.../file.wav", ...],
        "output_prefix": "vc/users/.../models/",
        "callback_url": "https://.../api/vc/webhooks/modal",
        "params": {"epochs": 100, ...}  # optional
    }
    """
    import tempfile

    _check_auth(request)
    payload = await request.json()

    job_id = payload["training_job_id"]
    dataset_keys = payload["dataset_r2_keys"]
    output_prefix = payload["output_prefix"]
    callback_url = payload["callback_url"]
    params = payload.get("params", {})
    call_id = str(uuid.uuid4())

    # Signal running
    _send_callback(callback_url, {
        "event_id": f"{job_id}-running",
        "job_type": "training",
        "job_id": job_id,
        "status": "running",
    })

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)
            dataset_dir = tmp / "dataset"
            artifacts_dir = tmp / "artifacts"
            dataset_dir.mkdir()
            artifacts_dir.mkdir()
            job_payload_path = tmp / "job_payload.json"
            job_payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            # 1. Download dataset files from R2
            for key in dataset_keys:
                fname = key.split("/")[-1]
                data = _r2_download(key)
                (dataset_dir / fname).write_bytes(data)

            # 2. Execute the configured training runner.
            _run_runner(
                _runner_command("VC_TRAIN_RUNNER_COMMAND"),
                cwd=tmp,
                env_updates={
                    "VC_JOB_TYPE": "training",
                    "VC_JOB_ID": job_id,
                    "VC_JOB_DIR": str(tmp),
                    "VC_JOB_PAYLOAD_PATH": str(job_payload_path),
                    "VC_DATASET_DIR": str(dataset_dir),
                    "VC_ARTIFACTS_DIR": str(artifacts_dir),
                    "VC_OUTPUT_PREFIX": output_prefix,
                    "VC_PARAMS_JSON": json.dumps(params),
                },
                timeout_seconds=_runner_timeout("VC_TRAIN_RUNNER_TIMEOUT_SEC", 3300),
            )

            model_path = artifacts_dir / "model.pth"
            config_path = artifacts_dir / "config.json"
            metrics_path = artifacts_dir / "metrics.json"

            if not model_path.exists():
                raise RuntimeError("Training runner did not produce artifacts/model.pth")
            if not config_path.exists():
                raise RuntimeError("Training runner did not produce artifacts/config.json")

            model_data = model_path.read_bytes()
            config_data = config_path.read_bytes()
            metrics = _read_json_file(metrics_path, default={})

            # 3. Upload artifacts to R2
            model_version_id = str(uuid.uuid4())
            model_key = f"{output_prefix}{model_version_id}/model.pth"
            config_key = f"{output_prefix}{model_version_id}/config.json"
            _r2_upload(model_key, model_data, "application/octet-stream")
            _r2_upload(config_key, config_data, "application/json")

        # 4. Callback — succeeded
        _send_callback(callback_url, {
            "event_id": f"{job_id}-done",
            "job_type": "training",
            "job_id": job_id,
            "status": "succeeded",
            "artifact_keys": {
                "r2_model_key": model_key,
                "r2_config_key": config_key,
            },
            "metrics": metrics,
        })

    except Exception as exc:
        _send_callback(callback_url, {
            "event_id": f"{job_id}-failed",
            "job_type": "training",
            "job_id": job_id,
            "status": "failed",
            "error": str(exc),
        })
        raise

    return {"call_id": call_id, "status": "queued"}


# ── Conversion endpoint ──────────────────────────────────────────
@app.function(
    gpu="A10G",
    timeout=600,
    secrets=[vc_secrets],
)
@modal.fastapi_endpoint(method="POST")
async def convert(request: Request):
    """Run voice conversion inference.

    Expected payload:
    {
        "conversion_job_id": "uuid",
        "model_artifact_keys": {
            "r2_model_key": "vc/users/.../models/.../model.pth",
            "r2_config_key": "vc/users/.../models/.../config.json",
        },
        "input_r2_key": "vc/users/.../conversions/.../input.wav",
        "output_r2_key": "vc/users/.../conversions/.../output.wav",
        "callback_url": "https://.../api/vc/webhooks/modal",
    }
    """
    import tempfile

    _check_auth(request)
    payload = await request.json()

    job_id = payload["conversion_job_id"]
    model_keys = payload["model_artifact_keys"]
    input_key = payload["input_r2_key"]
    output_key = payload["output_r2_key"]
    callback_url = payload["callback_url"]
    call_id = str(uuid.uuid4())

    _send_callback(callback_url, {
        "event_id": f"{job_id}-running",
        "job_type": "conversion",
        "job_id": job_id,
        "status": "running",
    })

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)
            artifacts_dir = tmp / "artifacts"
            artifacts_dir.mkdir()
            job_payload_path = tmp / "job_payload.json"
            job_payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            # 1. Download model + input from R2
            model_data = _r2_download(model_keys["r2_model_key"])
            config_data = _r2_download(model_keys["r2_config_key"])
            input_data = _r2_download(input_key)

            model_path = tmp / "model.pth"
            config_path = tmp / "config.json"
            input_path = tmp / "input.wav"
            output_path = artifacts_dir / "output.wav"

            model_path.write_bytes(model_data)
            config_path.write_bytes(config_data)
            input_path.write_bytes(input_data)

            # 2. Execute the configured conversion runner.
            _run_runner(
                _runner_command("VC_CONVERT_RUNNER_COMMAND"),
                cwd=tmp,
                env_updates={
                    "VC_JOB_TYPE": "conversion",
                    "VC_JOB_ID": job_id,
                    "VC_JOB_DIR": str(tmp),
                    "VC_JOB_PAYLOAD_PATH": str(job_payload_path),
                    "VC_ARTIFACTS_DIR": str(artifacts_dir),
                    "VC_MODEL_PATH": str(model_path),
                    "VC_CONFIG_PATH": str(config_path),
                    "VC_INPUT_PATH": str(input_path),
                    "VC_OUTPUT_PATH": str(output_path),
                },
                timeout_seconds=_runner_timeout("VC_CONVERT_RUNNER_TIMEOUT_SEC", 540),
            )

            if not output_path.exists():
                raise RuntimeError("Conversion runner did not produce artifacts/output.wav")
            output_data = output_path.read_bytes()

            # 3. Upload result to R2
            _r2_upload(output_key, output_data, "audio/wav")

        _send_callback(callback_url, {
            "event_id": f"{job_id}-done",
            "job_type": "conversion",
            "job_id": job_id,
            "status": "succeeded",
            "output_r2_key": output_key,
        })

    except Exception as exc:
        _send_callback(callback_url, {
            "event_id": f"{job_id}-failed",
            "job_type": "conversion",
            "job_id": job_id,
            "status": "failed",
            "error": str(exc),
        })
        raise

    return {"call_id": call_id, "status": "queued"}