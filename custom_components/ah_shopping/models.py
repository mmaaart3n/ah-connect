"""Typed data models for the AH Shopping integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


@dataclass(slots=True)
class AhPrice:
    """Product price information."""

    now: float | None = None
    was: float | None = None

    @classmethod
    def from_api(cls, data: Any) -> AhPrice:
        if isinstance(data, (int, float)):
            return cls(now=float(data))
        if not isinstance(data, dict):
            return cls()
        now = data.get("now")
        was = data.get("was")
        if isinstance(now, dict):
            now = now.get("amount")
        if isinstance(was, dict):
            was = was.get("amount")
        return cls(now=_safe_float(now), was=_safe_float(was))


@dataclass(slots=True)
class AhImage:
    """Product image."""

    url: str | None = None
    width: int | None = None
    height: int | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> AhImage:
        return cls(
            url=data.get("url"),
            width=data.get("width"),
            height=data.get("height"),
        )


@dataclass(slots=True)
class AhProduct:
    """A product from AH search or detail."""

    webshop_id: int
    title: str
    price: float | None = None
    price_was: float | None = None
    unit_size: str | None = None
    brand: str | None = None
    image_url: str | None = None
    available: bool = True
    is_bonus: bool = False
    bonus_mechanism: str | None = None
    category: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> AhProduct:
        price_now = data.get("currentPrice")
        price_was = data.get("priceBeforeBonus")
        price_info = data.get("priceBeforeBonus") or data.get("price") or {}
        if price_now is None and isinstance(price_info, dict):
            price_now = price_info.get("now") or price_info.get("amount")
        elif price_now is None and isinstance(price_info, (int, float)):
            price_now = price_info

        images = data.get("images") or []
        image_url = None
        if images and isinstance(images[0], dict):
            image_url = images[0].get("url")

        return cls(
            webshop_id=_safe_int(data.get("webshopId") or data.get("id")),
            title=str(data.get("title") or data.get("description") or "Unknown"),
            price=_safe_float(price_now),
            price_was=_safe_float(price_was if isinstance(price_was, (int, float)) else None),
            unit_size=data.get("salesUnitSize") or data.get("unitSize"),
            brand=data.get("brand"),
            image_url=image_url,
            available=bool(data.get("availableOnline", True)),
            is_bonus=bool(data.get("isBonus")),
            bonus_mechanism=data.get("bonusMechanism"),
            category=data.get("mainCategory") or data.get("category"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "webshop_id": self.webshop_id,
            "title": self.title,
            "price": self.price,
            "price_was": self.price_was,
            "unit_size": self.unit_size,
            "brand": self.brand,
            "image_url": self.image_url,
            "available": self.available,
            "is_bonus": self.is_bonus,
            "bonus_mechanism": self.bonus_mechanism,
            "category": self.category,
        }


@dataclass(slots=True)
class AhReceiptItem:
    """Line item on a receipt."""

    description: str
    quantity: int = 1
    amount: float | None = None
    product_id: int | None = None
    webshop_id: int | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> AhReceiptItem:
        amount_info = data.get("amount") or {}
        price_info = data.get("price") or {}
        return cls(
            description=str(data.get("name") or data.get("description") or "Unknown"),
            quantity=_safe_int(data.get("quantity"), 1),
            amount=_safe_float(
                amount_info.get("amount") if isinstance(amount_info, dict) else amount_info
            ),
            product_id=_safe_int(data.get("id")) or None,
        )


@dataclass(slots=True)
class AhReceipt:
    """A receipt from AH."""

    transaction_id: str
    date: datetime | None = None
    total: float | None = None
    store_name: str | None = None
    items: list[AhReceiptItem] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> AhReceipt:
        total_info = data.get("total") or data.get("totalAmount") or {}
        total: float | None = None
        if isinstance(total_info, dict):
            total = _safe_float(total_info.get("amount"))
        elif isinstance(total_info, (int, float)):
            total = float(total_info)

        items: list[AhReceiptItem] = []
        for raw in data.get("products") or data.get("items") or []:
            if isinstance(raw, dict):
                try:
                    items.append(AhReceiptItem.from_api(raw))
                except (KeyError, TypeError, ValueError):
                    pass

        return cls(
            transaction_id=str(data.get("transactionId") or data.get("id") or ""),
            date=_parse_datetime(data.get("transactionDateTime") or data.get("dateTime") or data.get("date")),
            total=total,
            store_name=data.get("storeName"),
            items=items,
        )


@dataclass(slots=True)
class AhShoppingList:
    """Remote AH shopping list summary."""

    list_id: str
    name: str
    item_count: int = 0

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> AhShoppingList:
        return cls(
            list_id=str(data.get("id") or ""),
            name=str(data.get("description") or data.get("name") or "List"),
            item_count=_safe_int(data.get("itemCount") or data.get("totalSize")),
        )


@dataclass(slots=True)
class AhShoppingListItem:
    """Item on remote AH shopping list."""

    item_id: str
    product_id: int | None = None
    title: str | None = None
    quantity: int = 1
    checked: bool = False

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> AhShoppingListItem:
        return cls(
            item_id=str(data.get("id") or ""),
            product_id=_safe_int(data.get("productId")) or None,
            title=data.get("description") or data.get("name"),
            quantity=max(_safe_int(data.get("quantity"), 1), 1),
            checked=bool(data.get("checked") or data.get("strikeThrough")),
        )


@dataclass(slots=True)
class AhOrderItem:
    """Item in AH order/cart."""

    product_id: int
    quantity: int = 1
    title: str | None = None
    price: float | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> AhOrderItem:
        product = data.get("product") or {}
        if isinstance(product, dict):
            return cls(
                product_id=_safe_int(product.get("webshopId") or data.get("productId")),
                quantity=max(_safe_int(data.get("quantity"), 1), 1),
                title=product.get("title"),
                price=_safe_float(product.get("currentPrice") or product.get("priceBeforeBonus")),
            )
        return cls(
            product_id=_safe_int(data.get("productId")),
            quantity=max(_safe_int(data.get("quantity"), 1), 1),
        )


@dataclass(slots=True)
class AhOrder:
    """AH order / cart."""

    order_id: str
    state: str | None = None
    total_price: float | None = None
    total_discount: float | None = None
    item_count: int = 0
    items: list[AhOrderItem] = field(default_factory=list)

    @classmethod
    def from_summary_api(cls, data: dict[str, Any]) -> AhOrder:
        total_info = data.get("totalPrice") or {}
        items: list[AhOrderItem] = []
        for raw in data.get("orderedProducts") or []:
            if isinstance(raw, dict):
                items.append(AhOrderItem.from_api(raw))
        return cls(
            order_id=str(data.get("id") or data.get("orderId") or ""),
            state=data.get("state") or data.get("orderState"),
            total_price=_safe_float(total_info.get("priceTotalPayable")),
            total_discount=_safe_float(total_info.get("priceDiscount")),
            item_count=len(items),
            items=items,
        )


@dataclass(slots=True)
class AhOrderSummary:
    """Order totals summary."""

    total_items: int = 0
    total_price: float | None = None
    total_discount: float | None = None


@dataclass(slots=True)
class AhFulfillment:
    """Open order fulfillment / delivery."""

    order_id: int
    status: str | None = None
    status_description: str | None = None
    total_price: float | None = None
    modifiable: bool = False

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> AhFulfillment:
        total = data.get("totalPrice") or {}
        if isinstance(total, dict):
            inner = total.get("totalPrice") or {}
            total_amount = _safe_float(inner.get("amount") if isinstance(inner, dict) else inner)
        else:
            total_amount = _safe_float(total)
        return cls(
            order_id=_safe_int(data.get("orderId")),
            status=data.get("status"),
            status_description=data.get("statusDescription"),
            total_price=total_amount,
            modifiable=bool(data.get("modifiable")),
        )


@dataclass(slots=True)
class AhStore:
    """AH store location (stub parser)."""

    store_id: str | None = None
    name: str | None = None
    postal_code: str | None = None
    city: str | None = None


@dataclass(slots=True)
class AhMember:
    """Authenticated member profile."""

    member_id: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> AhMember:
        name = data.get("name") or {}
        return cls(
            member_id=str(data.get("id") or ""),
            email=data.get("emailAddress"),
            first_name=name.get("first") if isinstance(name, dict) else None,
            last_name=name.get("last") if isinstance(name, dict) else None,
        )


@dataclass(slots=True)
class LocalShoppingListItem:
    """An item on the local HA shopping list."""

    webshop_id: int
    title: str
    quantity: int = 1
    added_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "webshop_id": self.webshop_id,
            "title": self.title,
            "quantity": self.quantity,
            "added_at": self.added_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LocalShoppingListItem:
        return cls(
            webshop_id=int(data["webshop_id"]),
            title=str(data.get("title") or "Unknown"),
            quantity=int(data.get("quantity") or 1),
            added_at=str(data.get("added_at") or datetime.now(timezone.utc).isoformat()),
        )


# Backward compatibility alias
ShoppingListItem = LocalShoppingListItem
