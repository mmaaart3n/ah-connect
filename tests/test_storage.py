"""Tests for shopping list storage logic."""

from custom_components.ah_shopping.models import ShoppingListItem


class TestShoppingListLogic:
    """Test shopping list operations without HA storage."""

    def test_count_sums_quantities(self):
        items = [
            ShoppingListItem(webshop_id=1, title="A", quantity=2),
            ShoppingListItem(webshop_id=2, title="B", quantity=3),
        ]
        count = sum(i.quantity for i in items)
        assert count == 5

    def test_remove_by_webshop_id(self):
        items = [
            ShoppingListItem(webshop_id=1, title="A"),
            ShoppingListItem(webshop_id=2, title="B"),
        ]
        webshop_id = 1
        remaining = [i for i in items if i.webshop_id != webshop_id]
        assert len(remaining) == 1
        assert remaining[0].webshop_id == 2

    def test_increment_existing(self):
        items = [ShoppingListItem(webshop_id=1, title="Melk", quantity=1)]
        for item in items:
            if item.webshop_id == 1:
                item.quantity += 2
        assert items[0].quantity == 3
