"""add chat_links, chat_link_codes and chat_messages for the WhatsApp Coach"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "chatlinks1200"
down_revision: Union[str, None] = "meallogs2100"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chat_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("address_hash", sa.String(64), nullable=False),
        sa.Column("address_last4", sa.String(4), nullable=False),
        sa.Column("language", sa.String(2), nullable=False),
        sa.Column("utc_offset_minutes", sa.Integer(), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("channel", "address_hash", name="uq_chat_link_address"),
    )
    op.create_index("ix_chat_links_user_id", "chat_links", ["user_id"])

    op.create_table(
        "chat_link_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("language", sa.String(2), nullable=False),
        sa.Column("utc_offset_minutes", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chat_link_codes_user_id", "chat_link_codes", ["user_id"])

    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("message_id", sa.String(128), nullable=False),
        sa.Column("address_hash", sa.String(64), nullable=False),
        sa.Column("link_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chat_links.id", ondelete="SET NULL"), nullable=True),
        sa.Column("intent", sa.String(20), nullable=False),
        sa.Column("ok", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("channel", "message_id", name="uq_chat_message_id"),
    )
    op.create_index("ix_chat_messages_address_hash", "chat_messages", ["address_hash"])
    op.create_index("ix_chat_messages_created_at", "chat_messages", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_chat_messages_created_at", table_name="chat_messages")
    op.drop_index("ix_chat_messages_address_hash", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index("ix_chat_link_codes_user_id", table_name="chat_link_codes")
    op.drop_table("chat_link_codes")
    op.drop_index("ix_chat_links_user_id", table_name="chat_links")
    op.drop_table("chat_links")
