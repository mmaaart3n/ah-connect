"""Tests for AH Connect models."""

from custom_components.ah_connect.models import (
    AhOrder,
    AhProduct,
    AhReceipt,
    AhShoppingList,
)


def test_product_from_search_response():
    product = AhProduct.from_product_response(
        {
            "webshopId": 12345,
            "title": "Melk",
            "currentPrice": 1.29,
            "priceBeforeBonus": 1.49,
            "isBonus": True,
            "availableOnline": True,
        }
    )
    assert product.id == 12345
    assert product.title == "Melk"
    assert product.price.now == 1.29
    assert product.is_bonus is True


def test_receipt_from_api():
    receipt = AhReceipt.from_api(
        {
            "transactionId": "tx-1",
            "dateTime": "2026-01-01",
            "totalAmount": {"amount": 12.5},
        }
    )
    assert receipt.transaction_id == "tx-1"
    assert receipt.total_amount == 12.5


def test_shopping_list_from_api():
    lst = AhShoppingList.from_api(
        {"id": "abc", "description": "Week", "itemCount": 3}
    )
    assert lst.id == "abc"
    assert lst.name == "Week"
    assert lst.item_count == 3


def test_order_from_summary():
    order = AhOrder.from_summary(
        {
            "id": 99,
            "state": "NEW",
            "orderedProducts": [{"productId": 1, "quantity": 2}],
            "totalPrice": {"priceTotalPayable": 10.0, "priceDiscount": 1.0},
        }
    )
    assert order.id == "99"
    assert order.total_price == 10.0
