# Services

Alle services zijn beschikbaar onder domain `ah_shopping`.

## search_products

Zoek producten op Albert Heijn.

```yaml
service: ah_shopping.search_products
data:
  query: "volkoren brood"
  limit: 10
```

| Veld | Type | Verplicht | Default | Beschrijving |
|------|------|-----------|---------|--------------|
| `query` | string | ✅ | — | Zoekterm |
| `limit` | integer | ❌ | 10 | Max resultaten (1–50) |

**Output:**

- Event: `ah_shopping_products_found` met `products` array
- Persistent notification met samenvatting

**Event payload voorbeeld:**

```json
{
  "query": "melk",
  "count": 3,
  "products": [
    {
      "webshop_id": 12345,
      "title": "AH Halfvolle melk",
      "price": 1.19,
      "unit_size": "1 liter",
      "brand": "AH",
      "available": true
    }
  ]
}
```

---

## add_to_list

Voeg een product toe aan de lokale boodschappenlijst.

```yaml
service: ah_shopping.add_to_list
data:
  webshop_id: 12345
  title: "AH Halfvolle melk"
  quantity: 2
```

| Veld | Type | Verplicht | Default |
|------|------|-----------|---------|
| `webshop_id` | integer | ✅ | — |
| `title` | string | ❌ | "Unknown" |
| `quantity` | integer | ❌ | 1 |

Bestaande items met dezelfde `webshop_id` krijgen extra quantity.

---

## remove_from_list

Verwijder een product van de lokale lijst.

```yaml
service: ah_shopping.remove_from_list
data:
  webshop_id: 12345
```

---

## clear_list

Maak de lokale lijst leeg.

```yaml
service: ah_shopping.clear_list
```

---

## get_list

Haal de huidige lijst op via event.

```yaml
service: ah_shopping.get_list
```

**Event:** `ah_shopping_list_retrieved`

```json
{
  "items": [...],
  "count": 3
}
```

---

## refresh_receipts

Forceer vernieuwing van bondata. **Alleen authenticated mode.**

```yaml
service: ah_shopping.refresh_receipts
```

---

## export_list_to_todo

Exporteer lokale lijst naar een Home Assistant todo entity.

```yaml
service: ah_shopping.export_list_to_todo
data:
  todo_entity_id: todo.shopping_list
```

| Veld | Type | Verplicht | Beschrijving |
|------|------|-----------|--------------|
| `todo_entity_id` | string | ❌ | Doel todo entity. Auto-detect als leeg. |

Vereist een actieve todo-integratie (bijv. de ingebouwde Shopping List / Todo).

---

## Events overzicht

| Event | Wanneer |
|-------|---------|
| `ah_shopping_products_found` | Na `search_products` |
| `ah_shopping_list_retrieved` | Na `get_list` |
| `ah_shopping_list_updated` | Na add/remove/clear |
