"""create_equipment_table

Revision ID: 443f2160ae86
Revises: 29d9cc19748a
Create Date: 2026-07-30 11:40:19.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '443f2160ae86'
down_revision: Union[str, None] = '29d9cc19748a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'equipment',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_equipment_id'), 'equipment', ['id'], unique=False)
    op.create_index(op.f('ix_equipment_name'), 'equipment', ['name'], unique=True)
    op.create_index(op.f('ix_equipment_slug'), 'equipment', ['slug'], unique=True)
    op.create_index(op.f('ix_equipment_is_active'), 'equipment', ['is_active'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_equipment_is_active'), table_name='equipment')
    op.drop_index(op.f('ix_equipment_slug'), table_name='equipment')
    op.drop_index(op.f('ix_equipment_name'), table_name='equipment')
    op.drop_index(op.f('ix_equipment_id'), table_name='equipment')
    op.drop_table('equipment')
