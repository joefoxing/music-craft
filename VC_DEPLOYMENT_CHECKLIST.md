# VC Deployment Checklist

This checklist is the shortest path to getting the Voice Conversion module running for this exact repository.

It assumes:

- the Flask app lives in this repo
- Modal runs the GPU worker from `modal_vc_app.py`
- Cloudflare R2 stores datasets, model artifacts, and outputs
- So-VITS-SVC is provided as an external checkout inside the Modal image

Use this together with:

- `VC_SETUP_GUIDE.md`
- `VC_MODAL_IMAGE_RECIPE.md`
- `VC_SOVITS_4X_MODAL_SECRET.example`
- `VC_SOVITS_RUNNER_GUIDE.md`

## Phase 1 — Local Repo Prep

### 1. Confirm the app starts locally

From the repo root:

```powershell
Set-Location "y:\lyric_cover_staging\music-craft"
docker compose up --build -d
```

Check:

- `http://localhost:3001/health` returns `200`
- `/voice` redirects to login when not authenticated

### 2. Confirm your local VC code is present

These files should exist:

- `app/routes/vc_api.py`
- `modal_vc_app.py`
- `scripts/vc/run_training.py`
- `scripts/vc/run_inference.py`
- `scripts/vc/validate_sovits_setup.py`

### 3. Prepare your local `.env`

Start from `.env.example` and make sure these groups are present:

- VC Modal endpoint vars
- R2 vars
- So-VITS vars

Local Flask-side minimum:

```dotenv
BASE_URL=https://your-public-flask-url
VC_MODAL_TRAINING_URL=https://your-modal-train-endpoint
VC_MODAL_CONVERSION_URL=https://your-modal-convert-endpoint
VC_MODAL_AUTH_TOKEN=your-modal-auth-token
VC_WEBHOOK_SECRET=your-shared-webhook-secret

R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=audiocraft-vc
R2_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
```

If you are testing from your local machine, `BASE_URL` must be publicly reachable by Modal. `localhost` will not work.

## Phase 2 — Cloudflare R2

### 4. Create the R2 bucket

Create one bucket for VC artifacts, for example:

- `audiocraft-vc`

### 5. Create an R2 API token

Grant object read/write access to that bucket and record:

- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`

### 6. Record the R2 endpoint

You need:

```text
https://<ACCOUNT_ID>.r2.cloudflarestorage.com
```

## Phase 3 — Choose and Pin Your So-VITS Fork

### 7. Choose the exact So-VITS-SVC repository

For the long-term base used by this repo, use these values unless you intentionally choose another fork:

- `SOVITS_GIT_URL=https://github.com/voicepaw/so-vits-svc-fork.git`
- `SOVITS_GIT_REF=v4.2.30`

Do not deploy against an unpinned branch if you want predictable training and inference behavior.

### 8. Check that your chosen fork matches the default CLI assumptions

This repo’s current long-term integration assumes the package-based `voicepaw/so-vits-svc-fork` CLI with stages:

- `python -m so_vits_svc_fork pre-resample`
- `python -m so_vits_svc_fork pre-config`
- `python -m so_vits_svc_fork pre-hubert`
- `python -m so_vits_svc_fork train`
- `python -m so_vits_svc_fork infer`

If you choose another fork, update the `SOVITS_*` templates in your Modal secret before deploying.

## Phase 4 — Build the Modal Worker Image

### 9. Update `modal_vc_app.py` image build section

Use the pattern in `VC_MODAL_IMAGE_RECIPE.md`.

At minimum, the image should:

- install `git`
- install `ffmpeg`
- install `libsndfile1`
- install Python dependencies needed by the worker
- clone your So-VITS repo into `/root/so-vits-svc`
- copy this repo’s `scripts` directory into the image
- set `PYTHONPATH=/root/app`

### 10. Keep the repo path aligned

If the image clones So-VITS into `/root/so-vits-svc`, then your Modal secret must also set:

```dotenv
SOVITS_REPO_DIR=/root/so-vits-svc
```

## Phase 5 — Create the Modal Secret

### 11. Start from the example secret file

Use:

- `VC_SOVITS_4X_MODAL_SECRET.example`

as your base.

### 12. Fill in required secret values

You must replace placeholders for:

- `R2_ENDPOINT_URL`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `VC_WEBHOOK_SECRET`
- `VC_MODAL_AUTH_TOKEN`

### 13. Keep the default runner entrypoints unless you intentionally changed them

```dotenv
VC_TRAIN_RUNNER_COMMAND=python -m scripts.vc.run_training
VC_CONVERT_RUNNER_COMMAND=python -m scripts.vc.run_inference
```

### 14. Verify So-VITS command templates

Default templates expected by this repo:

```dotenv
SOVITS_CONFIG_TYPE=so-vits-svc-4.0v1
SOVITS_SPEAKER_NAME=target
SOVITS_SAMPLE_RATE=44100
SOVITS_RESAMPLE_CMD_TEMPLATE=python -m so_vits_svc_fork pre-resample -i "{param_dataset_raw_dir}" -o "{param_processed_data_dir}" -s {param_sample_rate}
SOVITS_CONFIG_CMD_TEMPLATE=python -m so_vits_svc_fork pre-config -i "{param_processed_data_dir}" -f "{param_filelists_dir}" -c "{param_config_output_path}" -t "{param_config_type}"
SOVITS_HUBERT_CMD_TEMPLATE=python -m so_vits_svc_fork pre-hubert -i "{param_processed_data_dir}" -c "{param_config_output_path}" -fm "{param_f0_method}"
SOVITS_TRAIN_CMD_TEMPLATE=python -m so_vits_svc_fork train -c "{param_config_output_path}" -m "{param_model_dir}" -nt
SOVITS_MODEL_SOURCE={param_model_dir}/G_*.pth
SOVITS_CONFIG_SOURCE={param_config_output_path}
SOVITS_METRICS_SOURCE=
SOVITS_INFER_SPEAKER=
SOVITS_INFER_TRANSPOSE=0
SOVITS_INFER_F0_METHOD=dio
SOVITS_INFER_CMD_TEMPLATE=python -m so_vits_svc_fork infer "{input_path}" -o "{output_path}" -s "{param_speaker_name}" -m "{model_path}" -c "{config_path}" -t {param_transpose} -fm "{param_f0_method}" -na
```

If your fork does not use these names, update the secret now.

## Phase 6 — Smoke Test the Worker Contract

### 15. Run the smoke test inside the built Modal image

Command:

```bash
python -m scripts.vc.validate_sovits_setup --mode both --check-paths
```

This checks:

- required runner env vars exist
- required So-VITS template env vars exist
- template rendering works
- `SOVITS_REPO_DIR` exists

Do not skip this. It is the fastest way to catch path and template mistakes before burning GPU time.

## Phase 7 — Deploy Modal

### 16. Deploy the worker

From the repo root:

```bash
modal deploy modal_vc_app.py
```

Record the two generated web endpoints:

- train endpoint
- convert endpoint

### 17. Put those URLs into the Flask `.env`

```dotenv
VC_MODAL_TRAINING_URL=https://your-workspace--audiocraft-vc-train.modal.run
VC_MODAL_CONVERSION_URL=https://your-workspace--audiocraft-vc-convert.modal.run
```

### 18. Rebuild the local or hosted Flask app

For local Docker:

```powershell
docker compose up --build -d
```

## Phase 8 — Expose Flask Publicly

### 19. Make sure Modal can reach Flask webhooks

Modal must reach:

```text
POST /api/vc/webhooks/modal
```

So `BASE_URL` must point to a public address for your Flask app.

If you are testing locally, use a tunnel such as:

- ngrok
- Cloudflare Tunnel

Then update:

```dotenv
BASE_URL=https://your-public-tunnel-or-domain
```

## Phase 9 — First Training Validation

### 20. Log into the app and open `/voice`

Create a user if needed, then visit:

```text
http://localhost:3001/voice
```

### 21. Create a test voice profile

Use one small test profile first.

### 22. Upload a tiny WAV dataset

Use a short, valid dataset for first verification, not your full production data.

Expected behavior:

- dataset upload succeeds
- dataset commit succeeds
- profile detail shows dataset minutes

### 23. Start one training job

Expected state progression:

- queued
- running
- succeeded or failed with a real error

### 24. Verify training artifacts

After success, verify:

- a `VoiceModelVersion` is created
- the profile gets an `active_model_version_id`
- R2 contains:
  - model artifact
  - config artifact

## Phase 10 — First Conversion Validation

### 25. Upload one small inference WAV

This should create a staged conversion job first, then upload the audio.

### 26. Start conversion

Expected state progression:

- uploading
- queued
- running
- succeeded or failed with a real error

### 27. Download and inspect the output

Verify:

- the output downloads successfully
- the audio is real converted output
- it is not just a pass-through copy of the input

## Phase 11 — Production Readiness Checks

### 28. Verify secrets alignment

These values must match between Flask and Modal:

- `VC_WEBHOOK_SECRET`
- `VC_MODAL_AUTH_TOKEN`
- R2 credentials and bucket

### 29. Verify quotas

Check the environment values you intend to run with:

- `VC_TRAININGS_PER_MONTH`
- `VC_CONVERSIONS_PER_DAY`
- `VC_MAX_UPLOAD_BYTES`

### 30. Keep the deployed fork pinned

Record and version:

- So-VITS repo URL
- So-VITS commit or tag
- Modal image changes
- secret template changes

## Quick Failure Triage

If training never starts:

- check `VC_MODAL_TRAINING_URL`
- check Modal auth token
- check `BASE_URL`

If smoke test fails:

- check `SOVITS_REPO_DIR`
- check command template names
- check `PYTHONPATH`

If training succeeds but no model is activated:

- check `SOVITS_MODEL_SOURCE`
- check `SOVITS_CONFIG_SOURCE`
- check webhook delivery

If conversion succeeds but output is wrong:

- check `SOVITS_INFER_CMD_TEMPLATE`
- check the selected model artifact
- inspect the actual So-VITS inference output path

## Minimum Commands Summary

Local app:

```powershell
Set-Location "y:\lyric_cover_staging\music-craft"
docker compose up --build -d
```

Modal deploy:

```bash
modal deploy modal_vc_app.py
```

Smoke test:

```bash
python -m scripts.vc.validate_sovits_setup --mode both --check-paths
```