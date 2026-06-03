"""Data models for AH Connect API responses."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def _float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def _int(val: Any, default: int = 0) -> int:
    try:
        return int(val) if val is not None else default
    except (TypeError, ValueError):
        return default


@dataclass
class AhPrice:
    now: float = 0.0
    was: float = 0.0
    unit_size: str | None = None

    @classmethod
    def from_api(cls, data: Any) -> AhPrice:
        if not isinstance(data, dict):
            return cls()
        return cls(
            now=_float(data.get("now")),
            was=_float(data.get("was")),
            unit_size=data.get("unitSize") or data.get("unit_size"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AhImage:
    url: str = ""
    width: int | None = None
    height: int | None = None

    @classmethod
    def from_api(cls, data: Any) -> AhImage:
        if not isinstance(data, dict):
            return cls()
        return cls(
            url=str(data.get("url", "")),
            width=data.get("width"),
            height=data.get("height"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class AhProduct:
    id: int = 0
    webshop_id: str = ""
    title: str = ""
    brand: str = ""
    category: str = ""
    sub_category: str = ""
    price: AhPrice = field(default_factory=AhPrice)
    images: list[AhImage] = field(default_factory=list)
    is_bonus: bool = False
    bonus_mechanism: str = ""
    is_available: bool = False
    is_orderable: bool = False
    unit_size: str = ""
    nutri_score: str = ""

    @classmethod
    def from_product_response(cls, data: dict[str, Any]) -> AhProduct:
        webshop_id = _int(data.get("webshopId") or data.get("id"))
        price_now = _float(data.get("currentPrice"))
        if price_now == 0:
            price_now = _float(data.get("priceBeforeBonus"))
        images = [AhImage.from_api(i) for i in data.get("images") or []]
        return cls(
            id=webshop_id,
            webshop_id=str(webshop_id),
            title=str(data.get("title", "")),
            brand=str(data.get("brand", "")),
            category=str(data.get("mainCategory") or data.get("category", "")),
            sub_category=str(data.get("subCategory", "")),
            price=AhPrice(now=price_now, was=_float(data.get("priceBeforeBonus"))),
            images=images,
            is_bonus=bool(data.get("isBonus")),
            bonus_mechanism=str(data.get("bonusMechanism", "")),
            is_available=bool(data.get("availableOnline")),
            is_orderable=bool(data.get("isOrderable")),
            unit_size=str(data.get("salesUnitSize", "")),
            nutri_score=str(data.get("nutriscore") or data.get("nutriScore", "")),
        )

    @classmethod
    def from_api(cls, data: Any) -> AhProduct:
        if not isinstance(data, dict):
            return cls()
        if "productCard" in data:
            return cls.from_product_response(data["productCard"])
        if "webshopId" in data or "currentPrice" in data:
            return cls.from_product_response(data)
        price = AhPrice.from_api(data.get("price") or {})
        images = [AhImage.from_api(i) for i in data.get("images") or []]
        pid = _int(data.get("id") or data.get("webshopId"))
        return cls(
            id=pid,
            webshop_id=str(data.get("webshopId") or pid),
            title=str(data.get("title", "")),
            brand=str(data.get("brand", "")),
            category=str(data.get("category", "")),
            sub_category=str(data.get("subCategory", "")),
            price=price,
            images=images,
            is_bonus=bool(data.get("isBonus")),
            bonus_mechanism=str(data.get("bonusMechanism", "")),
            is_available=bool(data.get("isAvailable")),
            is_orderable=bool(data.get("isOrderable")),
            unit_size=str(data.get("unitSize", "")),
            nutri_score=str(data.get("nutriScore", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["price"] = self.price.to_dict()
        d["images"] = [i.to_dict() for i in self.images]
        return d


@dataclass
class AhReceiptItem:
    description: str = ""
    quantity: int = 0
    amount: float = 0.0
    unit_price: float = 0.0
    product_id: int = 0
    webshop_id: int = 0

    @classmethod
    def from_api(cls, data: Any) -> AhReceiptItem:
        if not isinstance(data, dict):
            return cls()
        price = data.get("price") or {}
        amount_obj = data.get("amount") or {}
        unit = _float(price.get("amount") if isinstance(price, dict) else price)
        amt = _float(amount_obj.get("amount") if isinstance(amount_obj, dict) else amount_obj)
        return cls(
            description=str(data.get("name") or data.get("description", "")),
            quantity=_int(data.get("quantity")),
            amount=amt,
            unit_price=unit,
            product_id=_int(data.get("id") or data.get("productId")),
            webshop_id=_int(data.get("webshopId")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AhReceipt:
    transaction_id: str = ""
    date: str = ""
    total_amount: float = 0.0
    items: list[AhReceiptItem] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: Any) -> AhReceipt:
        if not isinstance(data, dict):
            return cls()
        total = data.get("totalAmount")
        if isinstance(total, dict):
            total_amount = _float(total.get("amount"))
        else:
            total_amount = _float(total)
        items = [AhReceiptItem.from_api(i) for i in data.get("items") or data.get("products") or []]
        return cls(
            transaction_id=str(data.get("transactionId") or data.get("id", "")),
            date=str(data.get("date") or data.get("dateTime", "")),
            total_amount=total_amount,
            items=items,
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["items"] = [i.to_dict() for i in self.items]
        return d


@dataclass
class AhShoppingListItem:
    id: str = ""
    name: str = ""
    product_id: int = 0
    quantity: int = 1
    checked: bool = False

    @classmethod
    def from_api(cls, data: Any) -> AhShoppingListItem:
        if not isinstance(data, dict):
            return cls()
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name") or data.get("description", "")),
            product_id=_int(data.get("productId")),
            quantity=max(_int(data.get("quantity"), 1), 1),
            checked=bool(data.get("checked") or data.get("strikeThrough")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AhShoppingList:
    id: str = ""
    name: str = ""
    item_count: int = 0
    items: list[AhShoppingListItem] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: Any) -> AhShoppingList:
        if not isinstance(data, dict):
            return cls()
        items = [AhShoppingListItem.from_api(i) for i in data.get("items") or []]
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name") or data.get("description", "")),
            item_count=_int(data.get("itemCount") or data.get("totalSize"), len(items)),
            items=items,
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["items"] = [i.to_dict() for i in self.items]
        return d


@dataclass
class AhOrderItem:
    product_id: int = 0
    quantity: int = 0
    product: AhProduct | None = None

    @classmethod
    def from_api(cls, data: Any) -> AhOrderItem:
        if not isinstance(data, dict):
            return cls()
        prod_data = data.get("product")
        product = AhProduct.from_api(prod_data) if prod_data else None
        pid = _int(data.get("productId") or (prod_data or {}).get("webshopId"))
        return cls(
            product_id=pid,
            quantity=_int(data.get("quantity") or data.get("amount")),
            product=product,
        )

    def to_dict(self) -> dict[str, Any]:
        d = {"product_id": self.product_id, "quantity": self.quantity}
        if self.product:
            d["product"] = self.product.to_dict()
        return d


@dataclass
class AhOrder:
    id: str = ""
    state: str = ""
    items: list[AhOrderItem] = field(default_factory=list)
    total_count: int = 0
    total_price: float = 0.0
    total_discount: float = 0.0

    @classmethod
    def from_summary(cls, data: dict[str, Any]) -> AhOrder:
        items = []
        for op in data.get("orderedProducts") or []:
            items.append(AhOrderItem.from_api(op))
        total_price = data.get("totalPrice") or {}
        return cls(
            id=str(data.get("id", "")),
            state=str(data.get("state", "")),
            items=items,
            total_count=len(items),
            total_price=_float(total_price.get("priceTotalPayable")),
            total_discount=_float(total_price.get("priceDiscount")),
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["items"] = [i.to_dict() for i in self.items]
        return d


@dataclass
class AhOrderSummary:
    total_items: int = 0
    total_price: float = 0.0
    total_discount: float = 0.0
    delivery_cost: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AhFulfillment:
    order_id: int = 0
    status: str = ""
    status_description: str = ""
    shopping_type: str = ""
    total_price: float = 0.0
    transaction_completed: bool = False
    modifiable: bool = False

    @classmethod
    def from_api(cls, data: Any) -> AhFulfillment:
        if not isinstance(data, dict):
            return cls()
        total = data.get("totalPrice") or {}
        if isinstance(total, dict) and "totalPrice" in total:
            total = total["totalPrice"]
        amount = _float(total.get("amount") if isinstance(total, dict) else total)
        delivery = data.get("delivery") or {}
        return cls(
            order_id=_int(data.get("orderId")),
            status=str(delivery.get("status") or data.get("statusCode", "")),
            status_description=str(data.get("statusDescription", "")),
            shopping_type=str(data.get("shoppingType", "")),
            total_price=amount,
            transaction_completed=bool(data.get("transactionCompleted")),
            modifiable=bool(data.get("modifiable")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AhStore:
    id: int = 0
    name: str = ""
    store_type: str = ""
    street: str = ""
    postal_code: str = ""
    city: str = ""

    @classmethod
    def from_api(cls, data: Any) -> AhStore:
        if not isinstance(data, dict):
            return cls()
        addr = data.get("address") or {}
        return cls(
            id=_int(data.get("id")),
            name=str(data.get("name", "")),
            store_type=str(data.get("storeType", "")),
            street=str(addr.get("street", "")),
            postal_code=str(addr.get("postalCode", "")),
            city=str(addr.get("city", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AhMember:
    id: str = ""
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    bonus_card_number: str = ""

    @classmethod
    def from_api(cls, data: Any) -> AhMember:
        if not isinstance(data, dict):
            return cls()
        name = data.get("name") or {}
        cards = data.get("cards") or {}
        return cls(
            id=str(data.get("id", "")),
            first_name=str(name.get("first") or data.get("firstName", "")),
            last_name=str(name.get("last") or data.get("lastName", "")),
            email=str(data.get("email") or data.get("emailAddress", "")),
            bonus_card_number=str(cards.get("bonus") or data.get("bonusCardNumber", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AhKoopje:
    product_id: int = 0
    title: str = ""
    brand: str = ""
    category: str = ""
    price_was: str = ""
    price_now: str = ""
    stock: int = 0
    markdown_percentage: float = 0.0

    @classmethod
    def from_api(cls, data: Any) -> AhKoopje:
        if not isinstance(data, dict):
            return cls()
        prod = data.get("product") or {}
        markdown = data.get("markdown") or {}
        bargain = data.get("bargainPrice") or {}
        return cls(
            product_id=_int(prod.get("id")),
            title=str(prod.get("title", "")),
            brand=str(prod.get("brand", "")),
            category=str(data.get("categoryTitle", "")),
            price_was=str(bargain.get("priceWas", "")),
            price_now=str(bargain.get("priceNow", "")),
            stock=_int(data.get("stock")),
            markdown_percentage=_float(markdown.get("markdownPercentage")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
