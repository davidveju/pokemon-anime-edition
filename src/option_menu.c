#include "global.h"
#include "option_menu.h"
#include "bg.h"
#include "gpu_regs.h"
#include "international_string_util.h"
#include "main.h"
#include "menu.h"
#include "palette.h"
#include "scanline_effect.h"
#include "sprite.h"
#include "strings.h"
#include "task.h"
#include "text.h"
#include "text_window.h"
#include "window.h"
#include "gba/m4a_internal.h"
#include "constants/rgb.h"
#include "anime_boot.h"
#include "event_data.h"

#define tMenuSelection data[0]
#define tTextSpeed data[1]
#define tBattleSceneOff data[2]
#define tBattleStyle data[3]
#define tSound data[4]
#define tButtonMode data[5]
#define tWindowFrameType data[6]
#define tLanguage data[7]

enum
{
    MENUITEM_TEXTSPEED,
    MENUITEM_BATTLESCENE,
    MENUITEM_BATTLESTYLE,
    MENUITEM_SOUND,
    MENUITEM_BUTTONMODE,
    MENUITEM_FRAMETYPE,
    MENUITEM_LANGUAGE,
    MENUITEM_CANCEL,
    MENUITEM_COUNT,
};

enum
{
    WIN_HEADER,
    WIN_OPTIONS
};

// Pokemon Anime Edition: 8 rows (including LANGUAGE) share the 112px tall
// options window, so each row is 14px tall.
#define OPTION_MENU_ROW_H 14
#define YPOS_TEXTSPEED    (MENUITEM_TEXTSPEED * OPTION_MENU_ROW_H)
#define YPOS_BATTLESCENE  (MENUITEM_BATTLESCENE * OPTION_MENU_ROW_H)
#define YPOS_BATTLESTYLE  (MENUITEM_BATTLESTYLE * OPTION_MENU_ROW_H)
#define YPOS_SOUND        (MENUITEM_SOUND * OPTION_MENU_ROW_H)
#define YPOS_BUTTONMODE   (MENUITEM_BUTTONMODE * OPTION_MENU_ROW_H)
#define YPOS_FRAMETYPE    (MENUITEM_FRAMETYPE * OPTION_MENU_ROW_H)
#define YPOS_LANGUAGE     (MENUITEM_LANGUAGE * OPTION_MENU_ROW_H)

static void Task_OptionMenuFadeIn(u8 taskId);
static void Task_OptionMenuProcessInput(u8 taskId);
static void Task_OptionMenuSave(u8 taskId);
static void Task_OptionMenuFadeOut(u8 taskId);
static void HighlightOptionMenuItem(u8 selection);
static u8 TextSpeed_ProcessInput(u8 selection);
static void TextSpeed_DrawChoices(u8 selection);
static u8 BattleScene_ProcessInput(u8 selection);
static void BattleScene_DrawChoices(u8 selection);
static u8 BattleStyle_ProcessInput(u8 selection);
static void BattleStyle_DrawChoices(u8 selection);
static u8 Sound_ProcessInput(u8 selection);
static void Sound_DrawChoices(u8 selection);
static u8 FrameType_ProcessInput(u8 selection);
static void FrameType_DrawChoices(u8 selection);
static u8 Language_ProcessInput(u8 taskId, u8 selection);
static void Language_DrawChoices(u8 selection);
static void OptionMenu_RedrawAllTexts(u8 taskId);
static u8 AnimeOption_GetLang(void);
static u8 ButtonMode_ProcessInput(u8 selection);
static void ButtonMode_DrawChoices(u8 selection);
static void DrawHeaderText(void);
static void DrawOptionMenuTexts(void);
static void DrawBgWindowFrames(void);

EWRAM_DATA static bool8 sArrowPressed = FALSE;

static const u8 sText_AnimeOptionHeader_ES[] = _("OPCIONES");
static const u8 sText_AnimeOptionHeader_EN[] = _("OPTION");
static const u8 sText_AnimeOptionHeader_PT[] = _("OPCOES");
static const u8 sText_AnimeOptionHeader_IT[] = _("OPZIONI");
static const u8 *const sAnimeOptionHeader[] = {
    sText_AnimeOptionHeader_ES,
    sText_AnimeOptionHeader_EN,
    sText_AnimeOptionHeader_PT,
    sText_AnimeOptionHeader_IT,
};
// Pokemon Anime Edition: option labels in ES / EN / PT / IT.
// Portuguese avoids tilde vowels (uses ao/AO); every line stays short.
static const u8 sText_AnimeTextSpeed_ES[] = _("VELOCIDAD");
static const u8 sText_AnimeTextSpeed_EN[] = _("TEXT SPEED");
static const u8 sText_AnimeTextSpeed_PT[] = _("VELOCIDADE");
static const u8 sText_AnimeTextSpeed_IT[] = _("VELOCITA");
static const u8 sText_AnimeBattleScene_ES[] = _("ESCENA");
static const u8 sText_AnimeBattleScene_EN[] = _("BATTLE SCENE");
static const u8 sText_AnimeBattleScene_PT[] = _("CENA");
static const u8 sText_AnimeBattleScene_IT[] = _("SCENA");
static const u8 sText_AnimeBattleStyle_ES[] = _("ESTILO");
static const u8 sText_AnimeBattleStyle_EN[] = _("BATTLE STYLE");
static const u8 sText_AnimeBattleStyle_PT[] = _("ESTILO");
static const u8 sText_AnimeBattleStyle_IT[] = _("STILE");
static const u8 sText_AnimeSound_ES[] = _("SONIDO");
static const u8 sText_AnimeSound_EN[] = _("SOUND");
static const u8 sText_AnimeSound_PT[] = _("SOM");
static const u8 sText_AnimeSound_IT[] = _("SUONO");
static const u8 sText_AnimeButtonMode_ES[] = _("BOTONES");
static const u8 sText_AnimeButtonMode_EN[] = _("BUTTON MODE");
static const u8 sText_AnimeButtonMode_PT[] = _("BOTOES");
static const u8 sText_AnimeButtonMode_IT[] = _("PULSANTI");
static const u8 sText_AnimeFrame_ES[] = _("MARCO");
static const u8 sText_AnimeFrame_EN[] = _("FRAME");
static const u8 sText_AnimeFrame_PT[] = _("MOLDURA");
static const u8 sText_AnimeFrame_IT[] = _("CORNICE");
static const u8 sText_AnimeLanguage_ES[] = _("IDIOMA");
static const u8 sText_AnimeLanguage_EN[] = _("LANGUAGE");
static const u8 sText_AnimeLanguage_PT[] = _("IDIOMA");
static const u8 sText_AnimeLanguage_IT[] = _("LINGUA");
static const u8 sText_AnimeCancel_ES[] = _("SALIR");
static const u8 sText_AnimeCancel_EN[] = _("CANCEL");
static const u8 sText_AnimeCancel_PT[] = _("SAIR");
static const u8 sText_AnimeCancel_IT[] = _("ESCI");
static const u8 *const sAnimeOptionLabels[][MENUITEM_COUNT] = {
    {
        sText_AnimeTextSpeed_ES, sText_AnimeBattleScene_ES, sText_AnimeBattleStyle_ES,
        sText_AnimeSound_ES, sText_AnimeButtonMode_ES, sText_AnimeFrame_ES,
        sText_AnimeLanguage_ES, sText_AnimeCancel_ES,
    },
    {
        sText_AnimeTextSpeed_EN, sText_AnimeBattleScene_EN, sText_AnimeBattleStyle_EN,
        sText_AnimeSound_EN, sText_AnimeButtonMode_EN, sText_AnimeFrame_EN,
        sText_AnimeLanguage_EN, sText_AnimeCancel_EN,
    },
    {
        sText_AnimeTextSpeed_PT, sText_AnimeBattleScene_PT, sText_AnimeBattleStyle_PT,
        sText_AnimeSound_PT, sText_AnimeButtonMode_PT, sText_AnimeFrame_PT,
        sText_AnimeLanguage_PT, sText_AnimeCancel_PT,
    },
    {
        sText_AnimeTextSpeed_IT, sText_AnimeBattleScene_IT, sText_AnimeBattleStyle_IT,
        sText_AnimeSound_IT, sText_AnimeButtonMode_IT, sText_AnimeFrame_IT,
        sText_AnimeLanguage_IT, sText_AnimeCancel_IT,
    },
};
static const u8 sText_AnimeSlow_ES[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}LENTO");
static const u8 sText_AnimeSlow_EN[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}SLOW");
static const u8 sText_AnimeSlow_PT[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}LENTO");
static const u8 sText_AnimeSlow_IT[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}LENTO");
static const u8 sText_AnimeMid_ES[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}MEDIO");
static const u8 sText_AnimeMid_EN[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}MID");
static const u8 sText_AnimeMid_PT[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}MEDIO");
static const u8 sText_AnimeMid_IT[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}MEDIO");
static const u8 sText_AnimeFast_ES[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}RAPIDO");
static const u8 sText_AnimeFast_EN[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}FAST");
static const u8 sText_AnimeFast_PT[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}RAPIDO");
static const u8 sText_AnimeFast_IT[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}VELOCE");
static const u8 *const sAnimeTextSpeedChoices[][3] = {
    {sText_AnimeSlow_ES, sText_AnimeMid_ES, sText_AnimeFast_ES},
    {sText_AnimeSlow_EN, sText_AnimeMid_EN, sText_AnimeFast_EN},
    {sText_AnimeSlow_PT, sText_AnimeMid_PT, sText_AnimeFast_PT},
    {sText_AnimeSlow_IT, sText_AnimeMid_IT, sText_AnimeFast_IT},
};
static const u8 sText_AnimeOn_ES[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}SI");
static const u8 sText_AnimeOn_EN[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}ON");
static const u8 sText_AnimeOn_PT[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}SIM");
static const u8 sText_AnimeOn_IT[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}SI");
static const u8 sText_AnimeOff_ES[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}NO");
static const u8 sText_AnimeOff_EN[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}OFF");
static const u8 sText_AnimeOff_PT[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}NAO");
static const u8 sText_AnimeOff_IT[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}NO");
static const u8 *const sAnimeOnOffChoices[][2] = {
    {sText_AnimeOn_ES, sText_AnimeOff_ES},
    {sText_AnimeOn_EN, sText_AnimeOff_EN},
    {sText_AnimeOn_PT, sText_AnimeOff_PT},
    {sText_AnimeOn_IT, sText_AnimeOff_IT},
};
static const u8 sText_AnimeShift_ES[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}CAMBIO");
static const u8 sText_AnimeShift_EN[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}SHIFT");
static const u8 sText_AnimeShift_PT[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}TURNO");
static const u8 sText_AnimeShift_IT[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}CAMBIO");
static const u8 sText_AnimeSet_ES[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}FIJO");
static const u8 sText_AnimeSet_EN[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}SET");
static const u8 sText_AnimeSet_PT[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}FIXO");
static const u8 sText_AnimeSet_IT[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}FISSO");
static const u8 *const sAnimeShiftSetChoices[][2] = {
    {sText_AnimeShift_ES, sText_AnimeSet_ES},
    {sText_AnimeShift_EN, sText_AnimeSet_EN},
    {sText_AnimeShift_PT, sText_AnimeSet_PT},
    {sText_AnimeShift_IT, sText_AnimeSet_IT},
};
static const u8 sText_AnimeFrameWord_ES[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}TIPO");
static const u8 sText_AnimeFrameWord_EN[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}TYPE");
static const u8 sText_AnimeFrameWord_PT[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}TIPO");
static const u8 sText_AnimeFrameWord_IT[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}TIPO");
static const u8 *const sAnimeFrameWord[] = {
    sText_AnimeFrameWord_ES,
    sText_AnimeFrameWord_EN,
    sText_AnimeFrameWord_PT,
    sText_AnimeFrameWord_IT,
};
static const u8 sText_AnimeLangName_ES[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}ESPAÑOL");
static const u8 sText_AnimeLangName_EN[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}ENGLISH");
static const u8 sText_AnimeLangName_PT[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}PORTUGUES");
static const u8 sText_AnimeLangName_IT[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}ITALIANO");
static const u8 *const sAnimeLangNames[] = {
    sText_AnimeLangName_ES,
    sText_AnimeLangName_EN,
    sText_AnimeLangName_PT,
    sText_AnimeLangName_IT,
};

static const u8 gText_SoundMono[]          = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}MONO");
static const u8 gText_SoundStereo[]        = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}STEREO");
static const u8 gText_FrameTypeNumber[]    = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}");
static const u8 gText_ButtonTypeNormal[]   = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}NORMAL");
static const u8 gText_ButtonTypeLR[]       = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}LR");
static const u8 gText_ButtonTypeLEqualsA[] = _("{COLOR GREEN}{SHADOW LIGHT_GREEN}L=A");

static const u16 sOptionMenuText_Pal[] = INCGFX_U16("graphics/interface/option_menu_text.pal", ".gbapal");
// note: this is only used in the Japanese release
static const u8 sEqualSignGfx[] = INCGFX_U8("graphics/interface/option_menu_equals_sign.png", ".4bpp");

// Pokemon Anime Edition: display language for this menu. It mirrors
// gSelectedBootLanguage, which is synced with the save on Continue and
// written back to the save (flags) when leaving this menu.
static u8 AnimeOption_GetLang(void)
{
    u8 lang = gSelectedBootLanguage & 3;
    return (lang < 4) ? lang : 0;
}

static const struct WindowTemplate sOptionMenuWinTemplates[] =
{
    [WIN_HEADER] = {
        .bg = 1,
        .tilemapLeft = 2,
        .tilemapTop = 1,
        .width = 26,
        .height = 2,
        .paletteNum = 1,
        .baseBlock = 2
    },
    [WIN_OPTIONS] = {
        .bg = 0,
        .tilemapLeft = 2,
        .tilemapTop = 5,
        .width = 26,
        .height = 14,
        .paletteNum = 1,
        .baseBlock = 0x36
    },
    DUMMY_WIN_TEMPLATE
};

static const struct BgTemplate sOptionMenuBgTemplates[] =
{
    {
        .bg = 1,
        .charBaseIndex = 1,
        .mapBaseIndex = 30,
        .screenSize = 0,
        .paletteMode = 0,
        .priority = 0,
        .baseTile = 0
    },
    {
        .bg = 0,
        .charBaseIndex = 1,
        .mapBaseIndex = 31,
        .screenSize = 0,
        .paletteMode = 0,
        .priority = 1,
        .baseTile = 0
    }
};

static const u16 sOptionMenuBg_Pal[] = {RGB(17, 18, 31)};

static void MainCB2(void)
{
    RunTasks();
    AnimateSprites();
    BuildOamBuffer();
    UpdatePaletteFade();
}

static void VBlankCB(void)
{
    LoadOam();
    ProcessSpriteCopyRequests();
    TransferPlttBuffer();
}

void CB2_InitOptionMenu(void)
{
    switch (gMain.state)
    {
    default:
    case 0:
        SetVBlankCallback(NULL);
        gMain.state++;
        break;
    case 1:
        DmaClearLarge16(3, (void *)(VRAM), VRAM_SIZE, 0x1000);
        DmaClear32(3, OAM, OAM_SIZE);
        DmaClear16(3, PLTT, PLTT_SIZE);
        SetGpuReg(REG_OFFSET_DISPCNT, 0);
        ResetBgsAndClearDma3BusyFlags(0);
        InitBgsFromTemplates(0, sOptionMenuBgTemplates, ARRAY_COUNT(sOptionMenuBgTemplates));
        ChangeBgX(0, 0, BG_COORD_SET);
        ChangeBgY(0, 0, BG_COORD_SET);
        ChangeBgX(1, 0, BG_COORD_SET);
        ChangeBgY(1, 0, BG_COORD_SET);
        ChangeBgX(2, 0, BG_COORD_SET);
        ChangeBgY(2, 0, BG_COORD_SET);
        ChangeBgX(3, 0, BG_COORD_SET);
        ChangeBgY(3, 0, BG_COORD_SET);
        InitWindows(sOptionMenuWinTemplates);
        DeactivateAllTextPrinters();
        SetGpuReg(REG_OFFSET_WIN0H, 0);
        SetGpuReg(REG_OFFSET_WIN0V, 0);
        SetGpuReg(REG_OFFSET_WININ, WININ_WIN0_BG0);
        SetGpuReg(REG_OFFSET_WINOUT, WINOUT_WIN01_BG0 | WINOUT_WIN01_BG1 | WINOUT_WIN01_CLR);
        SetGpuReg(REG_OFFSET_BLDCNT, BLDCNT_TGT1_BG0 | BLDCNT_EFFECT_DARKEN);
        SetGpuReg(REG_OFFSET_BLDALPHA, 0);
        SetGpuReg(REG_OFFSET_BLDY, 4);
        SetGpuReg(REG_OFFSET_DISPCNT, DISPCNT_WIN0_ON | DISPCNT_OBJ_ON | DISPCNT_OBJ_1D_MAP);
        ShowBg(0);
        ShowBg(1);
        gMain.state++;
        break;
    case 2:
        ResetPaletteFade();
        ScanlineEffect_Stop();
        ResetTasks();
        ResetSpriteData();
        gMain.state++;
        break;
    case 3:
        LoadBgTiles(1, GetWindowFrameTilesPal(gSaveBlock2Ptr->optionsWindowFrameType)->tiles, 0x120, 0x1A2);
        gMain.state++;
        break;
    case 4:
        LoadPalette(sOptionMenuBg_Pal, BG_PLTT_ID(0), sizeof(sOptionMenuBg_Pal));
        LoadPalette(GetWindowFrameTilesPal(gSaveBlock2Ptr->optionsWindowFrameType)->pal, BG_PLTT_ID(7), PLTT_SIZE_4BPP);
        gMain.state++;
        break;
    case 5:
        LoadPalette(sOptionMenuText_Pal, BG_PLTT_ID(1), sizeof(sOptionMenuText_Pal));
        gMain.state++;
        break;
    case 6:
        PutWindowTilemap(WIN_HEADER);
        DrawHeaderText();
        gMain.state++;
        break;
    case 7:
        gMain.state++;
        break;
    case 8:
        PutWindowTilemap(WIN_OPTIONS);
        DrawOptionMenuTexts();
        gMain.state++;
    case 9:
        DrawBgWindowFrames();
        gMain.state++;
        break;
    case 10:
    {
        u8 taskId = CreateTask(Task_OptionMenuFadeIn, 0);

        gTasks[taskId].tMenuSelection = 0;
        gTasks[taskId].tTextSpeed = gSaveBlock2Ptr->optionsTextSpeed;
        gTasks[taskId].tBattleSceneOff = gSaveBlock2Ptr->optionsBattleSceneOff;
        gTasks[taskId].tBattleStyle = gSaveBlock2Ptr->optionsBattleStyle;
        gTasks[taskId].tSound = gSaveBlock2Ptr->optionsSound;
        gTasks[taskId].tButtonMode = gSaveBlock2Ptr->optionsButtonMode;
        gTasks[taskId].tWindowFrameType = gSaveBlock2Ptr->optionsWindowFrameType;
        gTasks[taskId].tLanguage = gSelectedBootLanguage & 3;

        TextSpeed_DrawChoices(gTasks[taskId].tTextSpeed);
        BattleScene_DrawChoices(gTasks[taskId].tBattleSceneOff);
        BattleStyle_DrawChoices(gTasks[taskId].tBattleStyle);
        Sound_DrawChoices(gTasks[taskId].tSound);
        ButtonMode_DrawChoices(gTasks[taskId].tButtonMode);
        FrameType_DrawChoices(gTasks[taskId].tWindowFrameType);
        Language_DrawChoices(gTasks[taskId].tLanguage);
        HighlightOptionMenuItem(gTasks[taskId].tMenuSelection);

        CopyWindowToVram(WIN_OPTIONS, COPYWIN_FULL);
        gMain.state++;
        break;
    }
    case 11:
        BeginNormalPaletteFade(PALETTES_ALL, 0, 16, 0, RGB_BLACK);
        SetVBlankCallback(VBlankCB);
        SetMainCallback2(MainCB2);
        return;
    }
}

static void Task_OptionMenuFadeIn(u8 taskId)
{
    if (!gPaletteFade.active)
        gTasks[taskId].func = Task_OptionMenuProcessInput;
}

static void Task_OptionMenuProcessInput(u8 taskId)
{
    if (JOY_NEW(A_BUTTON))
    {
        if (gTasks[taskId].tMenuSelection == MENUITEM_CANCEL)
            gTasks[taskId].func = Task_OptionMenuSave;
    }
    else if (JOY_NEW(B_BUTTON))
    {
        gTasks[taskId].func = Task_OptionMenuSave;
    }
    else if (JOY_NEW(DPAD_UP))
    {
        if (gTasks[taskId].tMenuSelection > 0)
            gTasks[taskId].tMenuSelection--;
        else
            gTasks[taskId].tMenuSelection = MENUITEM_CANCEL;
        HighlightOptionMenuItem(gTasks[taskId].tMenuSelection);
    }
    else if (JOY_NEW(DPAD_DOWN))
    {
        if (gTasks[taskId].tMenuSelection < MENUITEM_CANCEL)
            gTasks[taskId].tMenuSelection++;
        else
            gTasks[taskId].tMenuSelection = 0;
        HighlightOptionMenuItem(gTasks[taskId].tMenuSelection);
    }
    else
    {
        u8 previousOption;

        switch (gTasks[taskId].tMenuSelection)
        {
        case MENUITEM_TEXTSPEED:
            previousOption = gTasks[taskId].tTextSpeed;
            gTasks[taskId].tTextSpeed = TextSpeed_ProcessInput(gTasks[taskId].tTextSpeed);

            if (previousOption != gTasks[taskId].tTextSpeed)
                TextSpeed_DrawChoices(gTasks[taskId].tTextSpeed);
            break;
        case MENUITEM_BATTLESCENE:
            previousOption = gTasks[taskId].tBattleSceneOff;
            gTasks[taskId].tBattleSceneOff = BattleScene_ProcessInput(gTasks[taskId].tBattleSceneOff);

            if (previousOption != gTasks[taskId].tBattleSceneOff)
                BattleScene_DrawChoices(gTasks[taskId].tBattleSceneOff);
            break;
        case MENUITEM_BATTLESTYLE:
            previousOption = gTasks[taskId].tBattleStyle;
            gTasks[taskId].tBattleStyle = BattleStyle_ProcessInput(gTasks[taskId].tBattleStyle);

            if (previousOption != gTasks[taskId].tBattleStyle)
                BattleStyle_DrawChoices(gTasks[taskId].tBattleStyle);
            break;
        case MENUITEM_SOUND:
            previousOption = gTasks[taskId].tSound;
            gTasks[taskId].tSound = Sound_ProcessInput(gTasks[taskId].tSound);

            if (previousOption != gTasks[taskId].tSound)
                Sound_DrawChoices(gTasks[taskId].tSound);
            break;
        case MENUITEM_BUTTONMODE:
            previousOption = gTasks[taskId].tButtonMode;
            gTasks[taskId].tButtonMode = ButtonMode_ProcessInput(gTasks[taskId].tButtonMode);

            if (previousOption != gTasks[taskId].tButtonMode)
                ButtonMode_DrawChoices(gTasks[taskId].tButtonMode);
            break;
        case MENUITEM_FRAMETYPE:
            previousOption = gTasks[taskId].tWindowFrameType;
            gTasks[taskId].tWindowFrameType = FrameType_ProcessInput(gTasks[taskId].tWindowFrameType);

            if (previousOption != gTasks[taskId].tWindowFrameType)
                FrameType_DrawChoices(gTasks[taskId].tWindowFrameType);
            break;
        case MENUITEM_LANGUAGE:
            gTasks[taskId].tLanguage = Language_ProcessInput(taskId, gTasks[taskId].tLanguage);
            break;
        default:
            return;
        }

        if (sArrowPressed)
        {
            sArrowPressed = FALSE;
            CopyWindowToVram(WIN_OPTIONS, COPYWIN_GFX);
        }
    }
}

static void Task_OptionMenuSave(u8 taskId)
{
    gSaveBlock2Ptr->optionsTextSpeed = gTasks[taskId].tTextSpeed;
    gSaveBlock2Ptr->optionsBattleSceneOff = gTasks[taskId].tBattleSceneOff;
    gSaveBlock2Ptr->optionsBattleStyle = gTasks[taskId].tBattleStyle;
    gSaveBlock2Ptr->optionsSound = gTasks[taskId].tSound;
    gSaveBlock2Ptr->optionsButtonMode = gTasks[taskId].tButtonMode;
    gSaveBlock2Ptr->optionsWindowFrameType = gTasks[taskId].tWindowFrameType;
    // Pokemon Anime Edition: store the language chosen here, both in the
    // boot variable (used by every menu from now on) and in the save flags
    // (used in-game, e.g. PC messages). Harmless when no save is loaded.
    gSelectedBootLanguage = gTasks[taskId].tLanguage & 3;
    SetAnimeLanguage(gSelectedBootLanguage);

    BeginNormalPaletteFade(PALETTES_ALL, 0, 0, 16, RGB_BLACK);
    gTasks[taskId].func = Task_OptionMenuFadeOut;
}

static void Task_OptionMenuFadeOut(u8 taskId)
{
    if (!gPaletteFade.active)
    {
        DestroyTask(taskId);
        FreeAllWindowBuffers();
        SetMainCallback2(gMain.savedCallback);
    }
}

static void HighlightOptionMenuItem(u8 index)
{
    SetGpuReg(REG_OFFSET_WIN0H, WIN_RANGE(16, DISPLAY_WIDTH - 16));
    SetGpuReg(REG_OFFSET_WIN0V, WIN_RANGE(index * OPTION_MENU_ROW_H + 40, index * OPTION_MENU_ROW_H + 40 + OPTION_MENU_ROW_H));
}

static void DrawOptionMenuChoice(const u8 *text, u8 x, u8 y, u8 style)
{
    u8 dst[16];
    u16 i;

    for (i = 0; *text != EOS && i < ARRAY_COUNT(dst) - 1; i++)
        dst[i] = *(text++);

    if (style != 0)
    {
        dst[2] = TEXT_COLOR_RED;
        dst[5] = TEXT_COLOR_LIGHT_RED;
    }

    dst[i] = EOS;
    AddTextPrinterParameterized(WIN_OPTIONS, FONT_NORMAL, dst, x, y + 1, TEXT_SKIP_DRAW, NULL);
}

static u8 TextSpeed_ProcessInput(u8 selection)
{
    if (JOY_NEW(DPAD_RIGHT))
    {
        if (selection <= 1)
            selection++;
        else
            selection = 0;

        sArrowPressed = TRUE;
    }
    if (JOY_NEW(DPAD_LEFT))
    {
        if (selection != 0)
            selection--;
        else
            selection = 2;

        sArrowPressed = TRUE;
    }
    return selection;
}

static void TextSpeed_DrawChoices(u8 selection)
{
    u8 styles[3];
    s32 widthSlow, widthMid, widthFast, xMid;

    styles[0] = 0;
    styles[1] = 0;
    styles[2] = 0;
    styles[selection] = 1;

    {
        u8 lang = AnimeOption_GetLang();
        DrawOptionMenuChoice(sAnimeTextSpeedChoices[lang][0], 104, YPOS_TEXTSPEED, styles[0]);

        widthSlow = GetStringWidth(FONT_NORMAL, sAnimeTextSpeedChoices[lang][0], 0);
        widthMid = GetStringWidth(FONT_NORMAL, sAnimeTextSpeedChoices[lang][1], 0);
        widthFast = GetStringWidth(FONT_NORMAL, sAnimeTextSpeedChoices[lang][2], 0);

        widthMid -= 94;
        xMid = (widthSlow - widthMid - widthFast) / 2 + 104;
        DrawOptionMenuChoice(sAnimeTextSpeedChoices[lang][1], xMid, YPOS_TEXTSPEED, styles[1]);

        DrawOptionMenuChoice(sAnimeTextSpeedChoices[lang][2], GetStringRightAlignXOffset(FONT_NORMAL, sAnimeTextSpeedChoices[lang][2], 198), YPOS_TEXTSPEED, styles[2]);
    }
}

static u8 BattleScene_ProcessInput(u8 selection)
{
    if (JOY_NEW(DPAD_LEFT | DPAD_RIGHT))
    {
        selection ^= 1;
        sArrowPressed = TRUE;
    }

    return selection;
}

static void BattleScene_DrawChoices(u8 selection)
{
    u8 styles[2];

    styles[0] = 0;
    styles[1] = 0;
    styles[selection] = 1;

    {
        u8 lang = AnimeOption_GetLang();
        DrawOptionMenuChoice(sAnimeOnOffChoices[lang][0], 104, YPOS_BATTLESCENE, styles[0]);
        DrawOptionMenuChoice(sAnimeOnOffChoices[lang][1], GetStringRightAlignXOffset(FONT_NORMAL, sAnimeOnOffChoices[lang][1], 198), YPOS_BATTLESCENE, styles[1]);
    }
}

static u8 BattleStyle_ProcessInput(u8 selection)
{
    if (JOY_NEW(DPAD_LEFT | DPAD_RIGHT))
    {
        selection ^= 1;
        sArrowPressed = TRUE;
    }

    return selection;
}

static void BattleStyle_DrawChoices(u8 selection)
{
    u8 styles[2];

    styles[0] = 0;
    styles[1] = 0;
    styles[selection] = 1;

    {
        u8 lang = AnimeOption_GetLang();
        DrawOptionMenuChoice(sAnimeShiftSetChoices[lang][0], 104, YPOS_BATTLESTYLE, styles[0]);
        DrawOptionMenuChoice(sAnimeShiftSetChoices[lang][1], GetStringRightAlignXOffset(FONT_NORMAL, sAnimeShiftSetChoices[lang][1], 198), YPOS_BATTLESTYLE, styles[1]);
    }
}

static u8 Sound_ProcessInput(u8 selection)
{
    if (JOY_NEW(DPAD_LEFT | DPAD_RIGHT))
    {
        selection ^= 1;
        SetPokemonCryStereo(selection);
        sArrowPressed = TRUE;
    }

    return selection;
}

static void Sound_DrawChoices(u8 selection)
{
    u8 styles[2];

    styles[0] = 0;
    styles[1] = 0;
    styles[selection] = 1;

    DrawOptionMenuChoice(gText_SoundMono, 104, YPOS_SOUND, styles[0]);
    DrawOptionMenuChoice(gText_SoundStereo, GetStringRightAlignXOffset(FONT_NORMAL, gText_SoundStereo, 198), YPOS_SOUND, styles[1]);
}

static u8 FrameType_ProcessInput(u8 selection)
{
    if (JOY_NEW(DPAD_RIGHT))
    {
        if (selection < WINDOW_FRAMES_COUNT - 1)
            selection++;
        else
            selection = 0;

        LoadBgTiles(1, GetWindowFrameTilesPal(selection)->tiles, 0x120, 0x1A2);
        LoadPalette(GetWindowFrameTilesPal(selection)->pal, BG_PLTT_ID(7), PLTT_SIZE_4BPP);
        sArrowPressed = TRUE;
    }
    if (JOY_NEW(DPAD_LEFT))
    {
        if (selection != 0)
            selection--;
        else
            selection = WINDOW_FRAMES_COUNT - 1;

        LoadBgTiles(1, GetWindowFrameTilesPal(selection)->tiles, 0x120, 0x1A2);
        LoadPalette(GetWindowFrameTilesPal(selection)->pal, BG_PLTT_ID(7), PLTT_SIZE_4BPP);
        sArrowPressed = TRUE;
    }
    return selection;
}

static void FrameType_DrawChoices(u8 selection)
{
    u8 text[16] = {EOS};
    u8 n = selection + 1;
    u16 i;

    for (i = 0; gText_FrameTypeNumber[i] != EOS && i <= 5; i++)
        text[i] = gText_FrameTypeNumber[i];

    // Convert a number to decimal string
    if (n / 10 != 0)
    {
        text[i] = n / 10 + CHAR_0;
        i++;
        text[i] = n % 10 + CHAR_0;
        i++;
    }
    else
    {
        text[i] = n % 10 + CHAR_0;
        i++;
        text[i] = CHAR_SPACER;
        i++;
    }

    text[i] = EOS;

    DrawOptionMenuChoice(sAnimeFrameWord[AnimeOption_GetLang()], 104, YPOS_FRAMETYPE, 0);
    DrawOptionMenuChoice(text, 128, YPOS_FRAMETYPE, 1);
}

static u8 Language_ProcessInput(u8 taskId, u8 selection)
{
    if (JOY_NEW(DPAD_RIGHT))
    {
        selection = (selection + 1) & 3;
        sArrowPressed = TRUE;
    }
    if (JOY_NEW(DPAD_LEFT))
    {
        selection = (selection + 3) & 3;
        sArrowPressed = TRUE;
    }
    if (sArrowPressed)
    {
        // Pokemon Anime Edition: apply the new language at once and redraw
        // the whole menu in it.
        gSelectedBootLanguage = selection & 3;
        gTasks[taskId].tLanguage = gSelectedBootLanguage;
        OptionMenu_RedrawAllTexts(taskId);
        sArrowPressed = FALSE;
        CopyWindowToVram(WIN_OPTIONS, COPYWIN_GFX);
        CopyWindowToVram(WIN_HEADER, COPYWIN_GFX);
    }
    return selection;
}

static void Language_DrawChoices(u8 selection)
{
    DrawOptionMenuChoice(sAnimeLangNames[selection & 3], GetStringRightAlignXOffset(FONT_NORMAL, sAnimeLangNames[selection & 3], 198), YPOS_LANGUAGE, 1);
}

static void OptionMenu_RedrawAllTexts(u8 taskId)
{
    DrawHeaderText();
    DrawOptionMenuTexts();
    TextSpeed_DrawChoices(gTasks[taskId].tTextSpeed);
    BattleScene_DrawChoices(gTasks[taskId].tBattleSceneOff);
    BattleStyle_DrawChoices(gTasks[taskId].tBattleStyle);
    Sound_DrawChoices(gTasks[taskId].tSound);
    ButtonMode_DrawChoices(gTasks[taskId].tButtonMode);
    FrameType_DrawChoices(gTasks[taskId].tWindowFrameType);
    Language_DrawChoices(gTasks[taskId].tLanguage);
}

static u8 ButtonMode_ProcessInput(u8 selection)
{
    if (JOY_NEW(DPAD_RIGHT))
    {
        if (selection <= 1)
            selection++;
        else
            selection = 0;

        sArrowPressed = TRUE;
    }
    if (JOY_NEW(DPAD_LEFT))
    {
        if (selection != 0)
            selection--;
        else
            selection = 2;

        sArrowPressed = TRUE;
    }
    return selection;
}

static void ButtonMode_DrawChoices(u8 selection)
{
    s32 widthNormal, widthLR, widthLA, xLR;
    u8 styles[3];

    styles[0] = 0;
    styles[1] = 0;
    styles[2] = 0;
    styles[selection] = 1;

    DrawOptionMenuChoice(gText_ButtonTypeNormal, 104, YPOS_BUTTONMODE, styles[0]);

    widthNormal = GetStringWidth(FONT_NORMAL, gText_ButtonTypeNormal, 0);
    widthLR = GetStringWidth(FONT_NORMAL, gText_ButtonTypeLR, 0);
    widthLA = GetStringWidth(FONT_NORMAL, gText_ButtonTypeLEqualsA, 0);

    widthLR -= 94;
    xLR = (widthNormal - widthLR - widthLA) / 2 + 104;
    DrawOptionMenuChoice(gText_ButtonTypeLR, xLR, YPOS_BUTTONMODE, styles[1]);

    DrawOptionMenuChoice(gText_ButtonTypeLEqualsA, GetStringRightAlignXOffset(FONT_NORMAL, gText_ButtonTypeLEqualsA, 198), YPOS_BUTTONMODE, styles[2]);
}

static void DrawHeaderText(void)
{
    FillWindowPixelBuffer(WIN_HEADER, PIXEL_FILL(1));
    AddTextPrinterParameterized(WIN_HEADER, FONT_NORMAL, sAnimeOptionHeader[AnimeOption_GetLang()], 8, 1, TEXT_SKIP_DRAW, NULL);
    CopyWindowToVram(WIN_HEADER, COPYWIN_FULL);
}

static void DrawOptionMenuTexts(void)
{
    u8 i;

    FillWindowPixelBuffer(WIN_OPTIONS, PIXEL_FILL(1));
    for (i = 0; i < MENUITEM_COUNT; i++)
        AddTextPrinterParameterized(WIN_OPTIONS, FONT_NORMAL, sAnimeOptionLabels[AnimeOption_GetLang()][i], 8, (i * OPTION_MENU_ROW_H) + 1, TEXT_SKIP_DRAW, NULL);
    CopyWindowToVram(WIN_OPTIONS, COPYWIN_FULL);
}

#define TILE_TOP_CORNER_L 0x1A2
#define TILE_TOP_EDGE     0x1A3
#define TILE_TOP_CORNER_R 0x1A4
#define TILE_LEFT_EDGE    0x1A5
#define TILE_RIGHT_EDGE   0x1A7
#define TILE_BOT_CORNER_L 0x1A8
#define TILE_BOT_EDGE     0x1A9
#define TILE_BOT_CORNER_R 0x1AA

static void DrawBgWindowFrames(void)
{
    //                     bg, tile,              x, y, width, height, palNum
    // Draw title window frame
    FillBgTilemapBufferRect(1, TILE_TOP_CORNER_L,  1,  0,  1,  1,  7);
    FillBgTilemapBufferRect(1, TILE_TOP_EDGE,      2,  0, 27,  1,  7);
    FillBgTilemapBufferRect(1, TILE_TOP_CORNER_R, 28,  0,  1,  1,  7);
    FillBgTilemapBufferRect(1, TILE_LEFT_EDGE,     1,  1,  1,  2,  7);
    FillBgTilemapBufferRect(1, TILE_RIGHT_EDGE,   28,  1,  1,  2,  7);
    FillBgTilemapBufferRect(1, TILE_BOT_CORNER_L,  1,  3,  1,  1,  7);
    FillBgTilemapBufferRect(1, TILE_BOT_EDGE,      2,  3, 27,  1,  7);
    FillBgTilemapBufferRect(1, TILE_BOT_CORNER_R, 28,  3,  1,  1,  7);

    // Draw options list window frame
    FillBgTilemapBufferRect(1, TILE_TOP_CORNER_L,  1,  4,  1,  1,  7);
    FillBgTilemapBufferRect(1, TILE_TOP_EDGE,      2,  4, 26,  1,  7);
    FillBgTilemapBufferRect(1, TILE_TOP_CORNER_R, 28,  4,  1,  1,  7);
    FillBgTilemapBufferRect(1, TILE_LEFT_EDGE,     1,  5,  1, 18,  7);
    FillBgTilemapBufferRect(1, TILE_RIGHT_EDGE,   28,  5,  1, 18,  7);
    FillBgTilemapBufferRect(1, TILE_BOT_CORNER_L,  1, 19,  1,  1,  7);
    FillBgTilemapBufferRect(1, TILE_BOT_EDGE,      2, 19, 26,  1,  7);
    FillBgTilemapBufferRect(1, TILE_BOT_CORNER_R, 28, 19,  1,  1,  7);

    CopyBgTilemapBufferToVram(1);
}
