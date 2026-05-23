"""
proj2 seed script — populates CartItem, ShoppingCart, and the link table.

run from the backend/ directory:
    python proj2/seed_proj2.py
"""

import sys
import os

# allow imports from the backend/app package when running this script directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# load .env from the project root so DB credentials are available
_env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip())

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from sqlmodel import Session, select

from app.core.db import engine
from app.models import CartItem, Item, ShoppingCart, User


def seed_data() -> None:
    with Session(engine) as session:
        try:
            # get one existing user so Item.owner_id can be set
            user = session.exec(select(User)).first()
            if not user:
                raise ValueError("no user found in database. create a user first.")

            # ------------------------------------------------------------------
            # 1. create two Item rows — CartItem depends on existing items
            # ------------------------------------------------------------------
            item1 = Item(
                title="wireless mouse",
                description="bluetooth mouse",
                owner_id=user.id,
            )
            item2 = Item(
                title="usb keyboard",
                description="mechanical keyboard",
                owner_id=user.id,
            )

            session.add(item1)
            session.add(item2)
            session.commit()
            session.refresh(item1)
            session.refresh(item2)

            # ------------------------------------------------------------------
            # 2. create two CartItem rows — two objects for each class
            # ------------------------------------------------------------------
            cart_item1 = CartItem(
                item_id=item1.id,
                quantity=2,
                unit_price=Decimal("25.00"),
                description="two wireless mice",
            )
            cart_item2 = CartItem(
                item_id=item2.id,
                quantity=1,
                unit_price=Decimal("80.00"),
                description="one mechanical keyboard",
            )

            session.add(cart_item1)
            session.add(cart_item2)
            session.commit()
            session.refresh(cart_item1)
            session.refresh(cart_item2)

            # ------------------------------------------------------------------
            # 3. create two ShoppingCart rows — two objects for each class
            # ------------------------------------------------------------------
            # uuid4() session keys prevent duplicate-key errors on reruns
            cart1 = ShoppingCart(
                session_key=f"session_{uuid4()}",
                active=True,
                expires=datetime.now(timezone.utc) + timedelta(days=7),
                total=Decimal("130.00"),
            )
            cart2 = ShoppingCart(
                session_key=f"session_{uuid4()}",
                active=True,
                expires=datetime.now(timezone.utc) + timedelta(days=3),
                total=Decimal("25.00"),
            )

            # appending through the relationship creates rows in the link table
            # (many-to-many: one cart item can belong to many shopping carts)
            cart1.cart_items.append(cart_item1)
            cart1.cart_items.append(cart_item2)
            cart2.cart_items.append(cart_item1)

            session.add(cart1)
            session.add(cart2)
            session.commit()

            print("seed complete.")
            print(f"items:         {item1.id}, {item2.id}")
            print(f"cartitems:     {cart_item1.id}, {cart_item2.id}")
            print(f"shoppingcarts: {cart1.id}, {cart2.id}")

        except Exception as e:
            session.rollback()
            print("seed failed:", e)
            raise


if __name__ == "__main__":
    seed_data()
