"""Add voice-clone tables (voice_profiles, voice_dataset_files, voice_training_jobs,
voice_model_versions, voice_conversion_jobs)

Revision ID: a3b4c5d6e7f8
Revises: f1a2b3c4d5e6
Create Date: 2026-04-05 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from app.models import GUID


revision = 'a3b4c5d6e7f8'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # voice_profiles
    op.create_table(
        'voice_profiles',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('user_id', GUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('active_model_version_id', GUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_voice_profiles_user_id', 'voice_profiles', ['user_id'])

    # voice_dataset_files
    op.create_table(
        'voice_dataset_files',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('voice_profile_id', GUID(), sa.ForeignKey('voice_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('r2_key', sa.Text(), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('duration_sec', sa.Float(), nullable=True),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('sha256', sa.String(64), nullable=True),
        sa.Column('mime', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_voice_dataset_files_voice_profile_id', 'voice_dataset_files', ['voice_profile_id'])

    # voice_training_jobs
    op.create_table(
        'voice_training_jobs',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('user_id', GUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('voice_profile_id', GUID(), sa.ForeignKey('voice_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='queued'),
        sa.Column('modal_call_id', sa.String(200), nullable=True),
        sa.Column('params_json', sa.JSON(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_voice_training_jobs_user_id', 'voice_training_jobs', ['user_id'])
    op.create_index('ix_voice_training_jobs_voice_profile_id', 'voice_training_jobs', ['voice_profile_id'])

    # voice_model_versions
    op.create_table(
        'voice_model_versions',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('voice_profile_id', GUID(), sa.ForeignKey('voice_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('training_job_id', GUID(), sa.ForeignKey('voice_training_jobs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='ready'),
        sa.Column('r2_model_key', sa.Text(), nullable=True),
        sa.Column('r2_config_key', sa.Text(), nullable=True),
        sa.Column('metrics_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_voice_model_versions_voice_profile_id', 'voice_model_versions', ['voice_profile_id'])
    op.create_index('ix_voice_model_versions_training_job_id', 'voice_model_versions', ['training_job_id'])

    # voice_conversion_jobs
    op.create_table(
        'voice_conversion_jobs',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('user_id', GUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('voice_profile_id', GUID(), sa.ForeignKey('voice_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('model_version_id', GUID(), sa.ForeignKey('voice_model_versions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='queued'),
        sa.Column('modal_call_id', sa.String(200), nullable=True),
        sa.Column('input_r2_key', sa.Text(), nullable=True),
        sa.Column('output_r2_key', sa.Text(), nullable=True),
        sa.Column('input_duration_sec', sa.Float(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_voice_conversion_jobs_user_id', 'voice_conversion_jobs', ['user_id'])
    op.create_index('ix_voice_conversion_jobs_voice_profile_id', 'voice_conversion_jobs', ['voice_profile_id'])
    op.create_index('ix_voice_conversion_jobs_model_version_id', 'voice_conversion_jobs', ['model_version_id'])


def downgrade() -> None:
    op.drop_table('voice_conversion_jobs')
    op.drop_table('voice_model_versions')
    op.drop_table('voice_training_jobs')
    op.drop_table('voice_dataset_files')
    op.drop_table('voice_profiles')
