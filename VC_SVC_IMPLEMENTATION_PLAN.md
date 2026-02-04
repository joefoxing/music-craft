# VC/SVC Implementation Plan (Modal + Cloudflare R2)

## 0) Scope

- Users upload isolated vocal stems (dataset), train a custom singing voice model, then convert new vocal stems using that model.
- Workloads run on Modal (GPU).
- Artifacts are stored in Cloudflare R2.

### Locked product decisions

- Dataset size target: **3–10 minutes** of isolated vocals per training
- Training quota: **3 trainings/month/user**
- Conversion quota: **3 conversions/day/user**
- Retention: trained model artifacts kept **forever**

## 1) Architecture overview

### Data flow

1. **Client/UI** uploads dataset audio to R2 (via presigned upload URL returned by Flask).
2. **Flask** records dataset metadata and validates limits.
3. **Client/UI** requests training.
4. **Flask** creates a `VoiceTrainingJob` record and triggers the Modal training function.
5. **Modal** downloads dataset from R2, trains the model, uploads artifacts to R2.
6. **Modal** calls back to Flask via a signed webhook with job results.
7. **Client/UI** polls job status until complete.
8. **Client/UI** uploads a conversion input to R2, requests conversion.
9. **Modal** performs inference and uploads the output stem to R2.
10. **Modal** calls back to Flask; user downloads the output.

### Invariants

- Jobs are **asynchronous** and should be safe under retries.
- Webhook callbacks must be **authenticated** and **idempotent**.
- Users can only access profiles/jobs/artifacts they own.

## 2) Storage plan (Cloudflare R2)

### Key layout

Use consistent prefixes so ownership and cleanup are straightforward:

- Dataset uploads:
  - `vc/users/{user_id}/profiles/{profile_id}/dataset/{file_id}/{filename}`
- Model artifacts (kept forever):
  - `vc/users/{user_id}/profiles/{profile_id}/models/{model_version_id}/model.pth`
  - `vc/users/{user_id}/profiles/{profile_id}/models/{model_version_id}/config.json`
  - Optional indices (if used):
    - `vc/users/{user_id}/profiles/{profile_id}/models/{model_version_id}/index.faiss`
- Conversion IO:
  - `vc/users/{user_id}/profiles/{profile_id}/conversions/{job_id}/input.wav`
  - `vc/users/{user_id}/profiles/{profile_id}/conversions/{job_id}/output.wav`

### Download strategy

- Prefer a Flask endpoint that issues a **short-lived presigned GET** (or streams from R2) after verifying ownership.

## 3) Database models (SQLAlchemy + Alembic)

Introduce these tables (names are suggestions):

### `VoiceProfile`

- `id`
- `user_id`
- `name`
- `status` (`draft|ready|disabled`)
- `active_model_version_id` (nullable)
- `created_at`, `updated_at`

### `VoiceDatasetFile`

- `id`
- `voice_profile_id`
- `r2_key`
- `filename`
- `duration_sec`
- `size_bytes`
- `sha256` (optional)
- `mime`
- `created_at`

### `VoiceTrainingJob`

- `id`
- `user_id`
- `voice_profile_id`
- `status` (`queued|running|succeeded|failed|canceled`)
- `modal_call_id` (optional)
- `params_json`
- `error`
- `created_at`, `started_at`, `finished_at`

### `VoiceModelVersion`

- `id`
- `voice_profile_id`
- `training_job_id`
- `status` (`ready|failed|disabled`)
- `r2_model_key`
- `r2_config_key`
- `metrics_json`
- `created_at`

### `VoiceConversionJob`

- `id`
- `user_id`
- `voice_profile_id`
- `model_version_id`
- `status` (`queued|running|succeeded|failed|canceled`)
- `modal_call_id` (optional)
- `input_r2_key`
- `output_r2_key`
- `input_duration_sec`
- `error`
- `created_at`, `finished_at`

### Callback idempotency

- Add a small table or column to track processed webhook events:
  - `WebhookEvent(id, source, event_id, received_at)`

## 4) Limits and quotas (server-enforced)

### Dataset limits (for 3–10 min target)

Enforce at dataset commit time and before training:

- Allowed formats: wav/flac (optionally accept mp3 but convert to wav server-side)
- Max file size: recommended `<= 200MB/file`
- Max single-file duration: recommended `<= 6 minutes`
- Max total dataset duration per profile: recommended `<= 12 minutes`

### Training quota: 3 trainings/month/user

- Count only `VoiceTrainingJob` with `status='succeeded'` and `finished_at` in the current month.
- If quota exceeded: return `429` with remaining quota metadata.

### Conversion quota: jobs/day/user

- Count only `VoiceConversionJob` with `status='succeeded'` and `finished_at` in the current day.
- The cap value should be set in config, e.g. `VC_CONVERSIONS_PER_DAY`.

### Concurrency limits

- One running training job per user at a time.
- Optionally one running conversion job per user at a time.

## 5) Flask API design

Create a blueprint (suggestion): `/api/vc/*`.

All mutating routes:

- Require session auth
- Require CSRF header per the existing app pattern
- Rate limit appropriately

### Profiles

- `POST /api/vc/profiles` create profile
- `GET /api/vc/profiles` list profiles
- `GET /api/vc/profiles/<profile_id>` profile detail (include dataset summary, active model, recent jobs)
- `DELETE /api/vc/profiles/<profile_id>` delete or soft-delete

### Dataset

- `POST /api/vc/profiles/<profile_id>/dataset/upload-url`
  - Returns: `{ upload_url, r2_key, file_id }`
- `POST /api/vc/profiles/<profile_id>/dataset/commit`
  - Input: `{ file_id, r2_key, filename, size_bytes }`
  - Server validates object exists and probes duration
- `DELETE /api/vc/dataset-files/<file_id>`

### Training

- `POST /api/vc/profiles/<profile_id>/train`
  - Validates dataset limits
  - Enforces monthly quota
  - Creates `VoiceTrainingJob(status='queued')`
  - Triggers Modal training
- `GET /api/vc/training-jobs/<job_id>`
- `POST /api/vc/training-jobs/<job_id>/cancel` (optional)

### Conversion

- `POST /api/vc/profiles/<profile_id>/convert/upload-url`
- `POST /api/vc/profiles/<profile_id>/convert`
  - Requires `active_model_version_id`
  - Enforces jobs/day quota
  - Creates `VoiceConversionJob(status='queued')`
  - Triggers Modal conversion
- `GET /api/vc/conversion-jobs/<job_id>`
- `GET /api/vc/conversion-jobs/<job_id>/download`

### Webhooks

- `POST /api/vc/webhooks/modal`
  - Validates signature + timestamp
  - Updates job status and links artifacts
  - Idempotent via `event_id`

## 6) Modal GPU implementation

### Packaging strategy

- Modal app module (example): `modal_vc_app.py`
- Pin a stable SVC stack:
  - So-VITS-SVC 4.x
  - Compatible torch/cuda versions

### Training function

Input payload (example):

- `training_job_id`
- `user_id`
- `profile_id`
- `dataset_r2_keys[]`
- `output_prefix`
- `params` (epochs, f0 method, sample rate, etc.)

Steps:

- Download dataset from R2
- Preprocess (resample, slicing)
- Feature extraction (content features + F0)
- Train (defaults tuned for 3–10 minutes dataset)
- Upload artifacts to R2
- Webhook callback to Flask with:
  - `event_id`, `job_type='training'`, `job_id`, `status`, `artifact_keys`, `metrics`, `error`

### Conversion function

Input payload (example):

- `conversion_job_id`
- `user_id`
- `profile_id`
- `model_version_id`
- `model_artifact_keys`
- `input_r2_key`
- `output_r2_key`

Steps:

- Download model artifacts + input.wav
- Inference
- Upload output.wav
- Webhook callback with:
  - `event_id`, `job_type='conversion'`, `job_id`, `status`, `output_key`, `error`

## 7) Webhook security

- Shared secret in env var (example): `VC_WEBHOOK_SECRET`
- HMAC signature header + timestamp header
- Reject invalid signature with `401`
- Replay protection via timestamp tolerance
- Idempotency via `event_id`

## 8) UI plan (MVP)

Create a page (suggestion): `/voice` with a JS UI.

MVP components:

- Create/list profiles
- Upload dataset files
- Show dataset summary (minutes uploaded)
- Trigger training + show monthly trainings remaining
- Training status polling
- Conversion upload + trigger + show daily conversions remaining
- Download output

## 9) Testing and verification

### Unit tests

- Training quota counting (3/month)
- Conversion jobs/day quota
- Ownership checks (user cannot access other users’ objects)
- Webhook signature verification + idempotency

### Integration tests

- Profile create -> dataset upload/commit -> train -> webhook -> model ready
- Convert -> webhook -> download

### Manual QA

- Oversized dataset rejected with meaningful error
- Concurrent training prevented
- Webhook replay does not duplicate updates

## 10) Deployment and operations

### Env vars

- R2:
  - `R2_ENDPOINT`, `R2_BUCKET`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`
- Modal:
  - Modal auth vars/secrets
- Webhooks:
  - `VC_WEBHOOK_SECRET`
- Quotas:
  - `VC_TRAININGS_PER_MONTH=3`
  - `VC_CONVERSIONS_PER_DAY=3`

### Observability

- Store job errors in DB
- Surface last error in UI
- Optionally store a link to Modal logs in the job record

## 11) Recommended rollout milestones

- Milestone A: Models + migrations + R2 helper
- Milestone B: Profile + dataset APIs (upload-url + commit)
- Milestone C: Training orchestration + quota enforcement (Modal stub)
- Milestone D: Modal training + webhook integration
- Milestone E: Conversion jobs + Modal inference
- Milestone F: UI MVP end-to-end
- Milestone G: Hardening (rate limits, audit logs, retries, monitoring)
