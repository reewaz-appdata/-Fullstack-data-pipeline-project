import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from pydantic import EmailStr
from sqlalchemy import CheckConstraint, Column, DateTime, Numeric, String
from sqlmodel import Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore[assignment]
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore[assignment]


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")
    cart_items: list["CartItem"] = Relationship(back_populates="item")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# ---------------------------------------------------------------------------
# Cart / Shopping-Cart models (proj2)
# ---------------------------------------------------------------------------

# Link table — many-to-many between CartItem and ShoppingCart
class CartItemShoppingCartLink(SQLModel, table=True):
    cart_item_id: uuid.UUID = Field(
        foreign_key="cartitem.id",
        primary_key=True,
    )
    shopping_cart_id: uuid.UUID = Field(
        foreign_key="shoppingcart.id",
        primary_key=True,
    )


# ── CartItem ─────────────────────────────────────────────────────────────────

class CartItemBase(SQLModel):
    quantity: int = Field(default=1, ge=1)
    unit_price: Decimal = Field(
        sa_column=Column(Numeric(10, 2), nullable=False)
    )
    description: str = Field(
        sa_column=Column(String(255), nullable=False)
    )
    item_id: uuid.UUID = Field(foreign_key="item.id")

    __table_args__ = (
        CheckConstraint("quantity >= 1", name="ck_cartitem_quantity_positive"),
    )


class CartItem(CartItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    item: Optional["Item"] = Relationship(back_populates="cart_items")

    shopping_carts: list["ShoppingCart"] = Relationship(
        back_populates="cart_items",
        link_model=CartItemShoppingCartLink,
    )


class CartItemCreate(CartItemBase):
    pass


class CartItemUpdate(SQLModel):
    quantity: Optional[int] = None
    unit_price: Optional[Decimal] = None
    description: Optional[str] = None
    item_id: Optional[uuid.UUID] = None


class CartItemPublic(CartItemBase):
    id: uuid.UUID


class CartItemsPublic(SQLModel):
    data: list[CartItemPublic]
    count: int


# ── ShoppingCart ──────────────────────────────────────────────────────────────

class ShoppingCartBase(SQLModel):
    session_key: str = Field(
        sa_column=Column(String(255), nullable=False, unique=True)
    )
    active: bool = Field(default=True)
    expires: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    total: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False),
    )


class ShoppingCart(ShoppingCartBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid1, primary_key=True)

    cart_items: list[CartItem] = Relationship(
        back_populates="shopping_carts",
        link_model=CartItemShoppingCartLink,
    )


class ShoppingCartCreate(ShoppingCartBase):
    pass


class ShoppingCartUpdate(SQLModel):
    session_key: Optional[str] = None
    active: Optional[bool] = None
    expires: Optional[datetime] = None
    total: Optional[Decimal] = None


class ShoppingCartPublic(ShoppingCartBase):
    id: uuid.UUID


class ShoppingCartsPublic(SQLModel):
    data: list[ShoppingCartPublic]
    count: int
