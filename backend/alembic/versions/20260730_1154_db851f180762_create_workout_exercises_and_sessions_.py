"""create_workout_exercises_and_sessions_tables

Revision ID: db851f180762
Revises: 5b5910419944
Create Date: 2026-07-30 11:54:36.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'db851f180762'
down_revision: Union[str, None] = '5b5910419944'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create workout_exercises table
    op.create_table(
        'workout_exercises',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workout_day_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('exercise_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('sets', sa.Integer(), server_default='3', nullable=False),
        sa.Column('reps', sa.Integer(), server_default='10', nullable=False),
        sa.Column('target_weight', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('rest_seconds', sa.Integer(), server_default='60', nullable=True),
        sa.Column('tempo', sa.String(length=50), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('distance', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['workout_day_id'], ['workout_days.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workout_day_id', 'order_index', name='uq_day_order_index')
    )
    op.create_index(op.f('ix_workout_exercises_id'), 'workout_exercises', ['id'], unique=False)
    op.create_index(op.f('ix_workout_exercises_workout_day_id'), 'workout_exercises', ['workout_day_id'], unique=False)
    op.create_index(op.f('ix_workout_exercises_exercise_id'), 'workout_exercises', ['exercise_id'], unique=False)

    # 2. Create workout_sessions table
    op.create_table(
        'workout_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workout_plan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workout_day_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), server_default='0', nullable=False),
        sa.Column('calories_burned', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='IN_PROGRESS', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workout_day_id'], ['workout_days.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workout_plan_id'], ['workout_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workout_sessions_id'), 'workout_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_workout_sessions_user_id'), 'workout_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_workout_sessions_workout_plan_id'), 'workout_sessions', ['workout_plan_id'], unique=False)
    op.create_index(op.f('ix_workout_sessions_workout_day_id'), 'workout_sessions', ['workout_day_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_workout_sessions_workout_day_id'), table_name='workout_sessions')
    op.drop_index(op.f('ix_workout_sessions_workout_plan_id'), table_name='workout_sessions')
    op.drop_index(op.f('ix_workout_sessions_user_id'), table_name='workout_sessions')
    op.drop_index(op.f('ix_workout_sessions_id'), table_name='workout_sessions')
    op.drop_table('workout_sessions')

    op.drop_index(op.f('ix_workout_exercises_exercise_id'), table_name='workout_exercises')
    op.drop_index(op.f('ix_workout_exercises_workout_day_id'), table_name='workout_exercises')
    op.drop_index(op.f('ix_workout_exercises_id'), table_name='workout_exercises')
    op.drop_table('workout_exercises')
