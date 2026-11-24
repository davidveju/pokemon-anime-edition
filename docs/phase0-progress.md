# Pokémon Anime Edition — Progreso Fase 0 (arranque, multiidioma e intro)

> Última actualización: 2026-11-24
> Rama de desarrollo: `pokemon-anime-edition` (publicada en `origin`).
> Base: `master` = `origin/master` (`10e22cf91e`, Esmeralda prístina).
> ROM de referencia: `pokemon-anime-edition.gba` — **28.487.172 B usados (84,90 %)**, por debajo del límite de 32 MiB.

Este documento resume **qué está hecho, cómo está hecho y qué no debe romperse**.
Si algo de aquí se cambia, actualizar este archivo en el mismo commit.

---

## 1. Flujo de arranque actual

```
Boot GBA
  └─ Menú de idioma (ES / EN / PT / IT)        src/main_menu.c
      └─ Menú principal localizado (NUEVA PARTIDA / OPCIONES…)
          └─ NUEVA PARTIDA
              ├─ ya estamos en negro (el task espera !gPaletteFade.active)
              ├─ DestroyTask + FreeAllWindowBuffers
              ├─ gSelectedBootGender = MALE
              ├─ gSelectedBootName   = "ASH"
              └─ SetMainCallback2(CB2_NewGame)
                    └─ NewGameInitData()  (src/new_game.c)
                        ├─ WarpToTruck() → MAP_PALLET_TOWN_PLAYERS_HOUSE_2F (5,6)
                        ├─ resetea flags de mapa Hoenn + Kanto
                        ├─ fija género / nombre / idioma desde el boot
                        ├─ oculta Poké Balls y rival del laboratorio
                        ├─ desactiva el trigger de Oak del pueblo
                        └─ DoMapLoadLoop con gMain.state = 0
                              └─ Dormitorio 2F
                                  └─ mensaje "¡Son las 11:00! ¡Me he quedado dormido!"
```

**Decisiones cerradas (no revertir):**

1. **El discurso de Oak NO se usa en el arranque.** `src/oak_speech.c` sigue en el
   árbol, pero es una escena FRLG frágil con `IS_FRLG=0` y provocaba reinicios
   al encadenar con el warp. La entrada es directa a `CB2_NewGame`.
2. **Un solo origen de warp:** `WarpToTruck()` en `src/new_game.c`. No añadir
   warps en el flujo de arranque (nada de “doble warp”).
3. `CB2_NewGame()` fuerza `gMain.state = 0` antes de `DoMapLoadLoop()`
   (`src/overworld.c`). Sin esto se saltan pasos de carga del mapa.

---

## 2. Sistema multiidioma (ES / EN / PT / IT)

### 2.1 Almacenamiento
- 2 flags: `FLAG_ANIME_LANG_BIT0` (`0x493`) y `FLAG_ANIME_LANG_BIT1` (`0x494`).
  - `00` = ES, `01` = EN, `10` = PT, `11` = IT.
- API en `src/event_data.c` / `include/event_data.h`:
  - `u8 GetAnimeLanguage(void)`
  - `void SetAnimeLanguage(u8 lang)`
  - `const u8 *GetAnimeYesNoText(void)` → `SÍ/NO`, `YES/NO`, `SIM/NAO`, `SÌ/NO`
  - `const u8 *GetAnimeMoveOkBackText(void)` → barra del teclado de nombres

### 2.2 Textos de guion
- Macro `msgbox_i18n ES, EN, PT, IT` en `asm/macros/event.inc`.
- **Reglas obligatorias:**
  - Máximo **35 caracteres por línea** antes de `\n`, `\l` o `\p`.
  - Portugués **sin** `ã`, `õ`, `Ã`, `Õ` (bytes de control del motor): usar `ao` / `AO`.
    Sí se permiten `á`, `é`, `í`, `ó`, `ú`, `â`, `ê`, `ô` y mayúsculas con acento
    (`Í` = `0x5A` en `charmap.txt`).
- Los textos nuevos viven en los `scripts.inc` de cada mapa:
  - `PalletTown_Frlg` → textos compartidos de la escena de Oak.
  - `PalletTown_PlayersHouse_2F_Frlg` → mensaje de despertar tarde.
  - `PalletTown_PlayersHouse_1F_Frlg` → mamá.

### 2.3 Menús del motor
- **YES/NO**: `src/menu.c` usa `GetAnimeYesNoText()` en
  `CreateYesNoMenu()` y `CreateYesNoMenuAtPos()`. Esto cubre todos los
  `MSGBOX_YESNO` del juego (incluida la confirmación del nombre).
- **Barra del teclado de nombres**: `src/naming_screen.c` usa
  `GetAnimeMoveOkBackText()` (`MOVER/OK/VOLVER`, `MUOVI/OK/INDIETRO`…).
- Los botones gráficos `OK` / `BACK` / `Lower` / `Upper` del teclado son
  **gráficos**, no texto; traducirlos requiere arte nuevo (pendiente opcional).

### 2.4 Menú de Opciones
- Fila **IDIOMA / LANGUAGE** en `src/option_menu.c` (ya existía en Fase 0).
- Cambiar idioma actualiza flags + `gSelectedBootLanguage` y **repinta** el menú;
  al salir, el menú principal se reconstruye con el idioma nuevo.
- **Text speed**: se muestra solo el valor actual alineado a la derecha. Los tres
  valores ES/PT/IT no caben en la ventana (se probó y se desbordaba).

### 2.5 Selector de idioma al arrancar (pantalla azul corregida)
- `Task_AnimeBootLanguageSelect` (`src/main_menu.c`) se ejecuta tras el título y
  antes del menú principal.
- **Bug corregido:** la tarea usaba las ventanas 0/1 inicializadas con
  `sWindowTemplates_MainMenu` (26x2) en vez de `sWindowTemplates_AnimeBoot`
  (12x8); tampoco habilitaba `WINOUT` (BG0 quedaba oculto) ni cargaba los colores
  dinámicos 0xA/0xB/0xC del texto. El resultado era una pantalla azul sin menú.
- Correcciones aplicadas:
  - `InitWindows(sWindowTemplates_AnimeBoot)` antes de dibujar.
  - `WININ`/`WINOUT` con BG0 y OBJ visibles.
  - `LoadPalette` de 0xA (blanco), 0xB (gris oscuro) y 0xC (casi negro).
  - Al elegir idioma, `InitWindows(sWindowTemplates_MainMenu)` restaura las
    plantillas del menú principal antes de `Task_MainMenuCheckSaveFile`.
- Verificado en pantalla: las 4 opciones (Español/English/Português/Italiano) y
  el menú principal `NUEVA PARTIDA`/`OPCIONES` se ven correctamente.

---

## 3. Intro estilo anime (EP001)

### 3.0 Intro y título (estilo Amarillo)
- El splash de expansión encadena ahora **siempre** con el intro de FRLG
  (`CB2_SetUpIntroFrlg()` en `src/expansion_intro.c`), que muestra el combate
  **Gengar vs Nidorino** (el clásico de Gen 1 / Amarillo) y termina en
  `CB2_InitTitleScreen()`.
- No depende de `IS_FRLG`; el `.c` del intro FRLG ya se compilaba en Emerald.
- **Título (logo):** el antiguo banner de versión se retiró. El wordmark
  **Pokémon** y el óvalo **Pika!** se extrajeron del logo auténtico de Pokémon
  Amarillo (`pokemon_logo_source.png`) y se limpiaron de "YELLOW VERSION" y de
  cualquier texto de edición. El logo final es solo **Pokémon + Pika!**; el
  nombre del juego queda en el copyright inferior "© 2026 ANIME EDITION".
  `pokemon_logo.png` (256x64, paleta de 224 colores) se genera con
  `python3 dev_scripts/generate_title_logo.py`; el tilemap `pokemon_logo.bin`
  referencia los 256 tiles secuenciales de la imagen y deja el resto en el tile 0.
- **Título (fondo estilo Amarillo):** BG0 es un sunburst amarillo con el
  **Pikachu original** extraído de la imagen de referencia de Pokémon Amarillo,
  limpiado (fondo blanco fuera) y cuantizado a la paleta de 16 colores. BG1 son
  destellos animados que se desplazan sobre el fondo.
  - Assets: `graphics/title_screen/yellow_bg.png` (atlas 128x128 de 16x16 tiles),
    `yellow_bg.bin` (tilemap 32x32), `yellow_bg.pal` (banco 14),
    `sparkles.png/.bin` (BG1) y `pikachu_yellow.png` (128x88, índice 0
    transparente) como fuente del Pikachu.
  - Generador: `python3 dev_scripts/generate_title_bg.py`.
  - **Trampa del atlas:** el PNG de BG0 debe ser un **atlas de tiles**, no la
    escena completa: el build convierte los tiles en orden secuencial y una
    escena de 240x160 supera los 512 tiles del char base. El atlas 16x16 usa
    ~204 tiles únicos.
  - **Logo:** el BG2 se desplaza a `tBg2Y = -8` para dejar margen superior; la
    fase 3 **no** debe volver a poner `BG2Y` a 0 (eso cortaba el logo).
  - El antiguo `UpdateLegendaryMarkingColor()` sigue retirado; el índice 15 del
    banco 14 es el amarillo de Pikachu.
  - **“PRESS START” y copyright localizados:** `press_start_es/en/pt/it.png`
    (160x24, 5 segmentos de 32x8 para la frase + 5 para el copyright). Textos:
    `PULSA START`, `PRESS START`, `PRESSIONE START`, `PREMI START`; copyright
    común `© 2026 ANIME EDITION`.
    Generador: `python3 dev_scripts/generate_title_press_start.py`.
    La hoja se elige con `gSelectedBootLanguage` (0..3; por defecto ES en el
    primer arranque, porque el título se muestra antes del selector de idioma).

### 3.1 Dormitorio (2F)
- Spawn: `MAP_PALLET_TOWN_PLAYERS_HOUSE_2F` en `(5,6)`.
- `PalletTown_PlayersHouse_2F_OnFrame` (var `VAR_MAP_SCENE_PALLET_TOWN_PLAYERS_HOUSE_2F`):
  - `0` → OnWarp gira al jugador al norte y pone la var a `1`.
  - `1` → mensaje **“¡Son las 11:00! ¡Me he quedado dormido!”** y var a `2`.

### 3.2 Planta baja (mamá)
- `PalletTown_PlayersHouse_1F_EventScript_Mom` usa `msgbox_i18n`:
  “todos los chicos ya se han ido a por su primer Pokémon; el Prof. Oak te espera
  en el laboratorio”.
- Mamá (gráfico FRLG) ya se renderiza correctamente tras el arreglo de assets.

### 3.3 Pueblo Paleta
- Oak **no** aparece en la calle: `FLAG_HIDE_OAK_IN_PALLET_TOWN`.
- El trigger vanilla de la salida norte queda desactivado con
  `VarSet(VAR_MAP_SCENE_PALLET_TOWN_OAK, 1)` en `NewGameInitData()`.
  (Si se deja en 0, se dispara la escena vanilla de los 3 starters.)

### 3.4 Laboratorio de Oak
- Oak colocado en `(6,10)`, `MOVEMENT_TYPE_FACE_DOWN` (`map.json`).
- `PalletTown_ProfessorOaksLab_OnFrame` (var `VAR_MAP_SCENE_PALLET_TOWN_PROFESSOR_OAKS_LAB`):
  - `0` → `PalletTown_ProfessorOaksLab_EventScript_AnimePikachuIntro`:
    ```
    lockall / delay 16 / turnobject PLAYER, NORTH
    msgbox_i18n "llegas tarde, todos ya han venido, solo queda este Pikachu,
                 es un poco especial..."
    givemon SPECIES_PIKACHU, 5
    playfanfare MUS_LEVEL_UP
    msgbox_i18n "¡Pikachu ha rechazado la Poké Ball! Pero parece que te ha elegido a ti."
    waitfanfare / closemessage
    setflag FLAG_SYS_POKEMON_GET
    setflag FLAG_ANIME_PIKACHU_RECEIVED
    setflag FLAG_ANIME_PIKACHU_CANNOT_EVOLVE
    setflag FLAG_ANIME_PIKACHU_CANNOT_DEPOSIT
    setvar VAR_MAP_SCENE_PALLET_TOWN_PROFESSOR_OAKS_LAB, 9
    setvar VAR_MAP_SCENE_PALLET_TOWN_OAK, 1
    releaseall / end
    ```
  - `9` no coincide con ninguna entrada vanilla → no se dispara la escena
    original de elección de starter.
- La mesa aparece **vacía** (sin las 3 Poké Balls) y el rival **no está**.
- Tras la entrega, Pikachu **sigue al jugador** (sistema de followers).

### 3.5 Flags nuevas (antes `0`, ahora reales)

| Constante | Valor | Efecto |
| --- | --- | --- |
| `FLAG_HIDE_BULBASAUR_BALL` | `0x49B` | oculta la Poké Ball de Bulbasaur |
| `FLAG_HIDE_SQUIRTLE_BALL` | `0x49C` | oculta la de Squirtle |
| `FLAG_HIDE_CHARMANDER_BALL` | `0x49D` | oculta la de Charmander |
| `FLAG_HIDE_RIVAL_IN_LAB` | `0x49E` | oculta al rival (ya se fue) |
| `FLAG_HIDE_OAK_IN_PALLET_TOWN` | `0x49F` | Oak solo en el laboratorio |

Se activan en `NewGameInitData()` **después** de los resets de flags.

> **Aviso:** estos flags estaban *stubbeados a `0`* (siempre visibles). No
> volver a ponerlos a `0`: reaparecerían las bolas/rival y Oak en la calle.

---

## 4. Correcciones críticas del motor (NO REVERTIR)

### 4.1 Assets de overworld FRLG en build Emerald
**Síntoma:** el juego se reiniciaba al cargar Pueblo Paleta o el laboratorio.
**Causa:** estos recursos estaban dentro de `#if IS_FRLG`, así que con
`-DEMERALD` **no se compilaban** y la tabla de punteros quedaba con huecos
`NULL`; al spawnear un NPC FRLG se desreferenciaba NULL.
**Arreglo (commit actual):** compilar esos bloques también en Emerald, quitando
el guard en:
- `src/data/object_events/object_event_graphics.h`
- `src/data/object_events/object_event_pic_tables.h`
- `src/data/object_events/object_event_graphics_info.h`
- `src/data/object_events/object_event_graphics_info_pointers.h`
- `src/event_object_movement.c` (paletas `OBJ_EVENT_PAL_TAG_*` FRLG)

**Prueba del arreglo:** `tools/anime-debug/boottest.py` informa `FIELD OK` para
Pueblo Paleta `(0,37)` y laboratorio `(3,38)`; Oak, mamá, ayudantes y la señora
del cartel se dibujan correctamente.

### 4.2 `gMain.state` en `CB2_NewGame`
`src/overworld.c`: `gMain.state = 0;` antes de `DoMapLoadLoop()`.
Sin esto se arranca la carga del mapa en un paso avanzado y se saltan
`LoadMapFromWarp`, objetos y cámara.

### 4.3 Prefill del nombre
`src/naming_screen.c`: `sPlayerNamingScreenTemplate.copyExistingString = TRUE`
para que el nombre pre-rellenado (`ASH` / `HOJA`) se vea y se pueda editar.

---

## 5. Herramientas de depuración (sin capturas)

Ver `docs/anime-debug.md`. Resumen:
- `tools/anime-debug/rsp.py`: cliente RSP mínimo para el stub GDB de mGBA
  (`mgba-qt -g`), carga símbolos de `pokeemerald.map`, lee memoria/registros,
  pone breakpoints.
- `tools/anime-debug/boottest.py`: oráculo de arranque (`FIELD OK` / crash).
- `tools/anime-debug/watch.py <símbolo>`: corre el juego y para en un símbolo.
- `tools/anime-debug/verify.py`: volcado de flags/vars de la Fase 0.

**Offsets correctos (verificados por disassembly):**
- `flags[]` → `SaveBlock1 + 0x1270`
- `vars[]`  → `SaveBlock1 + 0x13A8`  ← **no** `0x139C`
- `gMain.state` → `gMain + 0x438`; `callback2` → `gMain + 0x04`

**Trampas del stub:**
- mGBA pausa al desconectar; para dejar correr hay que mantener la conexión.
- No soporta interrupción (`\x03`): se para con breakpoint.
- Las teclas deben inyectarse **con el CPU corriendo**; si está parado en un
  breakpoint, el `keydown/keyup` se pierde.
- `ScrCmd_setvar` **no** llama a `VarSet`.

---

## 6. Verificaciones realizadas

| Prueba | Resultado |
| --- | --- |
| Arranque sin discurso de Oak | `FIELD OK map=(1,38) pos=(5,6)` (dormitorio 2F) |
| Pueblo Paleta con NPCs FRLG | `FIELD OK map=(0,37) pos=(10,9)` |
| Laboratorio con NPCs FRLG | `FIELD OK map=(3,38) pos=(6,11)` |
| Guion de intro del laboratorio | breakpoint en `ScrCmd_lockall` alcanzado |
| Entrega de Pikachu | `party=1`; Pikachu visible siguiendo al jugador |
| Escaleras 2F → 1F | OK |
| Salida 1F → Pueblo Paleta | OK (antes reiniciaba) |
| Mamá / Oak / ayudantes / señora | visibles y con sprites correctos |
| Menú YES/NO | `SÍ/NO` (ES) verificado en pantalla |
| Barra del teclado de nombres | `MOVER OK VOLVER` verificada |
| Selector de idioma al arrancar | 4 opciones visibles y seleccionables (ES/EN/PT/IT) |
| Menú principal tras idioma | `NUEVA PARTIDA` / `OPCIONES` visibles (ES) |
| Título estilo Amarillo | Pikachu y logo auténticos de Amarillo + “PULSA START” verificados |
| Tamaño de ROM | 28.487.172 B usados (84,90 %) |

---

## 7. Pendientes conocidos

1. **Recorrido completo a pie** dormitorio → 1F → pueblo → puerta del
   laboratorio → intro (la lógica está verificada por separado; falta el
   paseo completo en una sesión limpia).
2. Textos vanilla que siguen en inglés y no forman parte del flujo nuevo:
   - cartel del dormitorio (`It's a posted notice…`),
   - diálogo de curación de mamá (tras la primera batalla del rival),
   - diálogos de los ayudantes del laboratorio y carteles del pueblo.
3. Traducir los **botones gráficos** del teclado de nombres (`OK`, `BACK`,
   `Lower/Upper`) requeriría arte nuevo.
4. Revisar si el `OnFrame` de la intro del laboratorio debe además fijar
   `FLAG_SYS_POKEDEX_GET` cuando se implemente la Pokédex.

---

## 8. Checklist anti-regresión

Antes de tocar arranque, mapas de Kanto o multiidioma:

- [ ] `WarpToTruck()` sigue siendo el **único** warp de nueva partida → 2F `(5,6)`.
- [ ] El arranque **no** llama a `StartNewGameSceneAnime()` / `oak_speech.c`.
- [ ] `CB2_NewGame()` mantiene `gMain.state = 0` antes de `DoMapLoadLoop()`.
- [ ] Los assets FRLG de overworld siguen **fuera** de `#if IS_FRLG`.
- [ ] Las flags `0x49B–0x49F` siguen siendo reales y se activan en `NewGameInitData()`.
- [ ] El laboratorio mantiene `VAR_MAP_SCENE_..._LAB = 9` al terminar la intro
      (no `1`, que dispara la escena vanilla de starters).
- [ ] `VAR_MAP_SCENE_PALLET_TOWN_OAK = 1` al iniciar (evita el trigger del pueblo).
- [ ] Textos: ≤35 caracteres por línea y sin `ã/õ/Ã/Õ` en portugués.
- [ ] `make -j3` sin errores/warnings nuevos y ROM usada < 32 MiB.
- [ ] Tras compilar, `python3 tools/anime-debug/boottest.py` → `FIELD OK`.

---

## 9. Auditoría de cambios del fork (`10e22cf91e..HEAD`) — 2026-11-24

**Alcance:** 5 commits nuestros (`32bb7793cb`, `a8b5662d9e`, `3024c86776`,
`9fe3c32b88`, `28f28e588f`).

### 9.1 Ruido de fin de línea (corregido)
- 110 archivos aparecían cambiados; **61 eran solo EOL/espacios** (contenido
  idéntico al normalizar CRLF→LF), arrastrados por el editor en `3024c86776`
  (scripts de migración, `dev_scripts/`, licencias de `tools/`, `.all-contributorsrc`, `docs/book.toml`…).
- **Acción:** revertidos esos 61 a la versión de `10e22cf91e`. El diff del fork
  queda solo con cambios reales.

### 9.2 Flags duplicadas (corregido)
- Las 5 flags nuevas convivían con sus `FLAG_UNUSED_0x49B..0x49F` (mismo valor).
- **Acción:** eliminadas las definiciones `FLAG_UNUSED_0x49x`. Ahora
  `0x493–0x49F` son únicas (verificado por script).

### 9.3 Textos (OK)
- 0 caracteres `ã/õ/Ã/Õ` en los `.inc` modificados.
- 0 líneas visibles > 35 caracteres (contando `{PLAYER}` como 3 y `{RIVAL}` como 4).

### 9.4 Variables (OK)
- `VARS_END = 0x40FF`; no se añadieron variables nuevas.

### 9.5 Compilación y pruebas (OK)
- `make -j3`: 0 errores / 0 warnings.
- `make -j3 pokeemerald-test.elf`: enlaza correctamente (incluye el cambio de `test/text.c`).
- ROM usada: **28.487.172 B (84,90 %)**.
- `tools/anime-debug/boottest.py`: `FIELD OK map=(1,38) pos=(5,6)`.

### 9.6 Riesgo preexistente detectado (no corregido aún)
- Cientos de flags `FLAG_HIDE_*` de FRLG siguen **stubbeadas a `0`** (heredado
  del port). Con `flagId = 0` los objetos están siempre visibles; en las fases
  de Kanto habrá que reasignarlas a flags libres (como se hizo con las 5 del
  arranque: `0x49B–0x49F`).
- `src/main_menu.c` ya no referencia `StartNewGameSceneAnime`; `src/oak_speech.c`
  queda compilado pero fuera del flujo (no borrar sin revisar `include/oak_speech.h`).

---

## 10. Gestión de flags `unused` (obligatorio al tocar Kanto)

Herramienta:
```bash
python3 tools/anime-debug/audit_flags.py
```
Informa de:
1. **Duplicados** (mismo valor con varios nombres).
2. **Flags usadas por mapas pero a `0`** (objetos siempre visibles). Hoy: **292**.
3. **`FLAG_UNUSED_*` libres** (<0x500, sin referencias). Hoy: **222**.

Procedimiento al añadir/tocar un mapa con `object_event` que use `FLAG_HIDE_*`:
1. Ejecutar la auditoría y comprobar si esa flag vale `0`.
2. Si vale `0`, reasignarla en `include/constants/flags.h` a una `FLAG_UNUSED_0xNNN`
   libre (no referenciada por nadie) y **borrar** la definición `FLAG_UNUSED` para
   evitar nombres duplicados.
3. Activarla donde corresponda (normalmente `NewGameInitData()` si debe estar
   oculta desde el inicio, o el `OnTransition` del mapa si es estado de escena).
4. Verificar: `audit_flags.py` sin duplicados para el valor y
   `python3 tools/anime-debug/boottest.py` con el mapa cargando.

Hecho hasta ahora: `0x49B–0x49F` (Poké Balls de starter, rival del laboratorio
y Oak en la calle).

---

## 11. Estrategia de ramas

- **`master`** = espejo de `origin/master` (base del fork, `10e22cf91e`). Solo se
  usa para traer cambios del fork original:
  ```bash
  git switch master && git pull
  ```
- **`pokemon-anime-edition`** = rama del proyecto (el juego completo que estamos
  construyendo sobre la base de Esmeralda). Publicada como
  `origin/pokemon-anime-edition`.
- Flujo recomendado:
  1. Trabajar y commitear en `pokemon-anime-edition`.
  2. Al actualizar el fork: `git switch master && git pull`, luego
     `git switch pokemon-anime-edition && git merge master` (o rebase si no está publicada).
  3. No commitear directamente en `master` para que el pull del fork sea limpio.

---

## 12. Comandos de verificación rápida

```bash
# compilación + ROM
make -j3
make -j3 pokeemerald-test.elf          # valida el arnés de test/
cp pokeemerald.gba pokemon-anime-edition.gba

# arranque sano (cierra mGBA al terminar)
python3 tools/anime-debug/boottest.py

# integridad de flags
python3 tools/anime-debug/audit_flags.py

# depuración puntual
python3 tools/anime-debug/watch.py ScrCmd_createmon 60 x
```
