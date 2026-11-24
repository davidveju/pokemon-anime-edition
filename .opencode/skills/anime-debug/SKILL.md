---
name: anime-debug
description: Depurar Pokémon Anime Edition en memoria (mapa, posición, equipo, flags y vars) con el GDB stub de mGBA, sin interpretar capturas.
---

# Depuración en memoria (mGBA GDB stub)

Usa esta skill cuando necesites comprobar el estado real del juego tras
compilar: si un mapa carga, en qué tile está el jugador, si se ejecutó un
guion, si se dieron flags o si el equipo tiene a Pikachu.

## Herramientas (`tools/anime-debug/`)

| Comando | Para qué |
| --- | --- |
| `python3 tools/anime-debug/boottest.py [seg]` | Oráculo de arranque: pulsa A y comprueba si se alcanzó `CB2_Overworld`. Imprime `FIELD OK map=... pos=... party=...` o `NO FIELD`. Cierra mGBA al terminar (`--keep` para dejarlo). |
| `python3 tools/anime-debug/audit_flags.py` | Duplicados de flags, flags usadas por mapas que siguen a `0` y `FLAG_UNUSED` libres. |
| `python3 tools/anime-debug/watch.py <símbolo> [seg] [tecla]` | Corre el juego y para en un breakpoint de símbolo, mostrando `pc/lr`, `cb2`, mapa, posición y party. |
| `python3 tools/anime-debug/rsp.py` | Cliente RSP: `state()`, `read/u8/u16/u32`, `ptr(sym)`, `regs()`, breakpoints. |

## Flujo típico

```bash
# 1. Compilar y copiar la ROM
make -j3 && cp pokeemerald.gba pokemon-anime-edition.gba

# 2. ¿Arranca y llega al campo?
python3 tools/anime-debug/boottest.py 45

# 3. ¿El guion del laboratorio entrega a Pikachu?
python3 tools/anime-debug/watch.py ScrCmd_createmon 60 x

# 4. Leer estado tras una secuencia
python3 - <<'PY'
import sys; sys.path.insert(0,'tools/anime-debug'); import rsp as R
syms=R.load_symbols(); r=R.RSP()
R.sync(r,syms)
sb1=r.ptr(syms['gSaveBlock1Ptr'])
print('map', (r.u8(sb1+5), r.u8(sb1+4)), 'pos', (r.s16(sb1), r.s16(sb1+2)))
print('party', r.u8(syms['gPartiesCount']))
r.close()
PY
```

## Offsets correctos (verificados por disassembly)

- `SaveBlock1`: `pos` en `+0x00/+0x02`; `location.mapGroup` en `+0x04`,
  `mapNum` en `+0x05`.
- `flags[]` → `SaveBlock1 + 0x1270`.
- `vars[]`  → `SaveBlock1 + 0x13A8` (**no** 0x139C), índice = `var - 0x4000`.
- `gMain.state` → `gMain + 0x438`; `callback2` → `gMain + 0x04`.

## Trampas del stub

1. mGBA **pausa la emulación al desconectar**; si dejas la ventana abierta se
   queda en negro. Por eso `boottest.py` cierra el emulador salvo `--keep`.
2. No soporta interrupción (`\x03`): para parar, breakpoint.
3. Las teclas deben inyectarse **con el CPU corriendo**; si está parado en un
   breakpoint, `keydown`+`keyup` se pierde.
4. `ScrCmd_setvar` escribe con `GetVarPointer` y **no** llama a `VarSet`.
5. Un breakpoint por frame (`RunTasks`) sirve para inspeccionar, pero es lento
   (~4 fps). Para pruebas de flujo usa breakpoints de evento.
6. Cierra siempre los breakpoints (`z0,<addr>,2`) antes de terminar.
