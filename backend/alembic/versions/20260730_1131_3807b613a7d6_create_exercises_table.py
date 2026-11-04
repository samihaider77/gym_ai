"""create_exercises_table

Revision ID: 3807b613a7d6
Revises: c8d143014e59
Create Date: 2026-07-30 11:31:59.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3807b613a7d6'
down_revision: Union[str, None] = 'c8d143014e59'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'exercises',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('slug', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('difficulty_level', sa.String(length=50), nullable=False),
        sa.Column('exercise_type', sa.String(length=50), nullable=False),
        sa.Column('force_type', sa.String(length=50), nullable=True),
        sa.Column('mechanic_type', sa.String(length=50), nullable=True),
        sa.Column('equipment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_compound', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_exercises_id'), 'exercises', ['id'], unique=False)
    op.create_index(op.f('ix_exercises_name'), 'exercises', ['name'], unique=True)
    op.create_index(op.f('ix_exercises_slug'), 'exercises', ['slug'], unique=True)
    op.create_index(op.f('ix_exercises_is_active'), 'exercises', ['is_active'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_exercises_is_active'), table_name='exercises')
    op.drop_index(op.f('ix_exercises_slug'), table_name='exercises')
    op.drop_index(op.f('ix_exercises_name'), table_name='exercises')
    op.drop_index(op.f('ix_exercises_id'), table_name='exercises')
    op.drop_table('exercises')
