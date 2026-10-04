"""Builds the canonical per-stop manifest (trip_stop_item rows) from order lines.

Every path that creates a TripStop (plan confirmation, optimizer approval, breakdown
recovery) should call `add_stop_items` so Loader and Driver see the same manifest.
"""

import uuid
from typing import Iterable, List, Optional

from sqlalchemy.orm import Session

from app.models.order import OrderLine
from app.models.product import Product
from app.models.trip import TripStopItem


def add_stop_items(
    db: Session,
    stop_id: str,
    order_id: str,
    line_item_ids: Optional[Iterable[str]] = None,
) -> List[TripStopItem]:
    """Create one TripStopItem per order line (or per listed line) not yet on the stop."""
    query = (
        db.query(OrderLine, Product)
        .outerjoin(Product, Product.product_id == OrderLine.product_id)
        .filter(OrderLine.order_id == order_id)
    )
    wanted = set(line_item_ids) if line_item_ids else None
    existing = {
        line_id
        for (line_id,) in db.query(TripStopItem.line_item_id).filter(TripStopItem.stop_id == stop_id)
    }

    created = []
    for line, product in query.order_by(OrderLine.line_item_id):
        if wanted is not None and line.line_item_id not in wanted:
            continue
        if line.line_item_id in existing:
            continue
        item = TripStopItem(
            item_id=f"STI-{uuid.uuid4().hex[:10].upper()}",
            stop_id=stop_id,
            line_item_id=line.line_item_id,
            qty_assigned=line.quantity,
            unit=(product.unit if product else None) or "unit",
            sku=line.product_id,
        )
        db.add(item)
        created.append(item)
    return created


def delete_stop_items(db: Session, stop_id: str) -> None:
    db.query(TripStopItem).filter(TripStopItem.stop_id == stop_id).delete(synchronize_session=False)
