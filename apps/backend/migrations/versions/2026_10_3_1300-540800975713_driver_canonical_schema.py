"""driver canonical schema

Aligns trip / trip_stop / trip_stop_item / driver_events / conflict / proof_of_delivery
with docs/schema_design.md, adds return_custody, and adds the road_geometry table that
was previously only created by Base.metadata.create_all().

Revision ID: 540800975713
Revises: 354f44f89c24
Create Date: 2026-10-03 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '540800975713'
down_revision: Union[str, None] = '354f44f89c24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def _row_count(table: str) -> int:
    return op.get_bind().execute(sa.text(f'SELECT COUNT(*) FROM "{table}"')).scalar()


def _require_empty(table: str) -> None:
    """The old driver_event / conflict shapes cannot be mapped onto the new ones
    (no driver_id, no stop_id). Nothing in the codebase could write them successfully,
    so they should be empty — refuse to drop them if they are not."""
    if _has_table(table) and _row_count(table) > 0:
        raise RuntimeError(
            f"Table '{table}' contains rows; migrate or archive them manually before running this migration."
        )


def _create_driver_events() -> None:
    op.create_table(
        'driver_events',
        sa.Column('event_id', sa.String(), nullable=False),
        sa.Column('driver_id', sa.String(), nullable=False),
        sa.Column('device_id', sa.String(), nullable=True),
        sa.Column('client_event_id', sa.String(), nullable=False),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('stop_id', sa.String(), nullable=True),
        sa.Column('trip_id', sa.String(), nullable=True),
        sa.Column('payload', sa.String(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('row_version_before', sa.Integer(), nullable=True),
        sa.Column('row_version_after', sa.Integer(), nullable=True),
        sa.Column('error', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['driver_id'], ['user.user_id']),
        sa.ForeignKeyConstraint(['stop_id'], ['trip_stop.stop_id']),
        sa.ForeignKeyConstraint(['trip_id'], ['trip.trip_id']),
        sa.PrimaryKeyConstraint('event_id'),
        sa.UniqueConstraint('client_event_id'),
    )
    op.create_index(op.f('ix_driver_events_driver_id'), 'driver_events', ['driver_id'], unique=False)
    op.create_index(op.f('ix_driver_events_trip_id'), 'driver_events', ['trip_id'], unique=False)


def _create_conflict() -> None:
    op.create_table(
        'conflict',
        sa.Column('conflict_id', sa.String(), nullable=False),
        sa.Column('stop_id', sa.String(), nullable=True),
        sa.Column('driver_event_id', sa.String(), nullable=True),
        sa.Column('driver_json', sa.String(), nullable=True),
        sa.Column('system_json', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('forwarded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.String(), nullable=True),
        sa.Column('resolved_by_role', sa.String(), nullable=True),
        sa.Column('resolution', sa.String(), nullable=True),
        sa.Column('resolution_note', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['driver_event_id'], ['driver_events.event_id']),
        sa.ForeignKeyConstraint(['resolved_by'], ['user.user_id']),
        sa.ForeignKeyConstraint(['stop_id'], ['trip_stop.stop_id']),
        sa.PrimaryKeyConstraint('conflict_id'),
    )


def _create_return_custody() -> None:
    op.create_table(
        'return_custody',
        sa.Column('return_id', sa.String(), nullable=False),
        sa.Column('trip_id', sa.String(), nullable=False),
        sa.Column('stop_id', sa.String(), nullable=False),
        sa.Column('driver_id', sa.String(), nullable=False),
        sa.Column('items', sa.String(), nullable=False),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('return_crate', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_event_id', sa.String(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('confirmed_event_id', sa.String(), nullable=True),
        sa.Column('officer_name', sa.String(), nullable=True),
        sa.Column('condition', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['confirmed_event_id'], ['driver_events.event_id']),
        sa.ForeignKeyConstraint(['created_event_id'], ['driver_events.event_id']),
        sa.ForeignKeyConstraint(['driver_id'], ['user.user_id']),
        sa.ForeignKeyConstraint(['stop_id'], ['trip_stop.stop_id']),
        sa.ForeignKeyConstraint(['trip_id'], ['trip.trip_id']),
        sa.PrimaryKeyConstraint('return_id'),
    )
    op.create_index(op.f('ix_return_custody_trip_id'), 'return_custody', ['trip_id'], unique=False)


def upgrade() -> None:
    # ── road_geometry (driver map cache; previously create_all-only) ─────────
    if not _has_table('road_geometry'):
        op.create_table(
            'road_geometry',
            sa.Column('from_id', sa.String(), nullable=False),
            sa.Column('to_id', sa.String(), nullable=False),
            sa.Column('coord_version', sa.Integer(), nullable=False),
            sa.Column('coords', sa.String(), nullable=False),
            sa.Column('distance_meters', sa.Float(), nullable=True),
            sa.Column('duration_seconds', sa.Float(), nullable=True),
            sa.Column('created_at', sa.String(), nullable=True),
            sa.PrimaryKeyConstraint('from_id', 'to_id', 'coord_version'),
        )

    # ── trip ─────────────────────────────────────────────────────────────────
    op.add_column('trip', sa.Column('driver_id', sa.String(), nullable=True))
    op.add_column('trip', sa.Column('brand', sa.String(), nullable=True))
    op.add_column('trip', sa.Column('district', sa.String(), nullable=True))
    op.add_column('trip', sa.Column('plan_depart', sa.String(), nullable=True))
    op.add_column('trip', sa.Column('plan_return', sa.String(), nullable=True))
    op.add_column('trip', sa.Column('dist_km', sa.Numeric(), nullable=True))
    op.add_column('trip', sa.Column('est_fuel_l', sa.Numeric(), nullable=True))
    op.add_column('trip', sa.Column('actual_depart', sa.DateTime(timezone=True), nullable=True))
    op.add_column('trip', sa.Column('actual_return', sa.DateTime(timezone=True), nullable=True))
    op.add_column('trip', sa.Column('actual_dist_km', sa.Numeric(), nullable=True))
    op.add_column('trip', sa.Column('actual_fuel_l', sa.Numeric(), nullable=True))
    op.create_index(op.f('ix_trip_driver_id'), 'trip', ['driver_id'], unique=False)
    op.create_foreign_key('fk_trip_driver_id', 'trip', 'user', ['driver_id'], ['user_id'])
    # Backfill brand from the trip's orders where they agree on one brand.
    op.execute(
        """
        UPDATE trip SET brand = sub.brand
        FROM (
            SELECT trip_id, MIN(brand) AS brand FROM "order"
            WHERE trip_id IS NOT NULL GROUP BY trip_id HAVING COUNT(DISTINCT brand) = 1
        ) AS sub
        WHERE trip.trip_id = sub.trip_id
        """
    )

    # ── trip_stop ────────────────────────────────────────────────────────────
    op.add_column('trip_stop', sa.Column('arrived_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('trip_stop', sa.Column('arrival_lat', sa.Numeric(), nullable=True))
    op.add_column('trip_stop', sa.Column('arrival_lng', sa.Numeric(), nullable=True))
    op.add_column('trip_stop', sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('trip_stop', sa.Column('skip_reason', sa.String(), nullable=True))
    op.alter_column('trip_stop', 'wt_kg', existing_type=sa.INTEGER(), type_=sa.Numeric(), existing_nullable=True)
    op.alter_column('trip_stop', 'vol_m3', existing_type=sa.INTEGER(), type_=sa.Numeric(), existing_nullable=True)
    op.alter_column('trip_stop', 'temp_req', existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column(
        'trip_stop', 'forced_reefer',
        existing_type=sa.VARCHAR(),
        type_=sa.Boolean(),
        nullable=False,
        server_default=sa.false(),
        postgresql_using="COALESCE(LOWER(forced_reefer) IN ('true', 't', '1', 'yes'), FALSE)",
    )

    # ── trip_stop_item ───────────────────────────────────────────────────────
    op.alter_column('trip_stop_item', 'stop_item_id', new_column_name='item_id', existing_type=sa.VARCHAR())
    op.add_column('trip_stop_item', sa.Column('qty_assigned', sa.Numeric(), nullable=True))
    op.add_column('trip_stop_item', sa.Column('qty_loaded', sa.Numeric(), nullable=True))
    op.add_column('trip_stop_item', sa.Column('qty_delivered', sa.Numeric(), nullable=True))
    op.add_column('trip_stop_item', sa.Column('qty_returned', sa.Numeric(), nullable=True))
    op.add_column('trip_stop_item', sa.Column('unit', sa.String(), nullable=True))
    op.add_column('trip_stop_item', sa.Column('sku', sa.String(), nullable=True))
    op.add_column('trip_stop_item', sa.Column('handling_note', sa.String(), nullable=True))
    op.execute(
        """
        UPDATE trip_stop_item SET
            qty_assigned = ol.quantity,
            unit = COALESCE(p.unit, 'unit'),
            sku = ol.product_id
        FROM order_line ol LEFT JOIN product p ON p.product_id = ol.product_id
        WHERE ol.line_item_id = trip_stop_item.line_item_id
        """
    )
    op.alter_column('trip_stop_item', 'qty_assigned', existing_type=sa.Numeric(), nullable=False)
    op.alter_column('trip_stop_item', 'unit', existing_type=sa.String(), nullable=False)

    # ── driver_event → driver_events, conflict reshaped ─────────────────────
    _require_empty('conflict')
    _require_empty('driver_event')
    op.drop_table('conflict')
    op.drop_table('driver_event')
    if not _has_table('driver_events'):
        _create_driver_events()
    _create_conflict()

    # ── return_custody ───────────────────────────────────────────────────────
    if not _has_table('return_custody'):
        _create_return_custody()

    # ── proof_of_delivery ────────────────────────────────────────────────────
    op.execute("UPDATE proof_of_delivery SET otp_code = 'LEGACY' WHERE otp_code IS NULL")
    op.execute("UPDATE proof_of_delivery SET otp_verified = FALSE WHERE otp_verified IS NULL")
    op.execute("UPDATE proof_of_delivery SET recorded_offline = FALSE WHERE recorded_offline IS NULL")
    op.alter_column('proof_of_delivery', 'otp_code', existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column('proof_of_delivery', 'otp_verified', existing_type=sa.BOOLEAN(), nullable=False, server_default=sa.false())
    op.alter_column('proof_of_delivery', 'recorded_offline', existing_type=sa.BOOLEAN(), nullable=False, server_default=sa.false())


def downgrade() -> None:
    op.alter_column('proof_of_delivery', 'recorded_offline', existing_type=sa.BOOLEAN(), nullable=True, server_default=None)
    op.alter_column('proof_of_delivery', 'otp_verified', existing_type=sa.BOOLEAN(), nullable=True, server_default=None)
    op.alter_column('proof_of_delivery', 'otp_code', existing_type=sa.VARCHAR(), nullable=True)

    op.drop_index(op.f('ix_return_custody_trip_id'), table_name='return_custody')
    op.drop_table('return_custody')

    op.drop_table('conflict')
    op.drop_index(op.f('ix_driver_events_trip_id'), table_name='driver_events')
    op.drop_index(op.f('ix_driver_events_driver_id'), table_name='driver_events')
    op.drop_table('driver_events')
    op.create_table(
        'driver_event',
        sa.Column('event_id', sa.VARCHAR(), nullable=False),
        sa.Column('client_event_id', sa.VARCHAR(), nullable=False),
        sa.Column('trip_id', sa.VARCHAR(), nullable=False),
        sa.Column('stop_id', sa.VARCHAR(), nullable=True),
        sa.Column('type', sa.VARCHAR(), nullable=False),
        sa.Column('occurred_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('received_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('payload', sa.VARCHAR(), nullable=False),
        sa.Column('sync_status', sa.VARCHAR(), nullable=False),
        sa.Column('sync_error', sa.VARCHAR(), nullable=True),
        sa.ForeignKeyConstraint(['stop_id'], ['trip_stop.stop_id']),
        sa.ForeignKeyConstraint(['trip_id'], ['trip.trip_id']),
        sa.PrimaryKeyConstraint('event_id'),
        sa.UniqueConstraint('client_event_id'),
    )
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

    op.drop_column('trip_stop_item', 'handling_note')
    op.drop_column('trip_stop_item', 'sku')
    op.drop_column('trip_stop_item', 'unit')
    op.drop_column('trip_stop_item', 'qty_returned')
    op.drop_column('trip_stop_item', 'qty_delivered')
    op.drop_column('trip_stop_item', 'qty_loaded')
    op.drop_column('trip_stop_item', 'qty_assigned')
    op.alter_column('trip_stop_item', 'item_id', new_column_name='stop_item_id', existing_type=sa.VARCHAR())

    op.alter_column(
        'trip_stop', 'forced_reefer',
        existing_type=sa.Boolean(),
        type_=sa.VARCHAR(),
        nullable=True,
        server_default=None,
        postgresql_using="CASE WHEN forced_reefer THEN 'true' ELSE NULL END",
    )
    op.execute("UPDATE trip_stop SET temp_req = 'ambient' WHERE temp_req IS NULL")
    op.alter_column('trip_stop', 'temp_req', existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column('trip_stop', 'vol_m3', existing_type=sa.Numeric(), type_=sa.INTEGER(), existing_nullable=True)
    op.alter_column('trip_stop', 'wt_kg', existing_type=sa.Numeric(), type_=sa.INTEGER(), existing_nullable=True)
    op.drop_column('trip_stop', 'skip_reason')
    op.drop_column('trip_stop', 'completed_at')
    op.drop_column('trip_stop', 'arrival_lng')
    op.drop_column('trip_stop', 'arrival_lat')
    op.drop_column('trip_stop', 'arrived_at')

    op.drop_constraint('fk_trip_driver_id', 'trip', type_='foreignkey')
    op.drop_index(op.f('ix_trip_driver_id'), table_name='trip')
    for col in ('actual_fuel_l', 'actual_dist_km', 'actual_return', 'actual_depart', 'est_fuel_l',
                'dist_km', 'plan_return', 'plan_depart', 'district', 'brand', 'driver_id'):
        op.drop_column('trip', col)
    # road_geometry is left in place: it may predate this migration (create_all).
