"""Phase 2 Full Schema - trips, deferrals, events, load checks, delivery, incidents, draft plan

Revision ID: a1b2c3d4e5f6
Revises: cffd139ab054
Create Date: 2026-10-02 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'cffd139ab054'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # trip
    op.create_table(
        'trip',
        sa.Column('trip_id', sa.String(), nullable=False),
        sa.Column('depot_id', sa.String(), nullable=False),
        sa.Column('vehicle_id', sa.String(), nullable=False),
        sa.Column('dispatcher_id', sa.String(), nullable=False),
        sa.Column('trip_date', sa.Date(), nullable=False),
        sa.Column('trip_no', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['depot_id'], ['depot.depot_id']),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicle.vehicle_id']),
        sa.ForeignKeyConstraint(['dispatcher_id'], ['user.user_id']),
        sa.PrimaryKeyConstraint('trip_id'),
        sa.UniqueConstraint('vehicle_id', 'trip_date', 'trip_no', name='uix_trip_vehicle_date_no'),
    )

    # trip_stop
    op.create_table(
        'trip_stop',
        sa.Column('stop_id', sa.String(), nullable=False),
        sa.Column('trip_id', sa.String(), nullable=False),
        sa.Column('outlet_id', sa.String(), nullable=False),
        sa.Column('order_id', sa.String(), nullable=False),
        sa.Column('stop_seq', sa.Integer(), nullable=False),
        sa.Column('pack_seq', sa.Integer(), nullable=True),
        sa.Column('eta', sa.String(), nullable=True),
        sa.Column('wt_kg', sa.Integer(), nullable=True),
        sa.Column('vol_m3', sa.Integer(), nullable=True),
        sa.Column('temp_req', sa.String(), nullable=False),
        sa.Column('forced_reefer', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('row_version', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['trip_id'], ['trip.trip_id']),
        sa.ForeignKeyConstraint(['outlet_id'], ['outlet.outlet_id']),
        sa.ForeignKeyConstraint(['order_id'], ['order.order_id']),
        sa.PrimaryKeyConstraint('stop_id'),
        sa.UniqueConstraint('order_id'),
    )

    # trip_stop_item
    op.create_table(
        'trip_stop_item',
        sa.Column('stop_item_id', sa.String(), nullable=False),
        sa.Column('stop_id', sa.String(), nullable=False),
        sa.Column('line_item_id', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['stop_id'], ['trip_stop.stop_id']),
        sa.ForeignKeyConstraint(['line_item_id'], ['order_line.line_item_id']),
        sa.PrimaryKeyConstraint('stop_item_id'),
    )

    # deferral
    op.create_table(
        'deferral',
        sa.Column('deferral_id', sa.String(), nullable=False),
        sa.Column('order_id', sa.String(), nullable=False),
        sa.Column('outlet_id', sa.String(), nullable=False),
        sa.Column('original_date', sa.Date(), nullable=False),
        sa.Column('new_date', sa.Date(), nullable=False),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('trip_id', sa.String(), nullable=True),
        sa.Column('client_op_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['order.order_id']),
        sa.ForeignKeyConstraint(['outlet_id'], ['outlet.outlet_id']),
        sa.ForeignKeyConstraint(['created_by'], ['user.user_id']),
        sa.ForeignKeyConstraint(['trip_id'], ['trip.trip_id']),
        sa.PrimaryKeyConstraint('deferral_id'),
        sa.UniqueConstraint('client_op_id'),
    )

    # delivery_event
    op.create_table(
        'delivery_event',
        sa.Column('event_id', sa.String(), nullable=False),
        sa.Column('order_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('actor_role', sa.String(), nullable=False),
        sa.Column('actor_id', sa.String(), nullable=False),
        sa.Column('note', sa.String(), nullable=True),
        sa.Column('offline', sa.Boolean(), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('client_op_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['order.order_id']),
        sa.ForeignKeyConstraint(['actor_id'], ['user.user_id']),
        sa.PrimaryKeyConstraint('event_id'),
        sa.UniqueConstraint('client_op_id'),
    )

    # driver_event
    op.create_table(
        'driver_event',
        sa.Column('event_id', sa.String(), nullable=False),
        sa.Column('client_event_id', sa.String(), nullable=False),
        sa.Column('trip_id', sa.String(), nullable=False),
        sa.Column('stop_id', sa.String(), nullable=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('payload', sa.String(), nullable=False),
        sa.Column('sync_status', sa.String(), nullable=False),
        sa.Column('sync_error', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['trip_id'], ['trip.trip_id']),
        sa.ForeignKeyConstraint(['stop_id'], ['trip_stop.stop_id']),
        sa.PrimaryKeyConstraint('event_id'),
        sa.UniqueConstraint('client_event_id'),
    )

    # conflict
    op.create_table(
        'conflict',
        sa.Column('conflict_id', sa.String(), nullable=False),
        sa.Column('driver_event_id', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=False),
        sa.Column('conflict_type', sa.String(), nullable=False),
        sa.Column('server_state', sa.String(), nullable=False),
        sa.Column('client_state', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['driver_event_id'], ['driver_event.event_id']),
        sa.ForeignKeyConstraint(['resolved_by'], ['user.user_id']),
        sa.PrimaryKeyConstraint('conflict_id'),
    )

    # load_check
    op.create_table(
        'load_check',
        sa.Column('check_id', sa.String(), nullable=False),
        sa.Column('trip_id', sa.String(), nullable=False),
        sa.Column('checked_by', sa.String(), nullable=False),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('note', sa.String(), nullable=True),
        sa.Column('client_op_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['trip_id'], ['trip.trip_id']),
        sa.ForeignKeyConstraint(['checked_by'], ['user.user_id']),
        sa.PrimaryKeyConstraint('check_id'),
        sa.UniqueConstraint('trip_id'),
        sa.UniqueConstraint('client_op_id'),
    )

    # load_check_item
    op.create_table(
        'load_check_item',
        sa.Column('chk_item_id', sa.String(), nullable=False),
        sa.Column('check_id', sa.String(), nullable=False),
        sa.Column('line_item_id', sa.String(), nullable=False),
        sa.Column('exp_qty', sa.Integer(), nullable=False),
        sa.Column('loaded_qty', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('note', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['check_id'], ['load_check.check_id']),
        sa.ForeignKeyConstraint(['line_item_id'], ['order_line.line_item_id']),
        sa.PrimaryKeyConstraint('chk_item_id'),
    )

    # proof_of_delivery
    op.create_table(
        'proof_of_delivery',
        sa.Column('pod_id', sa.String(), nullable=False),
        sa.Column('order_id', sa.String(), nullable=False),
        sa.Column('stop_id', sa.String(), nullable=False),
        sa.Column('delivered_by', sa.String(), nullable=False),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('otp_code', sa.String(), nullable=True),
        sa.Column('otp_verified', sa.Boolean(), nullable=True),
        sa.Column('signature_url', sa.String(), nullable=True),
        sa.Column('photo_url', sa.String(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('recorded_offline', sa.Boolean(), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('client_op_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['order.order_id']),
        sa.ForeignKeyConstraint(['stop_id'], ['trip_stop.stop_id']),
        sa.ForeignKeyConstraint(['delivered_by'], ['user.user_id']),
        sa.PrimaryKeyConstraint('pod_id'),
        sa.UniqueConstraint('order_id'),
        sa.UniqueConstraint('client_op_id'),
    )

    # receipt_confirmation
    op.create_table(
        'receipt_confirmation',
        sa.Column('confirm_id', sa.String(), nullable=False),
        sa.Column('order_id', sa.String(), nullable=False),
        sa.Column('pod_id', sa.String(), nullable=False),
        sa.Column('confirmed_by', sa.String(), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('items_ok', sa.Boolean(), nullable=False),
        sa.Column('client_op_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['order.order_id']),
        sa.ForeignKeyConstraint(['pod_id'], ['proof_of_delivery.pod_id']),
        sa.ForeignKeyConstraint(['confirmed_by'], ['user.user_id']),
        sa.PrimaryKeyConstraint('confirm_id'),
        sa.UniqueConstraint('order_id'),
        sa.UniqueConstraint('client_op_id'),
    )

    # discrepancy
    op.create_table(
        'discrepancy',
        sa.Column('discrepancy_id', sa.String(), nullable=False),
        sa.Column('order_id', sa.String(), nullable=False),
        sa.Column('raised_by', sa.String(), nullable=False),
        sa.Column('source_stage', sa.String(), nullable=False),
        sa.Column('chk_item_id', sa.String(), nullable=True),
        sa.Column('confirm_id', sa.String(), nullable=True),
        sa.Column('product_id', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('reported_qty', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('note', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['order.order_id']),
        sa.ForeignKeyConstraint(['raised_by'], ['user.user_id']),
        sa.ForeignKeyConstraint(['chk_item_id'], ['load_check_item.chk_item_id']),
        sa.ForeignKeyConstraint(['confirm_id'], ['receipt_confirmation.confirm_id']),
        sa.ForeignKeyConstraint(['product_id'], ['product.product_id']),
        sa.PrimaryKeyConstraint('discrepancy_id'),
    )

    # vehicle_incident
    op.create_table(
        'vehicle_incident',
        sa.Column('incident_id', sa.String(), nullable=False),
        sa.Column('vehicle_id', sa.String(), nullable=False),
        sa.Column('trip_id', sa.String(), nullable=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('detail', sa.String(), nullable=False),
        sa.Column('reported_by', sa.String(), nullable=False),
        sa.Column('reported_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicle.vehicle_id']),
        sa.ForeignKeyConstraint(['trip_id'], ['trip.trip_id']),
        sa.ForeignKeyConstraint(['reported_by'], ['user.user_id']),
        sa.PrimaryKeyConstraint('incident_id'),
    )

    # route_change
    op.create_table(
        'route_change',
        sa.Column('change_id', sa.String(), nullable=False),
        sa.Column('trip_id', sa.String(), nullable=False),
        sa.Column('change_type', sa.String(), nullable=False),
        sa.Column('payload', sa.String(), nullable=False),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('issued_by', sa.String(), nullable=False),
        sa.Column('acknowledged', sa.Boolean(), nullable=True),
        sa.Column('ack_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['trip_id'], ['trip.trip_id']),
        sa.ForeignKeyConstraint(['issued_by'], ['user.user_id']),
        sa.PrimaryKeyConstraint('change_id'),
    )

    # draft_plan
    op.create_table(
        'draft_plan',
        sa.Column('plan_id', sa.String(), nullable=False),
        sa.Column('depot_id', sa.String(), nullable=True),
        sa.Column('target_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('algorithm', sa.String(), nullable=True),
        sa.Column('plan_data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('approved_by', sa.String(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('plan_id'),
    )


def downgrade() -> None:
    op.drop_table('draft_plan')
    op.drop_table('route_change')
    op.drop_table('vehicle_incident')
    op.drop_table('discrepancy')
    op.drop_table('receipt_confirmation')
    op.drop_table('proof_of_delivery')
    op.drop_table('load_check_item')
    op.drop_table('load_check')
    op.drop_table('conflict')
    op.drop_table('driver_event')
    op.drop_table('delivery_event')
    op.drop_table('deferral')
    op.drop_table('trip_stop_item')
    op.drop_table('trip_stop')
    op.drop_table('trip')
