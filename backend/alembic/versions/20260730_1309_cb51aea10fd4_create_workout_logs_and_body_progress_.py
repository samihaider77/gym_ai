"""create_workout_logs_and_body_progress_tables

Revision ID: cb51aea10fd4
Revises: db851f180762
Create Date: 2026-07-30 13:09:11.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'cb51aea10fd4'
down_revision: Union[str, None] = 'db851f180762'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create workout_logs table
    op.create_table(
        'workout_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workout_session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workout_exercise_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('set_number', sa.Integer(), nullable=False),
        sa.Column('completed_reps', sa.Integer(), nullable=False),
        sa.Column('completed_weight', sa.Float(), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('rest_seconds', sa.Integer(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['workout_exercise_id'], ['workout_exercises.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workout_session_id'], ['workout_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workout_session_id', 'workout_exercise_id', 'set_number', name='uq_session_exercise_set')
    )
    op.create_index(op.f('ix_workout_logs_id'), 'workout_logs', ['id'], unique=False)
    op.create_index(op.f('ix_workout_logs_workout_session_id'), 'workout_logs', ['workout_session_id'], unique=False)
    op.create_index(op.f('ix_workout_logs_workout_exercise_id'), 'workout_logs', ['workout_exercise_id'], unique=False)

    # 2. Create body_progress table
    op.create_table(
        'body_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('weight_kg', sa.Float(), nullable=False),
        sa.Column('body_fat_percentage', sa.Float(), nullable=True),
        sa.Column('bmi', sa.Float(), nullable=True),
        sa.Column('chest_cm', sa.Float(), nullable=True),
        sa.Column('waist_cm', sa.Float(), nullable=True),
        sa.Column('hips_cm', sa.Float(), nullable=True),
        sa.Column('left_arm_cm', sa.Float(), nullable=True),
        sa.Column('right_arm_cm', sa.Float(), nullable=True),
        sa.Column('left_thigh_cm', sa.Float(), nullable=True),
        sa.Column('right_thigh_cm', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_body_progress_id'), 'body_progress', ['id'], unique=False)
    op.create_index(op.f('ix_body_progress_user_id'), 'body_progress', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_body_progress_user_id'), table_name='body_progress')
    op.drop_index(op.f('ix_body_progress_id'), table_name='body_progress')
    op.drop_table('body_progress')

    op.drop_index(op.f('ix_workout_logs_workout_exercise_id'), table_name='workout_logs')
    op.drop_index(op.f('ix_workout_logs_workout_session_id'), table_name='workout_logs')
    op.drop_index(op.f('ix_workout_logs_id'), table_name='workout_logs')
    op.drop_table('workout_logs')
