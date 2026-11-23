---
name: anime-i18n-script
description: Reglas estrictas para escribir scripts de episodios, dialogos en 4 idiomas (ES/EN/PT/IT) y coord_events seguros en Pokemon Anime Edition.
---

# Reglas para Scripts de Episodios y Multiidioma (`ES / EN / PT / IT`)

Aplica estas reglas siempre que edites o crees archivos en `data/maps/` o `data/scripts/`:

1. **Macros obligatorias:**
   - Usa siempre `msgbox_i18n` para diálogos y `trainerbattle_no_intro_i18n` para combates del anime (nunca `msgbox` ni `trainerbattle_no_intro` en texto plano de un solo idioma).
   - Mantén el orden de idiomas: `ES`, `EN`, `PT`, `IT`.

2. **Codificación `charmap.txt` (crítico):**
   - Los bytes `0xF8`–`0xFB` son códigos de control del motor.
   - **Prohibido** usar `ã`, `õ`, `Ã` o `Õ` en los textos en portugués; reemplázalos siempre por `ao`, `oe`, `AO`, `OE` (ej. `nao`, `emocao`, `coracoes`).

3. **Longitud de línea (máx. 35 caracteres):**
   - Ninguna línea de texto visible puede superar los **35 caracteres** antes de `\n`, `\l` o `\p`.
   - Cuenta los placeholders como `{PLAYER}` o `{STR_VAR_1}` como 8 caracteres para dejar margen seguro.

4. **Seguridad en `map.json` y `coord_events`:**
   - Antes de colocar un NPC o un `coord_event`, lee el `map.json` del mapa para verificar coordenadas caminables y evitar bloquear puertas o pasillos estrechos.
   - Todo `coord_event` debe comprobar un flag al inicio (`goto_if_set FLAG_..., Common_EventScript_NopReturn`) y activarlo antes de terminar para evitar bucles infinitos.
   - Equilibra siempre `lock`/`lockall` con `release`/`releaseall` en todas las ramas del script.
