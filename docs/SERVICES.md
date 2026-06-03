# Services

Domain: `ah_connect`  
Event: `ah_connect_result`

## Example

```yaml
service: ah_connect.search_products
data:
  query: "melk"
  limit: 5
```

Listen for results:

```yaml
event: ah_connect_result
```

## Anonymous

- `search_products`, `search_products_filtered`
- `get_product`, `get_product_full`, `get_products_by_ids`
- `get_bonus_products`, `get_koopjes` (requires `postal_code`)

## Authenticated

- `get_member`, `get_receipts`, `get_receipt`
- `get_shopping_lists`, `get_shopping_list_items`
- `add_product_to_shopping_list`, `add_free_text_to_shopping_list`
- `add_to_shopping_list`, `clear_shopping_list`, `check_shopping_list_item`

## Experimental (`experimental_order_enabled`)

- `get_order`, `get_order_details`, `get_order_summary`
- `add_to_order`, `remove_from_order`, `update_order_item`
- `reopen_order`, `revert_order`, `get_fulfillments`, `search_stores`

## Never available

- `checkout`, `place_order`, `payment`, `finalize_order`
