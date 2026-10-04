"""urgency request and deferral fixes

Aligns deferral.new_date (nullable=True) and deferral.reason (nullable=False)
with docs/schema_design.md, and creates the urgency_request table.

Revision ID: b2c3d4e5f6a7
Revises: 540800975713
Create Date: 2026-10-03 23:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = '540800975713'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def upgrade() -> None:
    # 1. Align deferral nullabilities
    if _has_table('deferral'):
        # Allow new_date to be NULL until rescheduled
        op.alter_column('deferral', 'new_date', existing_type=sa.Date(), nullable=True)

        # Ensure reason has no NULL values before making it NOT NULL
        op.execute(sa.text("UPDATE deferral SET reason = 'unspecified' WHERE reason IS NULL"))
        op.alter_column('deferral', 'reason', existing_type=sa.String(), nullable=False)

    # 2. Create urgency_request table
    if not _has_table('urgency_request'):
        op.create_table(
            'urgency_request',
            sa.Column('urgency_request_id', sa.String(), primary_key=True),
            sa.Column('order_id', sa.String(), sa.ForeignKey('order.order_id'), nullable=False, unique=True),
            sa.Column('outlet_id', sa.String(), sa.ForeignKey('outlet.outlet_id'), nullable=False),
            sa.Column('reported_by', sa.String(), sa.ForeignKey('user.user_id'), nullable=False),
            sa.Column('reason_code', sa.String(), nullable=False),
            sa.Column('reason_text', sa.String(), nullable=False),
            sa.Column('status', sa.String(), nullable=False, server_default='pending'),
            sa.Column('reviewed_by', sa.String(), sa.ForeignKey('user.user_id'), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('decision_note', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('client_op_id', sa.String(), nullable=True, unique=True),
            sa.CheckConstraint(
                "reason_code IN ('stockout_risk', 'store_operation_impact', 'chilled_shortage', 'time_bound_event', 'recovery_after_failed_delivery', 'other')",
                name='check_urgency_reason_code',
            ),
            sa.CheckConstraint(
                "status IN ('pending', 'approved', 'rejected', 'resolved')",
                name='check_urgency_status',
            ),
        )


def downgrade() -> None:
    if _has_table('urgency_request'):
        op.drop_table('urgency_request')

    if _has_table('deferral'):
        op.alter_column('deferral', 'reason', existing_type=sa.String(), nullable=True)
        # Backfill existing NULL new_date values before restoring NOT NULL constraint
        op.execute(sa.text("UPDATE deferral SET new_date = original_date WHERE new_date IS NULL"))
        op.alter_column('deferral', 'new_date', existing_type=sa.Date(), nullable=False)
