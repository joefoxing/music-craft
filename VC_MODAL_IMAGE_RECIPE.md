# VC Modal Image Recipe

This guide shows one concrete way to build the Modal worker image for the VC/SVC module with the long-term package-based `voicepaw/so-vits-svc-fork` repository.

Use this together with `VC_SOVITS_RUNNER_GUIDE.md` and `VC_SOVITS_4X_MODAL_SECRET.example`.

## Goal

The Modal image needs to provide:

1. Python dependencies used by the worker itself.
2. System packages commonly required by audio pipelines.
3. A real So-VITS-SVC repository checkout at `SOVITS_REPO_DIR`.
4. Access to the repo's CLI scripts expected by the configured command templates.
5. The repository's `scripts/vc` runner modules.

## Recommended Image Pattern

Use a Debian-based Python 3.11 image, install system packages first, then clone and install your So-VITS repository during the image build.

Example shape for `modal_vc_app.py`:

```python
import modal

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
        "torch==2.1.0",
        "torchaudio==2.1.0",
    )
    .run_commands(
        f"git clone {SOVITS_GIT_URL} /root/so-vits-svc",
        f"cd /root/so-vits-svc && git checkout {SOVITS_GIT_REF}",
        "cd /root/so-vits-svc && pip install .",
    )
    .add_local_dir("scripts", remote_path="/root/app/scripts")
    .env({"PYTHONPATH": "/root/app"})
)
```

This pattern makes `python -m scripts.vc.run_training` and `python -m scripts.vc.run_inference` import correctly inside Modal because `scripts` is copied into the image and `PYTHONPATH` includes `/root/app`.
It also installs the `so_vits_svc_fork` package so the runner can call `python -m so_vits_svc_fork ...` subcommands.

## Why `add_local_dir("scripts")` matters

The VC runner commands live in this repository, not in the So-VITS checkout.

If you do not copy the local `scripts` directory into the Modal image and expose it via `PYTHONPATH`, these commands will fail:

- `python -m scripts.vc.run_training`
- `python -m scripts.vc.run_inference`
- `python -m scripts.vc.validate_sovits_setup`

## Recommended Secret + Image Pairing

The following should match each other:

- Modal image clones So-VITS into `/root/so-vits-svc`
- Modal secret sets `SOVITS_REPO_DIR=/root/so-vits-svc`

If you clone somewhere else, update `SOVITS_REPO_DIR` accordingly.

## Smoke Test Before Deploying Real Jobs

Once the image and secret are ready, run the smoke test command inside the Modal image during development:

```bash
python -m scripts.vc.validate_sovits_setup --mode both --check-paths
```

That validates:

- required VC runner env vars exist
- required So-VITS template env vars exist
- template rendering works
- `SOVITS_REPO_DIR` exists when `--check-paths` is used

It does not train a model or consume GPU time. It is only a contract check.

## What You Still Need To Supply

This recipe does not choose a So-VITS fork for you.

You still need to provide:

- the exact git URL
- the exact tag or commit
- any extra Python dependencies your fork requires
- any CLI-flag adjustments needed by your fork

Those values should be versioned together with your Modal deployment, not discovered ad hoc at runtime.

## Recommended Rollout Sequence

1. Update the Modal image to clone your tested So-VITS fork.
2. Add the local `scripts` directory into the image and set `PYTHONPATH`.
3. Create the Modal secret using `VC_SOVITS_4X_MODAL_SECRET.example` as the base.
4. Run `python -m scripts.vc.validate_sovits_setup --mode both --check-paths` inside the built image.
5. Deploy `modal_vc_app.py`.
6. Run one training job with a tiny dataset.
7. Run one conversion job and verify that the output is real audio, not a pass-through artifact.