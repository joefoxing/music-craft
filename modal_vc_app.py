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
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import urllib.request
import uuid

import modal
from fastapi import Request, HTTPException

# ── Image: pin your ML stack here ─────────────────────────────────────────────
# TODO: Add your actual voice cloning dependencies (so-vits-svc, rvc, etc.)
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "boto3>=1.34.0",
        "torch==2.1.0",
        "torchaudio==2.1.0",
        # Add additional dependencies here, e.g.:
        # "so-vits-svc-fork",
        # "rivc",
    )
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
@modal.web_endpoint(method="POST")
def train(request: Request):
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
    import urllib.request
    import tempfile
    import pathlib

    _check_auth(request)
    payload = request.json()

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
            dataset_dir.mkdir()

            # 1. Download dataset files from R2
            for key in dataset_keys:
                fname = key.split("/")[-1]
                data = _r2_download(key)
                (dataset_dir / fname).write_bytes(data)

            # 2. TODO: Run your actual training here
            #    Example placeholder:
            #    from your_train_module import train_voice_model
            #    model_path = train_voice_model(dataset_dir, params)
            #
            #    # For now, just echo back a placeholder
            model_data = b"PLACEHOLDER_MODEL_DATA"
            config_data = json.dumps({
                "epochs": params.get("epochs", 100),
                "training_job_id": job_id,
            }).encode()

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
            "metrics": {},
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
@modal.web_endpoint(method="POST")
def convert(request: Request):
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
    import urllib.request
    import tempfile
    import pathlib

    _check_auth(request)
    payload = request.json()

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

            # 1. Download model + input from R2
            model_data = _r2_download(model_keys["r2_model_key"])
            config_data = _r2_download(model_keys["r2_config_key"])
            input_data = _r2_download(input_key)

            (tmp / "model.pth").write_bytes(model_data)
            (tmp / "config.json").write_bytes(config_data)
            (tmp / "input.wav").write_bytes(input_data)

            # 2. TODO: Run your actual inference here
            #    Example placeholder:
            #    from your_inference_module import convert_voice
            #    output_data = convert_voice(tmp / "model.pth", tmp / "input.wav")
            #
            #    For now, just copy input to output as placeholder
            output_data = input_data

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