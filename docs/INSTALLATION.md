# Installatie

## Vereisten

- Home Assistant **2024.1** of nieuwer
- Internetverbinding
- (Optioneel) Albert Heijn account voor authenticated mode

## Installatie via HACS

1. Open **HACS** in Home Assistant.
2. Ga naar **Integrations** (drie puntjes → Custom repositories).
3. Voeg de repository URL toe:
   - **URL:** `https://github.com/mmaaart3n/ah-connect`
   - **Category:** Integration
4. Zoek **AH Shopping** en installeer.
5. **Herstart Home Assistant** (verplicht na installatie).
6. Ga naar **Instellingen → Apparaten & services → Integratie toevoegen**.
7. Zoek op **AH Shopping** en volg de config flow.

## Handmatige installatie

1. Kopieer de map `custom_components/ah_shopping` naar je Home Assistant config directory:

   ```
   config/custom_components/ah_shopping/
   ```

2. Herstart Home Assistant.
3. Voeg de integratie toe via de UI.

## Config flow

### Stap 1: Authenticatiemodus kiezen

| Modus | Gebruik |
|-------|---------|
| **Anonymous** | Alleen product zoeken, geen bonnen |
| **Authenticated** | Product zoeken + bon-sensoren |

### Stap 2a: Anonymous

De integratie haalt automatisch een anoniem token op. Geen verdere stappen nodig.

### Stap 2b: Authenticated (OAuth)

1. Open de OAuth URL in je browser (wordt getoond in de config flow).
2. Log in met je AH-account.
3. Na redirect zie je een code in de URL (`appie://login-exit?code=XXXX`).
4. Kopieer de code en plak in de config flow.

Zie [AUTHENTICATION.md](AUTHENTICATION.md) voor details.

## Opties configureren

Na installatie: **Instellingen → Apparaten & services → AH Shopping → Configureer**.

| Optie | Standaard | Beschrijving |
|-------|-----------|--------------|
| Scan interval | 3600s | Hoe vaak bonnen worden opgehaald |
| Max search results | 10 | Standaard limiet voor zoeken |
| Enable receipts sensor | Aan | Bon-sensoren aan/uit |
| Experimental cart | Uit | Experimentele winkelwagen (niet in MVP) |

## Verificatie

Na installatie controleer:

1. Entiteit `sensor.ah_shopping_list_count` bestaat (waarde: 0).
2. Service `ah_shopping.search_products` is beschikbaar onder **Ontwikkelaarshulpmiddelen → Services**.
3. (Authenticated) Entiteiten `sensor.ah_last_receipt_total` en `sensor.ah_last_receipt_date` bestaan.

## Upgraden

Via HACS: klik op **Update** en herstart Home Assistant.

Handmatig: vervang de map `custom_components/ah_shopping` en herstart.

## Deïnstalleren

1. Verwijder de integratie via **Instellingen → Apparaten & services**.
2. (HACS) Deïnstalleer via HACS.
3. Herstart Home Assistant.

Lokale shopping list data wordt automatisch opgeruimd bij verwijderen van de config entry.
