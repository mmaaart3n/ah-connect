"""Typed data models for the AH Shopping integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class AhProduct:
    """A product from AH search results."""

    webshop_id: int
    title: str
    price: float | None = None
    unit_size: str | None = None
    brand: str | None = None
    image_url: str | None = None
    available: bool = True

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> AhProduct:
        """Parse a product from API response data."""
        price_info = data.get("priceBeforeBonus") or data.get("price") or {}
        price: float | None = None
        if isinstance(price_info, dict):
            price = price_info.get("now") or price_info.get("amount")
        elif isinstance(price_info, (int, float)):
            price = float(price_info)

        images = data.get("images") or []
        image_url = None
        if images and isinstance(images[0], dict):
            image_url = images[0].get("url")

        return cls(
            webshop_id=int(data.get("webshopId") or data.get("id") or 0),
            title=str(data.get("title") or data.get("description") or "Unknown"),
            price=price,
            unit_size=data.get("salesUnitSize") or data.get("unitSize"),
            brand=data.get("brand"),
            image_url=image_url,
            available=bool(data.get("availableOnline", True)),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "webshop_id": self.webshop_id,
            "title": self.title,
            "price": self.price,
            "unit_size": self.unit_size,
            "brand": self.brand,
            "image_url": self.image_url,
            "available": self.available,
        }


@dataclass(slots=True)
class AhReceipt:
    """A receipt summary from AH."""

    transaction_id: str
    date: datetime | None = None
    total: float | None = None
    store_name: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> AhReceipt:
        """Parse a receipt from API response data."""
        date_str = data.get("transactionDateTime") or data.get("date")
        parsed_date: datetime | None = None
        if date_str:
            try:
                parsed_date = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
            except ValueError:
                parsed_date = None

        total_info = data.get("total") or data.get("totalAmount") or {}
        total: float | None = None
        if isinstance(total_info, dict):
            total = total_info.get("amount")
        elif isinstance(total_info, (int, float)):
            total = float(total_info)

        return cls(
            transaction_id=str(data.get("transactionId") or data.get("id") or ""),
            date=parsed_date,
            total=total,
            store_name=data.get("storeName") or data.get("address", {}).get("city"),
        )


@dataclass(slots=True)
class ShoppingListItem:
    """An item on the local AH shopping list."""

    webshop_id: int
    title: str
    quantity: int = 1
    added_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "webshop_id": self.webshop_id,
            "title": self.title,
            "quantity": self.quantity,
            "added_at": self.added_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ShoppingListItem:
        """Deserialize from a plain dict."""
        return cls(
            webshop_id=int(data["webshop_id"]),
            title=str(data.get("title") or "Unknown"),
            quantity=int(data.get("quantity") or 1),
            added_at=str(data.get("added_at") or datetime.now(timezone.utc).isoformat()),
        )
