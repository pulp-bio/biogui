"""
Unity Trigger Monitor
======================

Displays gesture triggers from Unity for debugging.

INPUT:  Unity UDP (gesture trigger messages)
OUTPUT: None
TERMINAL: Table showing received triggers (gesture, duration)

Use Case:
- Debug Unity training trigger system
- Verify Unity is sending correct gesture labels
- Monitor training data collection

Usage:
    python -m apps.trigger_monitor
"""

import json
import socket
from datetime import datetime

from core import GESTURE_TO_LABEL

# Monitor listens on a different port than the training receiver
MONITOR_HOST = "127.0.0.1"
MONITOR_PORT = 6000


def main():
    print("=" * 60)
    print("Unity Trigger Monitor")
    print("=" * 60)
    print(f"Listening on {MONITOR_HOST}:{MONITOR_PORT}")
    print(f"Known gestures: {list(GESTURE_TO_LABEL.keys())}")
    print("Ctrl+C to stop")
    print("=" * 60)
    print()
    print(f"{'Time':<12} {'Gesture':<10} {'Duration(ms)':<15}")
    print("-" * 60)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((MONITOR_HOST, MONITOR_PORT))
    sock.settimeout(1.0)

    try:
        while True:
            try:
                data, addr = sock.recvfrom(1024)

                msg = json.loads(data.decode("utf-8").strip())

                gesture = msg.get("g", "unknown")
                duration_ms = msg.get("durMs", 0)

                now = datetime.now().strftime("%H:%M:%S.%f")[:-3]

                print(f"{now:<12} {gesture:<10} {duration_ms:<15.0f}")

            except socket.timeout:
                continue
            except (json.JSONDecodeError, UnicodeDecodeError, KeyError):
                continue

    except KeyboardInterrupt:
        print("\n" + "=" * 70)
        print("Stopped")
        print("=" * 70)
    finally:
        sock.close()


if __name__ == "__main__":
    main()
