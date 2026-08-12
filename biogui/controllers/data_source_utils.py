# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

import logging

from .. import data_sources
from ..utils import InterfaceModule

# Marker the ESP-side relay watches for (parse_gui_command() / gui_task.h's
# GUI_CONFIG_END_MARKER on the firmware side), sent as its own standalone
# one-byte message once the whole config+start sequence has gone out, so the
# ESP knows to relay everything it accumulated to the NRF as one control
# frame. Only meaningful over the TCP/WiFi transport -- BLE dispatches each
# startSeq message individually, no accumulation happens there.
_GUI_CONFIG_END_MARKER = bytes([0xEE])


def configure_transport(
    interface_module: InterfaceModule,
    data_source_type: data_sources.DataSourceType,
    worker_args: dict,
) -> None:
    """Configure packet framing according to the selected data source."""

    decode_globals = interface_module.decodeFn.__globals__
    logging.info(f"Configuring transport for data source type: {data_source_type}")
    if data_source_type == data_sources.DataSourceType.TCPCLIENT:
        worker_args["packetSize"] = (
            interface_module.wifiPacketSize
            if interface_module.wifiPacketSize not in (None, 0, [0, 0])
            else interface_module.packetSize
        )
        
        if interface_module.headerByte is not None:
            logging.info(f"Setting headerByte to {interface_module.headerByte}")
            worker_args["headerByte"] = interface_module.headerByte

        if interface_module.tailerByte is not None:
            logging.info(f"Setting tailerByte to {interface_module.tailerByte}")
            worker_args["tailerByte"] = interface_module.tailerByte

        active_transport = "wifi"

        # This is the only point in the whole flow where the data source
        # type is actually known -- startSeq is built earlier (at platform
        # config time, e.g. wulpus_pro/runtime.py's build_interface_module())
        # before any transport has been chosen, so it can't be done there.
        # Guarded so re-running configure_transport() for the same
        # InterfaceModule (e.g. a reconnect) doesn't duplicate the marker.
        if (
            not interface_module.startSeq
            or interface_module.startSeq[-1] != _GUI_CONFIG_END_MARKER
        ):
            interface_module.startSeq.append(_GUI_CONFIG_END_MARKER)
            logging.info("Added _GUI_CONFIG_END_MARKER to startSeq for TCPClient transport"
            )
            logging.info(f"final startSeq: {interface_module.startSeq}")


    else:
        logging.info(f"Using BLE packetSize: {interface_module.packetSize}")
        worker_args["packetSize"] = interface_module.packetSize
        active_transport = "ble"

        if data_source_type == data_sources.DataSourceType.SERIAL:
            # Give the serial worker the framing bytes so it can resync: a fixed
            # packetSize is only trustworthy while the stream stays aligned, and
            # one dropped byte otherwise cuts every later packet across two real
            # ones, silently and permanently. ((header, size) tables resync on
            # the table itself and need nothing here.)
            #
            # Only when those bytes are really in this stream, though. An
            # interface whose wifiPacketSize differs from its packetSize is
            # declaring framing that the Wi-Fi transport wraps around each
            # packet and BLE never carries -- biogapultra_wulpus_pro (0x55/0xAA,
            # 213 vs 211), whose BLE packets start with a 0x10..0x13 chunk
            # header instead. Checking for bytes that are not there would reject
            # every packet and the stream would never start.
            wifi_size = interface_module.wifiPacketSize
            transport_framed = (
                not isinstance(interface_module.packetSize, list)
                and wifi_size not in (None, 0)
                and wifi_size != interface_module.packetSize
            )
            if transport_framed:
                logging.info(
                    "Skipping headerByte/tailerByte: Wi-Fi transport framing "
                    "(wifiPacketSize %s != packetSize %s), absent in this stream",
                    wifi_size,
                    interface_module.packetSize,
                )
            else:
                if interface_module.headerByte is not None:
                    worker_args["headerByte"] = interface_module.headerByte
                if interface_module.tailerByte is not None:
                    worker_args["tailerByte"] = interface_module.tailerByte

    # Only transport-aware decoders declare this global variable.
    if "_active_transport" in decode_globals:
        decode_globals["_active_transport"] = active_transport