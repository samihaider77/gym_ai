"""add Roman Urdu exercise name and instructions"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "romanurdu1000"
down_revision: Union[str, None] = "3dmedia1300"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("exercises", sa.Column("name_ur", sa.String(200), nullable=True))
    op.add_column("exercises", sa.Column("instructions_ur", sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column("exercises", "instructions_ur")
    op.drop_column("exercises", "name_ur")
