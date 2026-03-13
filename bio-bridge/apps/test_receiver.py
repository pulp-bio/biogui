"""
BioGUI Packet Receiver Debug Tool
==================================

Receives and displays raw BioGUI packets.

INPUT:  BioGUI TCP (raw packets)
OUTPUT: None (no Unity)
TERMINAL: Prints packet contents (config_id, US data, IMU data)

Use Case:
- Debug BioGUI data forwarding
- Verify packet format and contents
- Check if BioGUI is sending correctly

Usage:
    python -m apps.test_receiver
    python -m apps.test_receiver --port 12345
"""

import argparse
import socket

from core import (
    BIOGUI_HOST,
    BIOGUI_PORT,
    WULPUS_PACKET_FORMAT,
    decode_packet,
    recv_exact,
)


def run_receiver(host: str = BIOGUI_HOST, port: int = BIOGUI_PORT):
    """
    Run TCP receiver and print received packets.

    Parameters
    ----------
    host : str
        Host address to bind to
    port : int
        TCP port to listen on
    """
    # Print configuration
    WULPUS_PACKET_FORMAT.print_info()
    print()

    # Create socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(1)

    packet_size = WULPUS_PACKET_FORMAT.packet_size
    print(f"Listening on {host}:{port} ({packet_size} bytes/packet)...")
    print("Waiting for BioGUI to connect...")
    print()

    conn, addr = server_socket.accept()
    print(f"✓ Connected from {addr}")
    print("=" * 70)
    print("Receiving packets... (Ctrl+C to stop)")
    print("=" * 70)
    print()

    packet_count = 0
    last_counter = None
    config_ids_seen = set()

    try:
        while True:
            # Receive packet
            packet = recv_exact(conn, packet_size)
            packet_count += 1

            # Decode
            decoded = decode_packet(packet)

            # Extract data
            acquisition_number = int(decoded["acquisition_number"][0])
            config_id = int(decoded["tx_rx_id"][0])
            imu = decoded["imu"]
            ax, ay, az = int(imu[0]), int(imu[1]), int(imu[2])
            us_data = decoded["ultrasound"]

            # Track unique config IDs
            config_ids_seen.add(config_id)

            # Check for packet loss
            loss_str = ""
            if last_counter is not None:
                expected = (last_counter + 1) % 65536
                if acquisition_number != expected:
                    loss = (
                        acquisition_number - expected
                        if acquisition_number > expected
                        else (65536 - expected) + acquisition_number
                    )
                    loss_str = f"LOSS: {loss} frame(s)!"
            last_counter = acquisition_number

            # Print loss
            if loss_str.strip():
                print(loss_str)

            # Print packet info, TODO: make cli argument
            if packet_count % 8 == 0:
                prefix = f"Packet #{packet_count:5d}:  "
                print(
                    f"{prefix}Acquisition: {acquisition_number:5d}  Config: {config_id}  "
                    f"IMU: [{ax:6d}, {ay:6d}, {az:6d}]  "
                    f"US: min={us_data.min():5d}, max={us_data.max():5d}, "
                    f"mean={us_data.mean():7.1f}"
                )

    except KeyboardInterrupt:
        print()
        print("=" * 70)
        print(f"Stopped by user. Received {packet_count} packets total.")
        print(f"Config IDs seen: {sorted(config_ids_seen)}")

    except ConnectionError:
        print()
        print("=" * 70)
        print(f"Connection closed. Received {packet_count} packets total.")
        print(f"Config IDs seen: {sorted(config_ids_seen)}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        conn.close()
        server_socket.close()


def main():
    parser = argparse.ArgumentParser(
        description="Test receiver for BioGUI forwarding",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python apps/test_receiver.py
  python apps/test_receiver.py --port 12345
        """,
    )
    parser.add_argument(
        "--host",
        type=str,
        default=BIOGUI_HOST,
        help=f"Host address to bind to (default: {BIOGUI_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=BIOGUI_PORT,
        help=f"TCP port to listen on (default: {BIOGUI_PORT})",
    )
    args = parser.parse_args()

    run_receiver(args.host, args.port)


if __name__ == "__main__":
    main()
