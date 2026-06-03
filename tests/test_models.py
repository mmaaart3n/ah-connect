"""Tests for AH data models."""

from custom_components.ah_shopping.models import AhProduct, AhReceipt, ShoppingListItem


class TestAhProduct:
    """Test AhProduct parsing."""

    def test_from_api_full(self):
        data = {
            "webshopId": 12345,
            "title": "AH Melk",
            "priceBeforeBonus": {"now": 1.19},
            "salesUnitSize": "1 liter",
            "brand": "AH",
            "images": [{"url": "https://example.com/image.jpg"}],
            "availableOnline": True,
        }
        product = AhProduct.from_api(data)
        assert product.webshop_id == 12345
        assert product.title == "AH Melk"
        assert product.price == 1.19
        assert product.unit_size == "1 liter"
        assert product.brand == "AH"
        assert product.image_url == "https://example.com/image.jpg"
        assert product.available is True

    def test_from_api_minimal(self):
        data = {"webshopId": 99, "title": "Test"}
        product = AhProduct.from_api(data)
        assert product.webshop_id == 99
        assert product.price is None

    def test_to_dict(self):
        product = AhProduct(webshop_id=1, title="Test", price=2.50)
        d = product.to_dict()
        assert d["webshop_id"] == 1
        assert d["price"] == 2.50


class TestAhReceipt:
    """Test AhReceipt parsing."""

    def test_from_api(self):
        data = {
            "transactionId": "abc-123",
            "transactionDateTime": "2024-06-01T14:30:00+00:00",
            "total": {"amount": 45.67},
            "storeName": "AH Amsterdam",
        }
        receipt = AhReceipt.from_api(data)
        assert receipt.transaction_id == "abc-123"
        assert receipt.total == 45.67
        assert receipt.store_name == "AH Amsterdam"
        assert receipt.date is not None


class TestShoppingListItem:
    """Test ShoppingListItem serialization."""

    def test_roundtrip(self):
        item = ShoppingListItem(webshop_id=123, title="Melk", quantity=2)
        restored = ShoppingListItem.from_dict(item.to_dict())
        assert restored.webshop_id == 123
        assert restored.title == "Melk"
        assert restored.quantity == 2
