---
name: anime-trainer-builder
description: Procedimiento para crear entrenadores canonicos del anime en opponents.h y trainers.party sin romper compatibilidad de guardado.
---

# Creación de Entrenadores Canónicos del Anime

Sigue estos pasos exactos cada vez que añadas un entrenador de episodio, gimnasio o liga:

1. **Compatibilidad de partidas guardadas:**
   - **No modifiques** `MAX_TRAINERS_COUNT_EMERALD` (`950`) en `include/constants/opponents.h`.
   - Añade los nuevos `TRAINER_ANIME_*` usando los IDs correlativos libres inmediatamente posteriores al último entrenador definido.

2. **Definición en `src/data/trainers.party`:**
   - Respeta la sintaxis nativa de `pokeemerald-expansion`:
     ```text
     === TRAINER_ANIME_EJEMPLO ===
     Name: BROCK
     Class: Leader
     Pic: Brock
     Gender: Male
     Music: Male
     Double Battle: No
     AI: Check Bad Move | Try To Faint | Check Viability

     Onix
     Level: 14
     Ability: Rock Head
     IVs: 15 HP / 15 Atk / 15 Def / 15 SpA / 15 SpD / 15 Spe
     - Tackle
     - Bind
     - Rock Throw
     - Harden
     ```
   - Verifica antes en `src/data/trainers.party` o `include/constants/trainers.h` que los valores de `Class:` y `Pic:` existen en este build `-DEMERALD`.

3. **Invocación en scripts:**
   - Lanza el combate con `trainerbattle_no_intro_i18n TRAINER_ANIME_..., Text_ES, Text_EN, Text_PT, Text_IT` para que la frase de derrota en batalla salga en el idioma elegido por el jugador.
