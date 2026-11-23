---
name: phase-audit
description: Auditoria automatica pre-commit de textos i18n, flags, variables, compilacion make -j3 y tamano de ROM (< 32 MB).
---

# Auditoría Técnica de Fase

Ejecuta estas comprobaciones antes de dar por cerrada cualquier fase:

1. **Escaneo de caracteres prohibidos (`ã/õ`):**
   - Busca `[ãõÃÕ]` en los archivos modificados de `data/maps/` y `data/scripts/`. Si aparece alguno, corrígelo a `ao/oe/AO/OE`.

2. **Revisión de desbordamiento de texto:**
   - Comprueba en los textos `.string` añadidos que ninguna línea supere los 35 caracteres visibles antes de `\n`, `\l` o `\p`.

3. **Integridad de Flags y Variables:**
   - Verifica en `include/constants/flags.h` que no existan valores hexadecimales duplicados ni colisiones con `SYSTEM_FLAGS`.
   - Verifica en `include/constants/vars.h` que `VARS_END` no supere `0x40FF`.

4. **Compilación y límite de ROM:**
   - Ejecuta `make -j3` y confirma 0 errores.
   - Verifica en la salida del enlazador que el uso real de la región `ROM` sea inferior a `33.554.432` bytes (32 MB) y que `pokemon-anime-edition.gba` esté actualizado.
