---
name: phase-audit
description: Auditoría pre-commit de textos i18n, flags unused, assets FRLG, compilación make -j3, tests y tamaño de ROM (< 32 MB).
---

# Auditoría Técnica de Fase

Ejecuta estas comprobaciones antes de dar por cerrada cualquier fase.

1. **Caracteres prohibidos (`ã/õ`):**
   - Busca `[ãõÃÕ]` en los archivos modificados de `data/maps/` y `data/scripts/`.
   - Si aparece alguno, corrígelo a `ao/oe/AO/OE`.

2. **Longitud de texto:**
   - Ninguna línea `.string` añadida debe superar **35 caracteres visibles**
     antes de `\n`, `\l` o `\p` (cuenta `{PLAYER}` como 3 y `{RIVAL}` como 4).

3. **Flags y variables:**
   - Ejecuta `python3 tools/anime-debug/audit_flags.py`:
     - **sin duplicados** (mismo valor, varios nombres);
     - ninguna flag usada por un `object_event` debe quedarse a `0`;
     - al reasignar, usar `FLAG_UNUSED_0xNNN` libre y **borrar** su definición
       `FLAG_UNUSED` para no dejar duplicados.
   - `VARS_END` no debe superar `0x40FF` (`include/constants/vars.h`).

4. **Assets FRLG (build Emerald):**
   - Los recursos de overworld FRLG deben seguir **fuera** de `#if IS_FRLG`
     (`object_event_graphics.h`, `object_event_pic_tables.h`,
     `object_event_graphics_info.h`, `object_event_graphics_info_pointers.h`
     y las paletas en `src/event_object_movement.c`). Volver a encerrarlos deja
     punteros `NULL` y reinicia el juego al spawnear NPCs de Kanto.

5. **Compilación y ROM:**
   - `make -j3` → 0 errores y 0 warnings nuevos.
   - `make -j3 pokeemerald-test.elf` → el arnés de tests enlaza (valida `test/`).
   - Uso real de la región `ROM` < `33.554.432` bytes (32 MB).
   - `cp pokeemerald.gba pokemon-anime-edition.gba` para dejar la ROM de prueba al día.

6. **Verificación funcional:**
   - `python3 tools/anime-debug/boottest.py` → `FIELD OK` (el arranque llega al campo).
   - Si el cambio toca un guion/mapa concreto, verificarlo con
     `tools/anime-debug/watch.py <símbolo>` o leyendo el estado con `rsp.py`.

7. **Rama y documentación:**
   - Commitear en `pokemon-anime-edition` (nunca en `master`, que es la base del fork).
   - Actualizar `docs/phase0-progress.md` si cambia el arranque, Kanto o el multiidioma.

8. **Título:**
   - Si se toca el banner, regenerarlo con `dev_scripts/generate_title_version.py`.
   - Si se toca el fondo BG0, regenerarlo con `dev_scripts/generate_title_bg.py`.
     El PNG de `kanto.png` debe seguir siendo un **atlas 16x16**; una escena
     completa de 240x160 desborda los 512 tiles del char base y rompe el
     tilemap.
   - Si se toca “PRESS START”/copyright, regenerar las 4 hojas con
     `dev_scripts/generate_title_press_start.py`.

9. **Selector de idioma al arrancar:**
   - Debe mostrar las 4 opciones y, al elegir, el menú principal. Comprobar
     `InitWindows(sWindowTemplates_AnimeBoot)`, `WINOUT` con BG0+OBJ y los
     colores 0xA/0xB/0xC; si falta, la pantalla queda azul.
