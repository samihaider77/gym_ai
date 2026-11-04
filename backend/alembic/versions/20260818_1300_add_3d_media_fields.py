"""add rendered 3d exercise media metadata"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "3dmedia1300"
down_revision: Union[str, None] = "9a2b3c4d5e6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("exercise_media", sa.Column("poster_url", sa.String(1000), nullable=True))
    op.add_column("exercise_media", sa.Column("duration_ms", sa.Integer(), nullable=True))
    op.add_column("exercise_media", sa.Column("camera_angle", sa.String(30), nullable=True))
    op.add_column("exercise_media", sa.Column("format", sa.String(20), nullable=True))
    op.add_column("exercise_media", sa.Column("version", sa.Integer(), server_default="1", nullable=False))
    op.add_column("exercise_media", sa.Column("status", sa.String(30), server_default="review_required", nullable=False))

def downgrade() -> None:
    for column in ("status", "version", "format", "camera_angle", "duration_ms", "poster_url"):
        op.drop_column("exercise_media", column, table_name="exercise_media")
