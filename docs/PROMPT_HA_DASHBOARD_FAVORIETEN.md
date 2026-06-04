# Prompt: HA-dashboard “AH Favorieten / winkelmandje”

Kopieer alles onder **START PROMPT** naar je andere Cursor-sessie (Home Assistant in Docker).

---

## START PROMPT

Je bent een senior Home Assistant consultant en Lovelace/dashboard-specialist.

### Context

- Home Assistant draait in **Docker** (geen directe toegang tot host-macOS, wel UI + YAML + File Editor / Studio Code Server).
- De custom integration **AH Connect** (`domain: ah_connect`) is geïnstalleerd via HACS en **werkt** met authenticated setup (appie-go config JSON).
- Repository integratie (alleen als referentie, niet aanpassen tenzij echt nodig): https://github.com/mmaaart3n/ah-connect
- Doel UX: vergelijkbaar met https://www.ah.nl/favorieten — zoeken, producten toevoegen aan boodschappenlijst, lijst bekijken; wijzigingen moeten in de **officiële AH-app** op dezelfde lijst verschijnen (remote AH-lijst, geen losse HA-only lijst als hoofdlijst).

### Wat de integratie AL levert (geen nieuwe Python nodig)

**Event (antwoord op services):** `ah_connect_result`  
Payload o.a.: `service`, `result` (lijst objecten of enkel object).

**Belangrijkste services:**

| Service | Doel |
|---------|------|
| `ah_connect.search_products` | Zoeken: `query`, `limit` |
| `ah_connect.search_products_filtered` | Zoeken met `bonus_only` |
| `ah_connect.get_product` | Detail op `product_id` |
| `ah_connect.get_shopping_lists` | AH-lijsten (UUID `id`) |
| `ah_connect.get_shopping_list_items` | Items in lijst: `list_id` |
| `ah_connect.add_product_to_shopping_list` | Product naar **hoofd-boodschappenlijst** AH: `product_id`, `quantity` |
| `ah_connect.add_free_text_to_shopping_list` | Vrije tekst: `name`, `quantity` |
| `ah_connect.add_to_shopping_list` | Naar specifieke lijst: `list_id`, `product_id` of `name` |
| `ah_connect.check_shopping_list_item` | Afvinken: `list_id`, `item_id`, `checked` |
| `ah_connect.clear_shopping_list` | Lijst leegmaken: `list_id` |

**Product in `result` (zoeken):** o.a. `id`, `title`, `brand`, `price.now`, `is_bonus`, `unit_size`.

**Niet bouwen:** checkout, place order, betaling.

### Opdracht

Bouw in **deze HA Docker-omgeving** een compleet, dagelijks bruikbaar dashboard “AH Winkelen”:

1. **Zoekveld** + knop “Zoeken” (AH-producten).
2. **Zoekresultaten** tonen (titel, prijs, bonus) — max ~10 resultaten.
3. Per resultaat: knop **“Toevoegen aan lijst”** → `add_product_to_shopping_list` met juiste `product_id`.
4. Sectie **“Mijn AH-lijst”**: items ophalen via `get_shopping_lists` + `get_shopping_list_items`, tonen met afvink-knop (`check_shopping_list_item`).
5. Na toevoegen: korte bevestiging (toast/notificatie) en lijst verversen.
6. Optioneel: sensor `sensor.ah_connect_remote_shopping_list_count` tonen als die bestaat.

### Technische richtlijnen

- Gebruik waar mogelijk **helpers** (`input_text`, `input_select`, `input_number`) voor zoekterm en geselecteerd product.
- Gebruik **scripts** + **automations** die luisteren op `ah_connect_result` en helpers vullen (geen custom integration wijzigen).
- Lovelace: moderne kaarten (entities, button, mushroom indien aanwezig, of markdown + custom button-card); **mobiel-vriendelijk**.
- Alle YAML in `configuration.yaml` includes of `scripts.yaml` / `automations.yaml` / `packages/` — geef **volledige, plakbare** bestanden.
- Geen secrets in YAML; geen tokens loggen.
- Als `input_select` te klein is voor dynamische zoekresultaten: gebruik `variable` + `script` of `rest`/template of meerdere `input_button` met script dat laatste zoekresultaten in `input_text`/`sensor` template opslaat — kies de **eenvoudigste robuuste oplossing** en leg uit waarom.

### Verwachte flow (data)

```
Gebruiker typt "melk" → script roept ah_connect.search_products aan
→ automation op ah_connect_result (service=search_products) slaat result op
→ dashboard toont keuzes → knop "Toevoegen" roept add_product_to_shopping_list aan
→ refresh script: get_shopping_lists → get_shopping_list_items → update sensors/templates
→ zelfde items zichtbaar in AH-app (favorieten/boodschappenlijst)
```

### Acceptatiecriteria

- [ ] Zoeken werkt vanuit dashboard zonder Developer Tools.
- [ ] Minstens één product toevoegen werkt; verschijnt in AH-app na refresh (vermeld dat gebruiker AH-app moet verversen).
- [ ] Lijst tonen met titel + quantity; afvinken werkt.
- [ ] Fouten (niet ingelogd, geen resultaten) netjes in UI.
- [ ] Documentatie in `README_DASHBOARD.md` in HA config-map: welke helpers/scripts/entities, hoe onderhouden.

### Beperkingen

- HA draait in Docker: geen `appie login` in container; integratie moet al geconfigureerd zijn.
- Geen wijzigingen aan ah-connect repo tenzij je een blocker vindt — dan alleen minimal fix voorstellen.
- Nederlands in UI-labels.

### Output die ik van je verwacht

1. Lijst van aan te maken helpers (entity_id’s).
2. `scripts.yaml` (of package) — volledig.
3. `automations.yaml` — volledig (event `ah_connect_result`).
4. Lovelace dashboard YAML (views + cards).
5. Korte gebruikershandleiding (5 stappen).
6. Troubleshooting (geen resultaten, verkeerde list_id, 401).

Begin met inventarisatie: welke `ah_connect` entities/sensors bestaan al in deze HA? Vraag alleen als je echt geen toegang hebt tot entity registry — anders assumeer standaard namen en documenteer placeholders.

### Referentie integratie-docs

- Services: zie HACS repo `docs/SERVICES.md`
- Auth: ingelogd via appie-go config vereist voor lijst/bon
- Event: `ah_connect_result`

---

## EINDE PROMPT
