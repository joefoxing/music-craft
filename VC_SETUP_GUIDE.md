# Voice Clone — Cloudflare R2 + Modal Setup Guide

This guide walks you through wiring up Cloudflare R2 (file storage) and Modal.com (GPU training/conversion) so the Voice Clone feature in this app works end-to-end.

For a concrete So-VITS-SVC runner integration, see `VC_SOVITS_RUNNER_GUIDE.md`.
For a ready-to-paste Modal secret template, see `VC_SOVITS_4X_MODAL_SECRET.example`.
For a worker-image example that clones and installs So-VITS, see `VC_MODAL_IMAGE_RECIPE.md`.
For a single end-to-end execution order for this repo, see `VC_DEPLOYMENT_CHECKLIST.md`.

---

## Overview

```
Browser → Flask API → Cloudflare R2 (stores audio files & model artifacts)
                    → Modal.com (GPU training / inference)
                    ← Modal webhook → Flask (job status update)
```

1. User uploads dataset audio → stored in R2
2. Flask dispatches training job → Modal downloads from R2, trains, uploads model back to R2, pings Flask webhook
3. User uploads conversion input → stored in R2
4. Flask dispatches conversion job → Modal downloads model + input from R2, runs inference, uploads output to R2, pings webhook
5. User downloads output via Flask (which streams it from R2)

---

## Part 1 — Cloudflare R2

### 1.1 Create a bucket

1. Log into [dash.cloudflare.com](https://dash.cloudflare.com) → **R2 Object Storage** → **Create bucket**
2. Name: `audiocraft-vc` (or anything you like — it goes in `R2_BUCKET_NAME`)
3. Location: choose the region closest to your Modal GPU region (e.g. `WEUR` for EU, `ENAM` for US East)

### 1.2 Create an API token

1. In R2 → **Manage R2 API Tokens** → **Create API Token**
2. Permissions: **Object Read & Write** on the bucket you just created
3. Copy **Access Key ID** and **Secret Access Key** — you will not see these again

### 1.3 Find your account endpoint

Your R2 S3-compatible endpoint is:
```
https://<ACCOUNT_ID>.r2.cloudflarestorage.com
```
Find `ACCOUNT_ID` in the Cloudflare dashboard URL or on the R2 overview page.

### 1.4 Add env vars to `.env`

```dotenv
R2_ACCOUNT_ID=your-cloudflare-account-id
R2_ACCESS_KEY_ID=your-r2-access-key-id
R2_SECRET_ACCESS_KEY=your-r2-secret-access-key
R2_BUCKET_NAME=audiocraft-vc
R2_ENDPOINT_URL=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
# Optional: public URL if you enable public access on the bucket
R2_PUBLIC_BASE_URL=https://pub-xxxx.r2.dev
```

### 1.5 Install boto3 in the app

Add to `requirements.txt`:
```
boto3>=1.34
```

Then rebuild the Docker image:
```powershell
docker compose up --build -d app
```

### 1.6 Upload behavior in the current code

The current code already supports R2-backed VC storage.

- Dataset uploads return a presigned R2 `PUT` URL when R2 is configured.
- Conversion uploads also return a presigned R2 `PUT` URL and create a staged conversion job up front.
- Without R2, both paths fall back to the Flask upload endpoints.

You do not need to rewrite the upload routes first unless you want a different storage contract.

**Upload helper (add to `vc_api.py` or a new `r2.py` service):**

```python
import boto3
from botocore.config import Config

def _r2_client():
    return boto3.client(
        's3',
        endpoint_url=os.environ['R2_ENDPOINT_URL'],
        aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
        config=Config(signature_version='s3v4'),
        region_name='auto',
    )

def upload_to_r2(r2_key: str, data: bytes, content_type: str = 'audio/wav'):
    _r2_client().put_object(
        Bucket=os.environ['R2_BUCKET_NAME'],
        Key=r2_key,
        Body=data,
        ContentType=content_type,
    )

def download_from_r2(r2_key: str) -> bytes:
    resp = _r2_client().get_object(
        Bucket=os.environ['R2_BUCKET_NAME'],
        Key=r2_key,
    )
    return resp['Body'].read()

def presigned_get_url(r2_key: str, expires_in: int = 3600) -> str:
    return _r2_client().generate_presigned_url(
        'get_object',
        Params={'Bucket': os.environ['R2_BUCKET_NAME'], 'Key': r2_key},
        ExpiresIn=expires_in,
    )
```

**Key layout** already defined in the codebase:
| File type | R2 key pattern |
|---|---|
| Dataset file | `vc/users/{user_id}/profiles/{profile_id}/dataset/{file_id}/{filename}` |
| Trained model | `vc/users/{user_id}/profiles/{profile_id}/models/{model_version_id}/model.pth` |
| Model config | `vc/users/{user_id}/profiles/{profile_id}/models/{model_version_id}/config.json` |
| Conversion input | `vc/users/{user_id}/profiles/{profile_id}/conversions/{job_id}/input.wav` |
| Conversion output | `vc/users/{user_id}/profiles/{profile_id}/conversions/{job_id}/output.wav` |

---

## Part 2 — Modal.com

### 2.1 Create a Modal account and install the CLI

```bash
pip install modal
modal setup          # opens browser for authentication
modal token new      # creates ~/.modal.toml with your token
```

### 2.2 Create and configure `modal_vc_app.py`

The worker in this repo is now designed around operator-provided runner commands rather than fake placeholder success.

The important contract is:

- `VC_TRAIN_RUNNER_COMMAND` must write `artifacts/model.pth` and `artifacts/config.json`
- `VC_CONVERT_RUNNER_COMMAND` must write `artifacts/output.wav`
- optional `artifacts/metrics.json` can be produced by training

The worker passes the job context to your engine through environment variables such as:

- `VC_JOB_DIR`
- `VC_JOB_PAYLOAD_PATH`
- `VC_DATASET_DIR`
- `VC_ARTIFACTS_DIR`
- `VC_MODEL_PATH`
- `VC_CONFIG_PATH`
- `VC_INPUT_PATH`
- `VC_OUTPUT_PATH`
- `VC_PARAMS_JSON`

This lets you wire So-VITS-SVC, RVC, or another internal training/conversion wrapper without changing Flask-side orchestration.

```python
import hashlib
import hmac
import json
import os
import time
import urllib.request

import modal

# ── Image: pin your ML stack here ─────────────────────────────────────────────
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "boto3",
        "torch==2.1.0",
        "torchaudio==2.1.0",
        # add so-vits-svc or rvc dependencies here
    )
)

app = modal.App("audiocraft-vc", image=image)

# ── Shared R2 helpers (same as Flask side) ─────────────────────────────────────
def _r2_download(key: str) -> bytes:
    import boto3
    from botocore.config import Config
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT_URL"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )
    return s3.get_object(Bucket=os.environ["R2_BUCKET_NAME"], Key=key)["Body"].read()

def _r2_upload(key: str, data: bytes, content_type="application/octet-stream"):
    import boto3
    from botocore.config import Config
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT_URL"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )
    s3.put_object(Bucket=os.environ["R2_BUCKET_NAME"], Key=key, Body=data, ContentType=content_type)

# ── Webhook helper ─────────────────────────────────────────────────────────────
def _send_callback(callback_url: str, payload: dict):
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
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Webhook callback failed: {e}")

# ── Secrets (set these in Modal dashboard) ─────────────────────────────────────
vc_secrets = modal.Secret.from_name("audiocraft-vc-secrets")

# ── Training endpoint ──────────────────────────────────────────────────────────
@app.function(
    gpu="A10G",
    timeout=3600,
    secrets=[vc_secrets],
)
@modal.web_endpoint(method="POST")
def train(payload: dict):
    import uuid

    job_id = payload["training_job_id"]
    dataset_keys = payload["dataset_r2_keys"]
    output_prefix = payload["output_prefix"]
    callback_url = payload["callback_url"]
    params = payload.get("params") or {}
    call_id = str(uuid.uuid4())

    # Signal running
    _send_callback(callback_url, {
        "event_id": f"{job_id}-running",
        "job_type": "training",
        "job_id": job_id,
        "status": "running",
    })

    try:
        import tempfile, pathlib

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)

            # 1. Download dataset files from R2
            dataset_dir = tmp / "dataset"
            dataset_dir.mkdir()
            for key in dataset_keys:
                fname = key.split("/")[-1]
                data = _r2_download(key)
                (dataset_dir / fname).write_bytes(data)

            # 2. TODO: run your training here
            #    e.g. preprocess audio, extract features, train So-VITS-SVC / RVC
            model_data = b""    # replace with actual trained model bytes
            config_data = b"{}" # replace with actual config bytes

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

# ── Conversion endpoint ────────────────────────────────────────────────────────
@app.function(
    gpu="A10G",
    timeout=600,
    secrets=[vc_secrets],
)
@modal.web_endpoint(method="POST")
def convert(payload: dict):
    import uuid

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
        import tempfile, pathlib

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)

            # 1. Download model + input from R2
            model_data  = _r2_download(model_keys["r2_model_key"])
            config_data = _r2_download(model_keys["r2_config_key"])
            input_data  = _r2_download(input_key)

            (tmp / "model.pth").write_bytes(model_data)
            (tmp / "config.json").write_bytes(config_data)
            (tmp / "input.wav").write_bytes(input_data)

            # 2. TODO: run inference here
            #    e.g. so-vits-svc or RVC inference
            output_data = input_data  # replace with real output

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
```

### 2.3 Create the Modal secret

In the [Modal dashboard](https://modal.com/secrets) → **New Secret** → name it `audiocraft-vc-secrets`.

For this repo, start from `VC_SOVITS_4X_MODAL_SECRET.example` and paste the values into the secret.

Use these values exactly unless you intentionally changed the worker image or runner contract:

| Key | Value |
|---|---|
| `R2_ENDPOINT_URL` | `https://<ACCOUNT_ID>.r2.cloudflarestorage.com` |
| `R2_ACCESS_KEY_ID` | your R2 access key |
| `R2_SECRET_ACCESS_KEY` | your R2 secret key |
| `R2_BUCKET_NAME` | `audiocraft-vc` |
| `VC_WEBHOOK_SECRET` | generate with `python -c "import secrets; print(secrets.token_hex(32))"` — **must match** `VC_WEBHOOK_SECRET` in your `.env` |
| `VC_MODAL_AUTH_TOKEN` | generate a random token and use the same value in Modal and your Flask `.env` |
| `VC_TRAIN_RUNNER_COMMAND` | `python -m scripts.vc.run_training` |
| `VC_CONVERT_RUNNER_COMMAND` | `python -m scripts.vc.run_inference` |
| `VC_TRAIN_RUNNER_TIMEOUT_SEC` | `3300` |
| `VC_CONVERT_RUNNER_TIMEOUT_SEC` | `540` |
| `SOVITS_REPO_DIR` | `/root/so-vits-svc` if your Modal image clones So-VITS there |
| `SOVITS_WORKSPACE_DIR` | leave blank unless you want to override the default working directory |
| `SOVITS_LOGS_DIR` | leave blank unless your fork writes logs elsewhere |
| `SOVITS_FILELISTS_DIR` | leave blank unless your fork requires a fixed path |
| `SOVITS_RAW_DATA_DIR` | leave blank unless your fork requires a fixed path |
| `SOVITS_PROCESSED_DATA_DIR` | leave blank unless you want to override the default `dataset/44k` path |
| `SOVITS_CONFIG_OUTPUT_PATH` | leave blank unless your fork requires a fixed config path |
| `SOVITS_CONFIG_TYPE` | `so-vits-svc-4.0v1` |
| `SOVITS_SPEAKER_NAME` | `target` |
| `SOVITS_SAMPLE_RATE` | `44100` |
| `SOVITS_RESAMPLE_CMD_TEMPLATE` | `python -m so_vits_svc_fork pre-resample -i "{param_dataset_raw_dir}" -o "{param_processed_data_dir}" -s {param_sample_rate}` |
| `SOVITS_CONFIG_CMD_TEMPLATE` | `python -m so_vits_svc_fork pre-config -i "{param_processed_data_dir}" -f "{param_filelists_dir}" -c "{param_config_output_path}" -t "{param_config_type}"` |
| `SOVITS_HUBERT_CMD_TEMPLATE` | `python -m so_vits_svc_fork pre-hubert -i "{param_processed_data_dir}" -c "{param_config_output_path}" -fm "{param_f0_method}"` |
| `SOVITS_TRAIN_CMD_TEMPLATE` | `python -m so_vits_svc_fork train -c "{param_config_output_path}" -m "{param_model_dir}" -nt` |
| `SOVITS_MODEL_SOURCE` | `{param_model_dir}/G_*.pth` |
| `SOVITS_CONFIG_SOURCE` | `{param_config_output_path}` |
| `SOVITS_METRICS_SOURCE` | leave blank unless you want to collect extra metrics artifacts |
| `SOVITS_INFER_SPEAKER` | leave blank to auto-select the first speaker from `config.json` |
| `SOVITS_INFER_TRANSPOSE` | `0` |
| `SOVITS_INFER_F0_METHOD` | `dio` |
| `SOVITS_INFER_CMD_TEMPLATE` | `python -m so_vits_svc_fork infer "{input_path}" -o "{output_path}" -s "{param_speaker_name}" -m "{model_path}" -c "{config_path}" -t {param_transpose} -fm "{param_f0_method}" -na` |
| `SOVITS_RESAMPLE_TIMEOUT_SEC` | `1800` |
| `SOVITS_CONFIG_TIMEOUT_SEC` | `1800` |
| `SOVITS_HUBERT_TIMEOUT_SEC` | `3600` |
| `SOVITS_TRAIN_TIMEOUT_SEC` | `10800` |
| `SOVITS_INFER_TIMEOUT_SEC` | `1800` |

These defaults target `voicepaw/so-vits-svc-fork` and its package-based `python -m so_vits_svc_fork ...` CLI.

### 2.4 Deploy

```bash
cd y:\lyric_cover_staging\music-craft
modal deploy modal_vc_app.py
```

After deployment Modal prints the web endpoint URLs:
```
✓ Created web endpoint train => https://your-workspace--audiocraft-vc-train.modal.run
✓ Created web endpoint convert => https://your-workspace--audiocraft-vc-convert.modal.run
```

Copy those URLs.

### 2.5 Set an auth token (recommended)

In `modal_vc_app.py`, add a bearer token check at the top of both `train` and `convert`:

```python
from fastapi import Request, HTTPException

@app.function(gpu="A10G", secrets=[vc_secrets])
@modal.web_endpoint(method="POST")
async def train(request: Request):
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {os.environ['VC_MODAL_AUTH_TOKEN']}":
        raise HTTPException(status_code=401)
    payload = await request.json()
    ...
```

Add `VC_MODAL_AUTH_TOKEN` to the Modal secret and to your `.env`.

### 2.6 Runner example

Example only:

```dotenv
VC_TRAIN_RUNNER_COMMAND=python -m scripts.vc.run_training
VC_CONVERT_RUNNER_COMMAND=python -m scripts.vc.run_inference
```

Your training script should read from `VC_DATASET_DIR` and write artifacts into `VC_ARTIFACTS_DIR`.

Your inference script should read from `VC_MODEL_PATH`, `VC_CONFIG_PATH`, and `VC_INPUT_PATH`, then write `VC_OUTPUT_PATH`.

---

## Part 3 — Wire it all together in `.env`

Add these to your `.env` (copy from `.env.example` as a template):

```dotenv
# Cloudflare R2
R2_ACCOUNT_ID=abc123
R2_ACCESS_KEY_ID=your-access-key-id
R2_SECRET_ACCESS_KEY=your-secret-access-key
R2_BUCKET_NAME=audiocraft-vc
R2_ENDPOINT_URL=https://abc123.r2.cloudflarestorage.com

# Voice Clone — Modal endpoints
VC_MODAL_TRAINING_URL=https://your-workspace--audiocraft-vc-train.modal.run
VC_MODAL_CONVERSION_URL=https://your-workspace--audiocraft-vc-convert.modal.run
VC_TRAIN_RUNNER_COMMAND=python -m scripts.vc.run_training
VC_CONVERT_RUNNER_COMMAND=python -m scripts.vc.run_inference
VC_MODAL_AUTH_TOKEN=your-chosen-token
VC_WEBHOOK_SECRET=same-secret-as-in-modal-dashboard

# Public base URL (Modal needs to call back to this)
BASE_URL=https://yourdomain.com
```

> **Local dev note:** Modal can't reach `localhost`. Use [ngrok](https://ngrok.com) or [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) to expose your local Flask app, then set `BASE_URL` to the tunnel URL.

---

## Part 4 — Rebuild and verify

```powershell
# Rebuild the app image with boto3
docker compose up --build -d app

# Check logs
docker compose logs -f app
```

Test the flow end-to-end:
1. Open http://localhost:3001/voice
2. Create a voice profile
3. Upload a `.wav` dataset file
4. Click Train — the job should move to `queued`, then `running`, then `succeeded` once Modal calls the webhook
5. Upload a conversion input and click Convert
6. Confirm your runner produced a real output file, not a pass-through artifact

---

## Webhook Security Summary

The webhook handler at `POST /api/vc/webhooks/modal` expects:

| Header | Value |
|---|---|
| `X-VC-Timestamp` | Unix timestamp (seconds) |
| `X-VC-Signature` | `HMAC-SHA256(secret, "{timestamp}.{body}")` hex digest |

Requests older than **5 minutes** are rejected. The `event_id` in the payload ensures idempotency — duplicate deliveries are safe.
