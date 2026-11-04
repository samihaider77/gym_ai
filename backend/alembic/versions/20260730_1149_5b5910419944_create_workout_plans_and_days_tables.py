"""create_workout_plans_and_days_tables

Revision ID: 5b5910419944
Revises: 443f2160ae86
Create Date: 2026-07-30 11:49:05.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5b5910419944'
down_revision: Union[str, None] = '443f2160ae86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create workout_plans table
    op.create_table(
        'workout_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('goal', sa.String(length=100), nullable=False),
        sa.Column('difficulty', sa.String(length=50), nullable=False),
        sa.Column('duration_weeks', sa.Integer(), server_default='4', nullable=False),
        sa.Column('days_per_week', sa.Integer(), server_default='4', nullable=False),
        sa.Column('is_template', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_plan_name')
    )
    op.create_index(op.f('ix_workout_plans_id'), 'workout_plans', ['id'], unique=False)
    op.create_index(op.f('ix_workout_plans_user_id'), 'workout_plans', ['user_id'], unique=False)
    op.create_index(op.f('ix_workout_plans_is_active'), 'workout_plans', ['is_active'], unique=False)

    # 2. Create workout_days table
    op.create_table(
        'workout_days',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workout_plan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('estimated_duration_minutes', sa.Integer(), server_default='60', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['workout_plan_id'], ['workout_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workout_plan_id', 'day_number', name='uq_plan_day_number')
    )
    op.create_index(op.f('ix_workout_days_id'), 'workout_days', ['id'], unique=False)
    op.create_index(op.f('ix_workout_days_workout_plan_id'), 'workout_days', ['workout_plan_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_workout_days_workout_plan_id'), table_name='workout_days')
    op.drop_index(op.f('ix_workout_days_id'), table_name='workout_days')
    op.drop_table('workout_days')

    op.drop_index(op.f('ix_workout_plans_is_active'), table_name='workout_plans')
    op.drop_index(op.f('ix_workout_plans_user_id'), table_name='workout_plans')
    op.drop_index(op.f('ix_workout_plans_id'), table_name='workout_plans')
    op.drop_table('workout_plans')
