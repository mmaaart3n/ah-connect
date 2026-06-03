# GitHub Repository Setup

Deze stappen moet je **handmatig in GitHub** uitvoeren. Repository metadata (description, topics) kan niet via codebestanden in de repo worden ingesteld.

## About / metadata

1. Ga naar [https://github.com/mmaaart3n/ah-connect](https://github.com/mmaaart3n/ah-connect)
2. Klik op het **tandwiel-icoon** rechtsboven in het **About**-blok (onder de groene Code-knop)
3. Vul **Description** in:

   ```
   Home Assistant custom integration for Albert Heijn product search, shopping lists and receipt sensors.
   ```

4. **Website** (optioneel): leeg laten, of `https://github.com/mmaaart3n/ah-connect#readme`
5. Voeg **Topics** toe:

   - `home-assistant`
   - `homeassistant`
   - `hacs`
   - `hacs-integration`
   - `custom-component`
   - `albert-heijn`
   - `ah`
   - `shopping-list`

6. Klik **Save changes**

## Issues inschakelen

1. Ga naar **Settings → General**
2. Controleer dat **Issues** aan staat (standaard bij publieke repos)

## Actions valideren

1. Ga naar **Actions**
2. Open de workflow **Validate**
3. Klik **Re-run all jobs** (of wacht op de push na je metadata-wijziging)

Alle jobs moeten groen zijn:

- Run tests
- HACS validation
- Hassfest validation

## HACS custom repository testen

1. Open Home Assistant → **HACS → Integrations**
2. Drie puntjes → **Custom repositories**
3. Voeg toe:
   - **Repository URL:** `https://github.com/mmaaart3n/ah-connect`
   - **Category:** Integration
4. Zoek **AH Shopping**, installeer en herstart Home Assistant
5. **Instellingen → Apparaten & services → Integratie toevoegen → AH Shopping**

## Checklist na setup

- [ ] Description ingevuld
- [ ] Alle topics toegevoegd
- [ ] Validate workflow groen
- [ ] HACS custom repository toegevoegd
- [ ] Integratie geïnstalleerd en config flow werkt

## Veelvoorkomende HACS-validatiefouten

| Fout | Oplossing |
|------|-----------|
| Repository has no description | About → Description invullen (zie boven) |
| Repository has no valid topics | About → Topics toevoegen (zie boven) |
| Repository has no issues enabled | Settings → Issues aanzetten |
| Brand/icon missing | Controleer `custom_components/ah_shopping/brand/icon.png` |

## Opmerking

De map `brands/ah_shopping/icon.png` in deze repo is optioneel (legacy/brands-structuur). Home Assistant 2026.3+ gebruikt primair `custom_components/ah_shopping/brand/icon.png`.
