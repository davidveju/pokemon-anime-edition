# Depuración rápida sin capturas (GDB stub de mGBA)

Esta guía describe cómo inspeccionar el estado real del juego (mapa, posición,
party, flags y variables) **sin interpretar imágenes**, usando el stub GDB
antiguo de mGBA (`mgba-qt -g`) y un cliente RSP mínimo en Python.

## Por qué no se usa `gdb`

`gdb`/`gdb-multiarch` negocian `qSupported`/`vMustReplyEmpty` y el stub de
mGBA 0.10.5 no responde como espera. Un cliente RSP propio evita esa
negociación y habla el protocolo mínimo (`m`, `M`, `g`, `Z0`, `c`, `s`).

## Requisitos

```bash
Xvfb :99 -screen 0 1280x800x24 &
DISPLAY=:99 mgba-qt -g pokemon-anime-edition.gba &
```

El stub escucha en `127.0.0.1:2345`.

## Herramientas

- `tools/anime-debug/rsp.py`
  - `state()`: para el CPU en el siguiente frame (`RunTasks`) y devuelve
    `cb1/cb2`, `gMain.state`, punteros de SaveBlock, `pos`, `map`, `party`.
  - `read(addr, len)`, `u8/u16/u32`, `ptr(sym)`, `reg(name)`.
  - Carga símbolos de `pokeemerald.map` (sin necesidad de `.elf`).
- `tools/anime-debug/watch.py <símbolo> [segundos] [tecla]`
  - Deja correr el juego a velocidad real, inyecta teclas con `xdotool`
    (mantiene Tab = fast-forward) y para al alcanzar un breakpoint en el
    símbolo indicado, imprimiendo `pc/lr`, `cb2`, mapa, posición y party.
- `tools/anime-debug/verify.py`
  - Breakpoint en `VarSet`, filtra por `VAR_MAP_SCENE_PALLET_TOWN_PROFESSOR_OAKS_LAB`
    y vuelca los flags de la Fase 0 y las variables del guion.

## Direcciones y offsets útiles

| Dato | Cómo obtenerlo |
| --- | --- |
| Símbolo | `pokeemerald.map` (líneas `0xADDR  nombre`) |
| `SaveBlock1` | `gSaveBlock1Ptr` (puntero) |
| `pos` (x, y) | `SaveBlock1 + 0x00` / `+0x02` (s16) |
| mapa (grupo, num) | `SaveBlock1 + 0x04` (s8, grupo) / `+0x05` (num) |
| `location` x/y | `SaveBlock1 + 0x08` / `+0x0A` |
| `flags[]` | `SaveBlock1 + 0x1270` |
| `vars[]` | `SaveBlock1 + 0x139C` (índice = var - 0x4000) |
| `gMain.state` | `gMain + 0x438` (u8) |
| `callback2` | `gMain + 0x04` |

Flags de la Fase 0: `FLAG_ANIME_LANG_BIT0/1` = `0x493/0x494`,
`FLAG_ANIME_PIKACHU_RECEIVED` = `0x495`, `..._CANNOT_EVOLVE` = `0x496`,
`..._CANNOT_DEPOSIT` = `0x497`.

## Notas

- El stub **pausa la emulación al desconectar**, así que para dejar correr el
  juego hay que mantener la conexión abierta mientras se ejecuta `c`.
- Un breakpoint por frame (`RunTasks`) sirve para inspeccionar, pero es lento
  (~4 fps por round-trip). Para pruebas de flujo usa breakpoints de evento
  (`ScrCmd_createmon`, `VarSet`, `CB2_Overworld`, ...).
- Cerrar siempre con `z0,<addr>,2` para no dejar breakpoints activos.
