# Pokémon Anime Edition — Guía de Arquitectura y Reglas Técnicas

## Objetivo y Compilación
- ROM hack de larga duración basado en `pokeemerald-expansion` (`-DEMERALD`, `IS_FRLG=0`) con soporte multiidioma en tiempo real (`ES`, `EN`, `PT`, `IT`) y episodios jugables fieles al anime (Kanto, Liga Añil, Islas Naranja y Johto).
- Compilar siempre con `make -j3` tras cada fase.
- La ROM (`pokemon-anime-edition.gba`) **no debe superar los 32 MB (33.554.432 bytes)**. Si al combinar regiones se acerca al límite, recortar grupos de mapas no utilizados de Hoenn (como Battle Frontier) manteniendo íntegros Kanto/Sevii y Johto.
- **No inspeccionar** nunca `graphics/`, `sound/`, `tools/bin2c` ni `build/`.

## Trampas Conocidas del Motor (`pokeemerald-expansion`)
1. **Mapas y layouts FRLG (`tools/mapjson/mapjson.cpp`):**
   - Por defecto, `mapjson` excluye mapas con `region != REGION_HOENN` (todos los `*_Frlg`) y layouts con `layout_version != emerald`.
   - Habilitar la generación combinada Hoenn + Kanto en `tools/mapjson/mapjson.cpp` y recompilar `tools/mapjson/mapjson`.
   - En `NewGameInitData()` (`src/new_game.c`), ejecutar tanto `EventScript_ResetAllMapFlags` como `EventScript_ResetAllMapFlagsFrlg`.
   - En `include/constants/flags.h`, reasignar los `FLAG_HIDDEN_ITEM_*` de FRLG stubbed a `0` hacia flags libres reales `>= FLAG_HIDDEN_ITEMS_START` sin colisionar con trainer flags.
2. **Arranque en Nueva Partida (`src/main_menu.c`, `src/new_game.c`):**
   - En `src/main_menu.c`, hacer primero el fundido a negro (`BeginNormalPaletteFade`), esperar `!gPaletteFade.active` en una tarea y solo entonces llamar a `SetMainCallback2(CB2_NewGame)` (saltando la intro de Abedul/Birch).
   - En `NewGameInitData()` y `WarpToTruck()`, inicializar `playerName = "ASH"`, `playerGender = MALE` y `rivalName = "GARY"`, y hacer warp incondicional a `MAP_PALLET_TOWN` (`PalletTown_Frlg`) en coordenadas caminables verificadas en su `map.json`.
   - En `PalletTown_Frlg/scripts.inc`, usar `delay 16` (nunca `waitstate` sin tarea en C) en `MAP_SCRIPT_ON_FRAME_TABLE` antes del `dynmultichoice` inicial para que la pantalla termine de aclararse.
3. **Variables y Entrenadores:**
   - **No añadir variables** por encima de `VARS_END` (`0x40FF`) en `include/constants/vars.h`; gestionar la historia con flags libres en `include/constants/flags.h`.
   - Fijar `MAX_TRAINERS_COUNT_EMERALD` en `950` (`include/constants/opponents.h`) desde la Fase 0 para no desplazar `SYSTEM_FLAGS` ni romper partidas guardadas en fases posteriores.

## Sistema Multiidioma (`ES / EN / PT / IT`)
- Codificar el idioma en 2 flags libres (`FLAG_ANIME_LANG_BIT0` y `FLAG_ANIME_LANG_BIT1`: `00`=ES, `01`=EN, `10`=PT, `11`=IT) y exponer `GetAnimeLanguage()` (0..3) en `src/event_data.c` / `include/event_data.h`.
- Definir macros `msgbox_i18n` y `trainerbattle_no_intro_i18n` en `asm/macros/event.inc` usando etiquetas locales `\@`.
- **Regla crítica de `charmap.txt`:** Los bytes `0xF8`–`0xFB` son prefijos de códigos de control del motor. **Nunca** escribir `ã`, `õ`, `Ã` ni `Õ` en los textos en portugués; sustituirlos siempre por `ao` / `AO`.
- **Longitud de texto:** Máximo **35 caracteres** por línea antes de `\n`, `\l` o `\p`.

## Mecánicas Canónicas del Anime en C
- **Follower Pikachu (`include/config/overworld.h`, `src/event_object_movement.c`):** Activar `OW_FOLLOWERS_ENABLED`; `GetFollowerMon()` devuelve únicamente un `SPECIES_PIKACHU` vivo del jugador cuando `FLAG_ANIME_PIKACHU_RECEIVED` está activo (y `FLAG_ANIME_FOLLOWERS_DISABLED` inactivo).
- **Bloqueo de evolución (`src/pokemon.c`):** En `GetEvolutionTargetSpecies()`, impedir que Pikachu evolucione con `ITEM_THUNDER_STONE` mientras `FLAG_ANIME_PIKACHU_CANNOT_EVOLVE` esté activa.
- **Bloqueo de PC (`src/pokemon_storage_system.c`):** Impedir depositar el Pikachu inicial mientras `FLAG_ANIME_PIKACHU_CANNOT_DEPOSIT` esté activa, mostrando el mensaje en los 4 idiomas mediante `GetAnimeLanguage()`.
- **Desobediencia (`src/battle_util.c`):** En `GetAttackerObedienceForAction()`, solo para `B_SIDE_PLAYER`, Pikachu desobedece mientras `FLAG_ANIME_PIKACHU_OBEDIENT` no esté activa, y Charmeleon/Charizard desobedecen mientras `FLAG_ANIME_CHARIZARD_OBEDIENT` no esté activa.

## Recursos Gráficos FRLG en Build Emerald (`-DEMERALD`)
- **Nunca** vuelvas a encerrar tras `#if IS_FRLG` los recursos de overworld FRLG (`object_event_graphics.h`, `object_event_pic_tables.h`, `object_event_graphics_info.h`, `object_event_graphics_info_pointers.h` y las paletas en `src/event_object_movement.c`); dejar huecos `NULL` en la tabla de punteros provoca un reinicio inmediato al spawnear NPCs de Kanto.
- Usa `tools/anime-debug/` (según `docs/anime-debug.md`) para verificar en memoria coordenadas, flags y equipo tras compilar.

## Estado y Reglas de Arranque (Fase 0)
> Documento detallado: **`docs/phase0-progress.md`** (leer antes de tocar el arranque, Kanto o el multiidioma).

- **Sin discurso de Oak en el arranque:** `src/oak_speech.c` queda fuera del flujo de nueva partida (escena FRLG frágil con `IS_FRLG=0`). El botón NUEVA PARTIDA hace `fade` → `SetMainCallback2(CB2_NewGame)` con `gSelectedBootGender`/`gSelectedBootName` ya fijados.
- **Un único warp de nueva partida:** `WarpToTruck()` en `src/new_game.c` → `MAP_PALLET_TOWN_PLAYERS_HOUSE_2F` en `(5,6)`. No añadir otros warps en el arranque (el “doble warp” con OakSpeech causaba reinicios).
- **`CB2_NewGame()`:** mantener `gMain.state = 0;` antes de `DoMapLoadLoop()` (`src/overworld.c`).
- **Flags 0x49B–0x49F:** `FLAG_HIDE_BULBASAUR_BALL`, `..._SQUIRTLE_BALL`, `..._CHARMANDER_BALL`, `FLAG_HIDE_RIVAL_IN_LAB` y `FLAG_HIDE_OAK_IN_PALLET_TOWN` son flags reales y se activan en `NewGameInitData()` (antes estaban stubbeadas a `0` y los objetos aparecían siempre).
- **Escena del laboratorio:** `VAR_MAP_SCENE_PALLET_TOWN_PROFESSOR_OAKS_LAB` pasa a `9` al entregar a Pikachu (nunca a `1`, que dispara la escena vanilla de los 3 starters) y `VAR_MAP_SCENE_PALLET_TOWN_OAK` se fija a `1` para desactivar el trigger de Oak del pueblo.
- **Multiidioma de menús:** `GetAnimeYesNoText()` (`SÍ/NO`, `YES/NO`, `SIM/NAO`, `SÌ/NO`) y `GetAnimeMoveOkBackText()` viven en `src/event_data.c`; `src/menu.c` y `src/naming_screen.c` los consumen.
