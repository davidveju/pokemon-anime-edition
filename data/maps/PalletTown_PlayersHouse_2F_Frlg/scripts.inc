PalletTown_PlayersHouse_2F_Frlg_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, PalletTown_PlayersHouse_2F_OnTransition
	map_script MAP_SCRIPT_ON_WARP_INTO_MAP_TABLE, PalletTown_PlayersHouse_2F_OnWarp
	map_script MAP_SCRIPT_ON_FRAME_TABLE, PalletTown_PlayersHouse_2F_OnFrame
	.byte 0

PalletTown_PlayersHouse_2F_OnTransition::
	call_if_eq VAR_MAP_SCENE_PALLET_TOWN_PLAYERS_HOUSE_2F, 0, PalletTown_PlayersHouse_2F_EventScript_SetRespawn
	end

PalletTown_PlayersHouse_2F_EventScript_SetRespawn::
	setrespawn HEAL_LOCATION_PALLET_TOWN
	return

PalletTown_PlayersHouse_2F_OnWarp::
	map_script_2 VAR_MAP_SCENE_PALLET_TOWN_PLAYERS_HOUSE_2F, 0, PalletTown_PlayersHouse_2F_FirstWarpIn
	.2byte 0

PalletTown_PlayersHouse_2F_FirstWarpIn::
	turnobject LOCALID_PLAYER, DIR_NORTH
	setvar VAR_MAP_SCENE_PALLET_TOWN_PLAYERS_HOUSE_2F, 1
	end

PalletTown_PlayersHouse_2F_OnFrame::
	map_script_2 VAR_MAP_SCENE_PALLET_TOWN_PLAYERS_HOUSE_2F, 1, PalletTown_PlayersHouse_2F_EventScript_WokeUpLate
	.2byte 0

@ Pokemon Anime Edition: first episode opening. The player oversleeps and
@ must rush to Professor Oak's lab.
PalletTown_PlayersHouse_2F_EventScript_WokeUpLate::
	lockall
	delay 16
	msgbox_i18n PalletTown_PlayersHouse_2F_Text_WokeUpLate_ES, PalletTown_PlayersHouse_2F_Text_WokeUpLate_EN, PalletTown_PlayersHouse_2F_Text_WokeUpLate_PT, PalletTown_PlayersHouse_2F_Text_WokeUpLate_IT
	closemessage
	setvar VAR_MAP_SCENE_PALLET_TOWN_PLAYERS_HOUSE_2F, 2
	releaseall
	end

PalletTown_PlayersHouse_2F_Text_WokeUpLate_ES::
	.string "¡Son las 11:00!\n"
	.string "¡Me he quedado dormido!\p"
	.string "¡El PROF. OAK me espera\n"
	.string "en el laboratorio!$"

PalletTown_PlayersHouse_2F_Text_WokeUpLate_EN::
	.string "It's 11:00!\n"
	.string "I overslept!\p"
	.string "Prof. Oak is waiting\n"
	.string "for me at the lab!$"

PalletTown_PlayersHouse_2F_Text_WokeUpLate_PT::
	.string "Sao 11:00!\n"
	.string "Acordei tarde!\p"
	.string "O Prof. Oak esta a minha\n"
	.string "espera no laboratorio!$"

PalletTown_PlayersHouse_2F_Text_WokeUpLate_IT::
	.string "Sono le 11:00!\n"
	.string "Ho dormito troppo!\p"
	.string "Il Prof. Oak mi aspetta\n"
	.string "nel laboratorio!$"

PalletTown_PlayersHouse_2F_EventScript_NES::
	msgbox PalletTown_PlayersHouse_2F_Text_PlayedWithNES, MSGBOX_SIGN
	end

PalletTown_PlayersHouse_2F_EventScript_Sign::
	msgbox PalletTown_PlayersHouse_2F_Text_PressLRForHelp, MSGBOX_SIGN
	end

PalletTown_PlayersHouse_2F_Text_PlayedWithNES::
	.string "{PLAYER} played with the NES.\p"
	.string "…Okay!\n"
	.string "It's time to go!$"

PalletTown_PlayersHouse_2F_Text_PressLRForHelp::
	.string "It's a posted notice…\p"
	.string "If you're confused, ask for HELP!\n"
	.string "Press the L or R Button!$"

