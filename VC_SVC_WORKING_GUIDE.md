# VC/SVC Working Guide

This guide describes how the Voice Conversion module currently works in this repository, how its pieces fit together, and what you need to know to develop or operate it safely.

It is based on the live implementation in the Flask app, not just the original design notes.

For the concrete So-VITS-SVC runner layer added on top of this orchestration, see `VC_SOVITS_RUNNER_GUIDE.md`.

## What This Module Is

The VC/SVC module is a three-part system:

1. The Flask app provides authenticated profile, upload, training, conversion, polling, and download endpoints.
2. Cloudflare R2 stores dataset audio, trained model artifacts, conversion inputs, and conversion outputs.
3. A Modal GPU worker performs training and inference, then reports job state back to Flask through a signed webhook.

At the UI level, the entry page is the authenticated route `/voice`, rendered by the main blueprint and backed by the VC API under `/api/vc`.

## Main Files

These are the files that matter most when working on the module:

- `app/routes/vc_api.py`: Main VC API surface and webhook handling.
- `app/services/vc_dispatch.py`: Outbound calls from Flask to Modal.
- `app/services/r2.py`: Cloudflare R2 storage helpers.
- `app/models.py`: Voice profile, dataset, training job, model version, conversion job, and webhook event tables.
- `app/templates/voice-conversion.html`: Browser UI and client-side workflow.
- `modal_vc_app.py`: Modal worker endpoints for training and conversion.
- `migrations/versions/a3b4c5d6e7f8_add_vc_tables.py`: VC schema migration.

## Data Model

The module is centered on five main records:

### VoiceProfile

A user-owned logical voice identity.

- `id`
- `user_id`
- `name`
- `status`: usually `draft` or `ready`
- `active_model_version_id`

### VoiceDatasetFile

One uploaded dataset audio file attached to a profile.

- `voice_profile_id`
- `r2_key`
- `filename`
- `duration_sec`
- `size_bytes`
- `mime`

### VoiceTrainingJob

Tracks one model-training request.

- `voice_profile_id`
- `status`: `queued`, `running`, `succeeded`, `failed`, `canceled`
- `modal_call_id`
- `params_json`
- `error`
- `created_at`, `started_at`, `finished_at`

### VoiceModelVersion

Represents a trained model artifact set.

- `voice_profile_id`
- `training_job_id`
- `status`
- `r2_model_key`
- `r2_config_key`
- `metrics_json`

When training succeeds, the webhook marks the resulting model version as the profile's active model.

### VoiceConversionJob

Tracks one inference request.

- `voice_profile_id`
- `model_version_id`
- `status`
- `modal_call_id`
- `input_r2_key`
- `output_r2_key`
- `error`
- `created_at`, `finished_at`

### WebhookEvent

Stores received webhook event IDs to make webhook processing idempotent.

## Storage Layout

When R2 is configured, the system uses object storage. If R2 is not configured, parts of the module fall back to local disk under Flask's instance directory.

The code currently builds keys under these prefixes:

- Dataset files: `vc/users/{user_id}/profiles/{profile_id}/dataset/{file_id}/{filename}`
- Model artifacts: `vc/users/{user_id}/profiles/{profile_id}/models/{model_version_id}/...`
- Conversion input: `vc/users/{user_id}/profiles/{profile_id}/conversions/{job_id}/input/...`
- Conversion output: `vc/users/{user_id}/profiles/{profile_id}/conversions/{job_id}/output.wav`

The helper switch is simple:

- If `R2_ENDPOINT_URL` and `R2_ACCESS_KEY_ID` are set, Flask uses R2.
- Otherwise it writes files to local storage.

In practice, the full VC flow is designed around R2 and Modal. Local disk fallback is mostly useful for partial local development.

## End-to-End Flow

## 1. User creates a voice profile

The browser calls:

- `POST /api/vc/profiles`

The backend creates a `VoiceProfile` in `draft` state.

## 2. User uploads dataset files

The intended dataset flow is:

1. Request upload metadata from Flask.
2. Upload the raw file bytes.
3. Commit the uploaded file so Flask records duration and metadata.

Endpoints:

- `POST /api/vc/profiles/<profile_id>/dataset/upload-url`
- `PUT /api/vc/uploads/<file_id>`
- `POST /api/vc/profiles/<profile_id>/dataset/commit`

Important behavior:

- Flask creates a `VoiceDatasetFile` row first, then returns an upload target.
- When R2 is configured, the upload target is a presigned R2 `PUT` URL.
- Without R2, the upload target falls back to an internal application `PUT` endpoint.
- After upload, `dataset/commit` verifies the object exists and attempts to read WAV duration.

Current code assumes dataset duration inspection via Python's `wave` module, so WAV works best for metadata extraction. Other audio formats may upload successfully but not produce duration metadata.

## 3. User starts training

The browser calls:

- `POST /api/vc/profiles/<profile_id>/train`

Before dispatching, Flask checks:

- The profile exists and belongs to the current user.
- At least one dataset file exists.
- Monthly training quota is not exhausted.
- The user does not already have a running or queued training job.

Training parameters currently passed through:

- `epochs`
- `f0_method`

Flask creates a `VoiceTrainingJob` with status `queued`, then `app/services/vc_dispatch.py` posts a JSON payload to `VC_MODAL_TRAINING_URL`.

Payload fields sent to Modal:

- `training_job_id`
- `user_id`
- `profile_id`
- `dataset_r2_keys`
- `output_prefix`
- `params`
- `callback_url`

## 4. Modal performs training and calls back

The Modal worker in `modal_vc_app.py` does the following:

1. Validates optional bearer auth.
2. Sends a `running` webhook event.
3. Downloads dataset files from R2.
4. Executes the command configured in `VC_TRAIN_RUNNER_COMMAND`.
5. Requires the training runner to write `artifacts/model.pth` and `artifacts/config.json`.
6. Uploads the produced artifacts to R2.
7. Sends a `succeeded` or `failed` webhook event.

This is the most important current limitation in the module:

- The worker is wired correctly as infrastructure.
- The worker no longer fakes success with placeholder artifacts.
- A real VC engine still must be provided through the configured runner command and dependencies.

That means the training pipeline is production-safe in the sense that it fails loudly when no engine is configured, but it still depends on an operator-supplied So-VITS-SVC, RVC, or equivalent training command.

## 5. Flask applies training webhook state

The webhook endpoint is:

- `POST /api/vc/webhooks/modal`

It verifies:

- `X-VC-Timestamp`
- `X-VC-Signature`
- The timestamp is within a five-minute window.
- `event_id` exists.

Then it de-duplicates using `WebhookEvent` and applies monotonic status transitions only. Once a job reaches a terminal state, later status changes are ignored.

For successful training webhooks, Flask:

- updates the `VoiceTrainingJob`
- creates or updates a `VoiceModelVersion`
- stores `r2_model_key` and `r2_config_key`
- marks the profile's `active_model_version_id`
- sets the profile status to `ready`

## 6. User uploads conversion input

The intended conversion flow mirrors training:

1. Request upload metadata.
2. Upload the input vocal stem.
3. Start conversion.

Endpoints:

- `POST /api/vc/profiles/<profile_id>/convert/upload-url`
- `PUT /api/vc/uploads/conversion-input/<upload_id>`
- `POST /api/vc/profiles/<profile_id>/convert`

The current code now creates a staged `VoiceConversionJob` during `convert/upload-url`.

- `convert/upload-url` returns an `upload_url`, `job_id`, and `input_r2_key`.
- The upload target is a presigned R2 `PUT` URL when R2 is configured, or an internal fallback endpoint otherwise.
- `POST /profiles/<profile_id>/convert` starts the staged job by `job_id` after verifying the uploaded input exists.

This closes the previous conversion upload sequencing bug and makes the browser flow consistent with the backend.

## 7. User starts conversion

The conversion start route is:

- `POST /api/vc/profiles/<profile_id>/convert`

Flask checks:

- The profile exists and belongs to the user.
- The profile has an active model version.
- The active model version status is `ready`.
- Daily conversion quota is not exhausted.
- The user does not already have a queued or running conversion job.
- The staged conversion input exists in storage.

Then Flask dispatches to `VC_MODAL_CONVERSION_URL` with:

- `conversion_job_id`
- `user_id`
- `profile_id`
- `model_version_id`
- `model_artifact_keys`
- `input_r2_key`
- `output_r2_key`
- `callback_url`

## 8. Modal performs conversion and calls back

The Modal conversion worker currently does this:

1. Downloads the model artifacts from R2.
2. Downloads the input audio from R2.
3. Executes the command configured in `VC_CONVERT_RUNNER_COMMAND`.
4. Requires the conversion runner to write `artifacts/output.wav`.
5. Uploads the output WAV to R2.
6. Sends a webhook back to Flask.

So, just like training:

- the dispatch, storage, and webhook infrastructure are in place
- real VC/SVC inference still depends on the operator-provided runner command and ML stack

## 9. User polls and downloads output

The browser polls:

- `GET /api/vc/training-jobs/<job_id>`
- `GET /api/vc/conversion-jobs/<job_id>`

When conversion succeeds, the browser downloads from:

- `GET /api/vc/conversion-jobs/<job_id>/download`

That download route streams from R2 when configured, otherwise from local storage.

## Quotas and Concurrency Rules

The module enforces simple usage limits via environment variables:

- `VC_TRAININGS_PER_MONTH`, default `3`
- `VC_CONVERSIONS_PER_DAY`, default `3`
- `VC_MAX_UPLOAD_BYTES`, default `104857600`

Quota counting only considers jobs with status `succeeded`.

Concurrency rules are stricter:

- Only one queued or running training job per user at a time.
- Only one queued or running conversion job per user at a time.

This behavior is enforced in the Flask routes before dispatching to Modal.

## Environment Variables

To make the full VC stack work, these variables matter:

### Flask app side

- `BASE_URL`: Public URL Modal should call back to.
- `VC_MODAL_TRAINING_URL`: Deployed Modal training endpoint.
- `VC_MODAL_CONVERSION_URL`: Deployed Modal conversion endpoint.
- `VC_MODAL_AUTH_TOKEN`: Optional bearer token sent to Modal.
- `VC_WEBHOOK_SECRET`: Shared HMAC secret used for webhook verification.
- `VC_TRAININGS_PER_MONTH`
- `VC_CONVERSIONS_PER_DAY`
- `VC_MAX_UPLOAD_BYTES`

### R2 storage

- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `R2_ENDPOINT_URL`
- `R2_PUBLIC_BASE_URL` optional

### Modal worker side

The Modal secret needs the same R2 credentials plus:

- `VC_WEBHOOK_SECRET`
- `VC_MODAL_AUTH_TOKEN` if auth is enabled
- `VC_TRAIN_RUNNER_COMMAND`
- `VC_CONVERT_RUNNER_COMMAND`
- optional runner timeout env vars

## Frontend Behavior

The browser implementation lives inline in `app/templates/voice-conversion.html`.

Important frontend details:

- It fetches a CSRF token from `/auth/csrf-token`.
- All authenticated non-GET VC requests include `X-CSRFToken`.
- Dataset upload uses a request-upload-commit sequence.
- Training and conversion status are polled every 2.5 seconds.
- On successful conversion it exposes `/api/vc/conversion-jobs/<job_id>/download` as a download link.

The frontend now stages conversion jobs before upload and passes `job_id` into the conversion start request. Uploads go directly to R2 with presigned URLs when configured, otherwise through Flask fallback endpoints.

## What Is Implemented vs What Is Stubbed

### Implemented

- Authenticated VC pages and routes
- Profile CRUD for create/list/detail
- Dataset file record creation and upload
- Staged conversion-job upload flow
- R2 storage helpers and R2-backed artifact flow
- Presigned R2 upload targets when R2 is configured
- Training job and conversion job persistence
- Dispatch from Flask to Modal
- Signed webhook verification and idempotency
- Automatic active-model activation after successful training
- Download of conversion result
- Fail-fast Modal runner contract for real training and conversion engines

### Stubbed or incomplete

- Bundled So-VITS-SVC or RVC implementation inside this repository
- Rich dataset validation beyond basic size and optional WAV duration parsing

## How To Work On The Module

## If you are working on infrastructure only

Focus on these files:

- `app/services/r2.py`
- `app/services/vc_dispatch.py`
- `app/routes/vc_api.py`
- `modal_vc_app.py`

Typical tasks:

- change bucket layout
- add retry logic around Modal callbacks or dispatch
- add richer webhook payloads
- convert internal uploads into real presigned R2 uploads

## If you are implementing real training/inference

Your primary file is `modal_vc_app.py`.

You do not need to change Flask-side orchestration first. The worker already exposes a runner contract.

You will also likely need to:

- add your actual model dependencies to the Modal image
- implement `VC_TRAIN_RUNNER_COMMAND`
- implement `VC_CONVERT_RUNNER_COMMAND`
- write preprocessing and feature extraction steps
- emit `artifacts/model.pth`, `artifacts/config.json`, and optionally `artifacts/metrics.json`
- emit `artifacts/output.wav` for conversion
- return useful metrics in the training webhook payload

## Recommended developer workflow

1. Confirm database tables exist via migrations.
2. Confirm R2 credentials and bucket access work.
3. Deploy `modal_vc_app.py` and verify the two endpoint URLs.
4. Set `VC_MODAL_TRAINING_URL`, `VC_MODAL_CONVERSION_URL`, and `VC_WEBHOOK_SECRET` in Flask.
5. Create a profile from the UI.
6. Upload a WAV dataset and verify `VoiceDatasetFile` rows are created.
7. Start training and verify webhook state transitions.
8. Confirm a `VoiceModelVersion` is created and profile status becomes `ready`.
9. Configure the Modal runner commands and verify they write the required artifacts.

## Debugging Checklist

If the module is not working, check these first:

### Training never leaves queued

- `VC_MODAL_TRAINING_URL` is missing or wrong.
- Modal endpoint auth rejects Flask requests.
- Modal cannot read R2 objects.
- `BASE_URL` is not publicly reachable from Modal.

### Training reaches running but never succeeds

- Modal worker crashed in the placeholder or real training logic.
- Callback failed because `VC_WEBHOOK_SECRET` mismatched.
- Webhook payload lacks `event_id` or `job_id`.

### Model never becomes active

- Training webhook did not include `artifact_keys`.
- The webhook updated the training job but not model artifacts.
- The profile was not updated to the new `active_model_version_id`.

### Conversion upload fails

- Check that the staged job was created by `POST /api/vc/profiles/<profile_id>/convert/upload-url`.
- Check that the uploaded object exists at `input_r2_key` before `POST /api/vc/profiles/<profile_id>/convert`.

### Conversion succeeds but output is identical to input

- Your configured conversion runner is copying the input or writing a pass-through output.

## Practical Bottom Line

Today, the module is best understood as a production-ready orchestration layer around an external VC engine:

- the API shape exists
- persistence exists
- R2 storage exists
- Modal dispatch exists
- webhook reconciliation exists

The remaining work is not Flask orchestration. It is choosing, packaging, and operating the actual VC/SVC engine behind the Modal runner commands.