"""create_muscle_groups_table

Revision ID: 29d9cc19748a
Revises: 3807b613a7d6
Create Date: 2026-07-30 11:35:03.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '29d9cc19748a'
down_revision: Union[str, None] = '3807b613a7d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'muscle_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('body_region', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_muscle_groups_id'), 'muscle_groups', ['id'], unique=False)
    op.create_index(op.f('ix_muscle_groups_name'), 'muscle_groups', ['name'], unique=True)
    op.create_index(op.f('ix_muscle_groups_slug'), 'muscle_groups', ['slug'], unique=True)
    op.create_index(op.f('ix_muscle_groups_is_active'), 'muscle_groups', ['is_active'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_muscle_groups_is_active'), table_name='muscle_groups')
    op.drop_index(op.f('ix_muscle_groups_slug'), table_name='muscle_groups')
    op.drop_index(op.f('ix_muscle_groups_name'), table_name='muscle_groups')
    op.drop_index(op.f('ix_muscle_groups_id'), table_name='muscle_groups')
    op.drop_table('muscle_groups')
