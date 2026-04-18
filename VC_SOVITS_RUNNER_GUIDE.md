# So-VITS-SVC Runner Guide

This guide explains how to use the concrete runner scripts in `scripts/vc` with the VC/SVC module.

These scripts are designed to run inside the Modal worker and translate the generic VC job contract into a `voicepaw/so-vits-svc-fork` execution flow.

## Files

- `scripts/vc/run_training.py`
- `scripts/vc/run_inference.py`
- `scripts/vc/common.py`

## What The Runner Does

### Training

`scripts/vc/run_training.py`:

1. Reads the Modal-provided VC job environment.
2. Resolves the So-VITS repo checkout location.
3. Stages the dataset under `dataset_raw/<speaker_name>`.
4. Optionally runs resample, config generation, and HuBERT/F0 preprocessing command templates.
5. Runs the training command template.
6. Collects the produced model/config artifacts.
7. Copies them into:
   - `artifacts/model.pth`
   - `artifacts/config.json`
7. Optionally copies `artifacts/metrics.json`.

### Inference

`scripts/vc/run_inference.py`:

1. Reads the Modal-provided model, config, and input paths.
2. Runs the So-VITS inference command template.
3. Verifies that `artifacts/output.wav` was created.

## Required Modal Worker Environment

These are already provided by `modal_vc_app.py` to the runner commands:

- `VC_JOB_ID`
- `VC_JOB_DIR`
- `VC_JOB_PAYLOAD_PATH`
- `VC_ARTIFACTS_DIR`
- `VC_DATASET_DIR` for training
- `VC_MODEL_PATH` for conversion
- `VC_CONFIG_PATH` for conversion
- `VC_INPUT_PATH` for conversion
- `VC_OUTPUT_PATH` for conversion
- `VC_PARAMS_JSON` for training

## Required So-VITS Environment

At minimum, define these in the Modal secret:

- `SOVITS_REPO_DIR`
- `SOVITS_RESAMPLE_CMD_TEMPLATE`
- `SOVITS_CONFIG_CMD_TEMPLATE`
- `SOVITS_HUBERT_CMD_TEMPLATE`
- `SOVITS_TRAIN_CMD_TEMPLATE`
- `SOVITS_MODEL_SOURCE`
- `SOVITS_INFER_CMD_TEMPLATE`

You will usually also define:

- `SOVITS_CONFIG_TYPE`
- `SOVITS_SPEAKER_NAME`
- `SOVITS_SAMPLE_RATE`
- `SOVITS_CONFIG_SOURCE`
- `SOVITS_METRICS_SOURCE`

## Training Placeholder Variables

The training command templates can use:

- `{repo_dir}`
- `{job_dir}`
- `{dataset_dir}`
- `{artifacts_dir}`
- `{payload_path}`
- `{param_epochs}`
- `{param_f0_method}`
- `{param_workspace_dir}`
- `{param_speaker_name}`
- `{param_sample_rate}`
- `{param_config_type}`
- `{param_dataset_raw_dir}`
- `{param_processed_data_dir}`
- `{param_filelists_dir}`
- `{param_model_dir}`
- `{param_config_output_path}`

The `param_*` values are supplied by the runner based on `VC_PARAMS_JSON` plus its derived working directories.

## Inference Placeholder Variables

The inference command template can use:

- `{repo_dir}`
- `{job_dir}`
- `{artifacts_dir}`
- `{payload_path}`
- `{model_path}`
- `{config_path}`
- `{input_path}`
- `{output_path}`
- `{param_speaker_name}`
- `{param_transpose}`
- `{param_f0_method}`

## Example Modal Secret Values

These are examples only. Adjust them to your So-VITS-SVC fork and CLI.

For a ready-to-paste example file, see `VC_SOVITS_4X_MODAL_SECRET.example`.
For a concrete Modal worker image layout, see `VC_MODAL_IMAGE_RECIPE.md`.

```dotenv
VC_TRAIN_RUNNER_COMMAND=python -m scripts.vc.run_training
VC_CONVERT_RUNNER_COMMAND=python -m scripts.vc.run_inference

SOVITS_REPO_DIR=/root/so-vits-svc

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

The exact file names and CLI flags depend on the So-VITS-SVC fork you use. The point of the runner scripts is to keep those engine-specific details out of Flask and Modal orchestration code.

## Artifact Rules

Training must finish with these outputs copied into the runner artifacts directory:

- `artifacts/model.pth`
- `artifacts/config.json`

Optional:

- `artifacts/metrics.json`

Conversion must finish with:

- `artifacts/output.wav`

If those files are not produced, the job fails and the Modal worker reports a failure back to Flask.

## Recommended Modal Image Additions

Your Modal image will usually need more than `torch` and `torchaudio`.

Typical additions:

- So-VITS-SVC repository checkout
- `ffmpeg`
- `libsndfile`
- any model-specific Python dependencies
- any GPU-specific runtime requirements required by your chosen fork

Whether you bake the repo into the image or clone it during build is up to you, but `SOVITS_REPO_DIR` must point to a real checkout inside the Modal container.

## Operational Advice

- Keep the Flask app generic and engine-agnostic.
- Keep engine-specific CLI details in the So-VITS env templates.
- Version the So-VITS fork and CLI flags together with your Modal image.
- Treat `SOVITS_MODEL_SOURCE` and `SOVITS_INFER_CMD_TEMPLATE` as part of your deploy contract, not as optional tuning.

## Failure Modes To Expect

- Missing `SOVITS_REPO_DIR`: runner fails immediately.
- Wrong command template: subprocess exits non-zero and the job fails.
- Wrong artifact glob: training finishes but artifact collection fails.
- Wrong output path handling: inference runs but `artifacts/output.wav` is missing.

That failure behavior is intentional. It prevents the system from reporting fake training or conversion success when the underlying engine is misconfigured.

## Smoke Test

Before deploying real jobs, run:

```bash
python -m scripts.vc.validate_sovits_setup --mode both --check-paths
```

That validates the required env vars, template rendering, and the presence of `SOVITS_REPO_DIR`.