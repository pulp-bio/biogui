# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

# This file mirrors the connectivity_commands.h file in the nrf5340 firmware.
# It deines the command bytes used to control the different shields 

GET_DEVICE_SETTINGS = 13
REQUEST_HARDWARE_VERSION = 14
GET_BOARD_STATE = 15
REQUEST_BATTERY_STATE = 17
START_EEG_STREAMING = 18
STOP_EEG_STREAMING = 19
SET_BOARD_STATE = 20
RESET_BOARD = 21
ENTER_BOOTLOADERT_MODE = 22
SET_TRIGGER_STATE = 23
GO_TO_SLEEP = 24
RESET_GAP9 = 25
START_MIC_STREAMING = 26
STOP_MIC_STREAMING = 27
REQUEST_AVAILABLE_SENSORS = 28
REQUEST_FIRMWARE_VERSION = 29
REQUEST_CONNECTING_STRING = 30
START_STREAMING_ALL = 31
STOP_STREAMING_ALL = 32
START_IMU_STREAMING = 33
STOP_IMU_STREAMING = 34
START_EEG_MIC_STREAMING = 35
STOP_EEG_MIC_STREAMING = 36
SET_DEVICE_SETTINGS = 12
START_EMG_STREAMING = 37
STOP_EMG_STREAMING = 38
START_PPG_STREAMING = 39
STOP_PPG_STREAMING = 40
START_WULPUS_STREAMING = 41
STOP_WULPUS_STREAMING = 42
# Extended battery/system status (v2).
# Response header 43 = 0x2B is chosen to avoid collisions with streaming
# packet headers:
#   0x55 ExG
#   0x56 IMU
#   0xAA MIC
#   0x10-0x13 WULPUS
#   0x70 PPG
#
# This avoids the ambiguity of the legacy REQUEST_BATTERY_STATE echo
# (17 = 0x11), which overlaps with WULPUS chunk 2 during ultrasound streaming.
REQUEST_SYSTEM_STATUS = 43

# mmWave radar (Infineon BGT60TR13C on the SENSEI mmWave shield).
# Ordering the host must respect: TURN_ON before CONFIGURE, CONFIGURE before
# START. The three CHANGE_* take one value byte and are only read at the next
# CONFIGURE, so they belong before it.
START_MMWAVE_STREAMING = 44
STOP_MMWAVE_STREAMING = 45
CONFIGURE_MMWAVE = 46
TURN_OFF_MMWAVE = 47
TURN_ON_MMWAVE = 48
CHANGE_IFGAIN_MMWAVE = 49
CHANGE_TXPOWER_MMWAVE = 50
CHANGE_FPS_MMWAVE = 51

# Deliberately NOT 250/251 (0xFA/0xFB):
# sensors/wulpus/wulpus_appl.c treats those values as protocol-internal
# "new config" / "restart" markers embedded in raw MSP430 config bytes
# forwarded through the same dispatcher.
#
# A WULPUS config fragment legitimately starting with 250 or 251 could
# otherwise be intercepted as one of these commands instead of reaching
# wulpus_set_msp_config().
START_DUMMY_STREAMING = 243
STOP_DUMMY_STREAMING = 244
ESP_STOP_COMMAND = 245