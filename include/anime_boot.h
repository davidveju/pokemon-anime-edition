#ifndef GUARD_ANIME_BOOT_H
#define GUARD_ANIME_BOOT_H

#include "global.h"

// Selections made in the main menu boot flow before a new game (Phase 0).
// gSelectedBootLanguage: 0 = ES, 1 = EN, 2 = PT, 3 = IT.
#define ANIME_LANG_ES 0
#define ANIME_LANG_EN 1
#define ANIME_LANG_PT 2
#define ANIME_LANG_IT 3

extern EWRAM_DATA u8 gSelectedBootLanguage;
extern EWRAM_DATA u8 gSelectedBootGender;
extern EWRAM_DATA u8 gSelectedBootName[PLAYER_NAME_LENGTH + 1];

#endif // GUARD_ANIME_BOOT_H
