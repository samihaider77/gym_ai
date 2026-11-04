"""add exercise equipment and muscle relationships

Revision ID: 8f1a2b3c4d5e
Revises: cb51aea10fd4
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "8f1a2b3c4d5e"
down_revision: Union[str, None] = "cb51aea10fd4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_foreign_key("fk_exercises_equipment_id", "exercises", "equipment", ["equipment_id"], ["id"], ondelete="SET NULL")
    op.create_table(
        "exercise_muscles",
        sa.Column("exercise_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("muscle_group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["muscle_group_id"], ["muscle_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("exercise_id", "muscle_group_id"),
        sa.CheckConstraint("role IN ('primary', 'secondary')", name="ck_exercise_muscle_role"),
    )

def downgrade() -> None:
    op.drop_table("exercise_muscles")
    op.drop_constraint("fk_exercises_equipment_id", "exercises", type_="foreignkey")
