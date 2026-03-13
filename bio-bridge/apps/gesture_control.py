"""
Gesture Control for Unity (2-Class)
===========================================

BioGUI ultrasound → NN gesture prediction → Unity.
Position and rotation controlled via keyboard.

INPUT:  BioGUI TCP (Ultrasound only, no IMU rotation)
OUTPUT: Unity UDP (gesture + keyboard position/rotation)
TERMINAL: ncurses UI showing gesture, position, rotation

Use Case:
- 2-class gesture model (fist/open) with keyboard movement
- Does NOT use IMU for rotation (keyboard only)

Controls:
- W/A/S/D: Position X/Z
- ↑/↓:     Position Y
- I/K:     Flexion/Extension
- O/U:     Supination/Pronation
- R:       Reset position/rotation
- Q:       Quit

Model: Uses DEFAULT_MODEL_PATH (2-class: fist/open)

Usage:
    python -m apps.gesture_control
"""

import curses
import socket
import threading
import time

from core import (
    BIOGUI_HOST,
    BIOGUI_PORT,
    DEFAULT_MODEL_PATH,
    MOVE_STEP_XZ,
    MOVE_STEP_Y,
    ROT_STEP,
    SEND_RATE,
    UNITY_HOST,
    UNITY_PORT,
    WULPUS_PACKET_FORMAT,
    clamp_flexion,
    clamp_supination,
    decode_packet,
    recv_exact,
)
from gesture import GesturePredictor, USDataBuffer
from unity import UnityController


def biogui_receiver_thread(
    predictor: GesturePredictor,
    buffer: USDataBuffer,
    unity: UnityController,
    running: dict,
):
    """
    Background thread that receives data from BioGUI and runs inference.

    Flow:
    1. Receive packet from BioGUI (acquisition_number + imu + tx_rx_id + ultrasound)
    2. Use tx_rx_id to determine which channel to update
    3. Once all channels filled, predict on every update
    4. Update Unity controller with predicted gesture
    """
    conn = None
    srv = None

    try:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((BIOGUI_HOST, BIOGUI_PORT))
        srv.listen(1)
        srv.settimeout(1.0)

        while running["active"]:
            try:
                conn, addr = srv.accept()
                running["biogui_connected"] = True
                break
            except socket.timeout:
                continue

        if not running["active"] or conn is None:
            return

        conn.settimeout(0.1)

        while running["active"]:
            try:
                packet = recv_exact(conn, WULPUS_PACKET_FORMAT.packet_size)
                decoded = decode_packet(packet)

                config_id = int(decoded["tx_rx_id"][0])
                us = decoded["ultrasound"]

                buffer.add_sample_to_channel(us, config_id)

                if not buffer.is_ready():
                    continue

                # Predict on every complete cycle (cfg0)
                if config_id == 0:
                    us_data = buffer.get_data()
                    class_idx, gesture_name, probs = predictor.predict(us_data)
                    confidence = probs[class_idx]
                    unity.update_gesture(class_idx, confidence)

            except socket.timeout:
                continue
            except ConnectionError:
                running["biogui_connected"] = False
                break

    except Exception as e:
        running["error"] = str(e)
        import traceback

        traceback.print_exc()

    finally:
        if conn:
            conn.close()
        if srv:
            srv.close()
        running["biogui_connected"] = False


def main_curses(stdscr):
    """Main curses loop with keyboard control."""
    if not DEFAULT_MODEL_PATH.exists():
        print(f"ERROR: Model not found at {DEFAULT_MODEL_PATH}")
        print("Please train a model first or adjust MODEL_PATH")
        return

    # Initialize components using shared modules
    predictor = GesturePredictor(model_path=DEFAULT_MODEL_PATH)
    buffer = USDataBuffer(thread_safe=True)
    unity = UnityController(host=UNITY_HOST, port=UNITY_PORT)

    running = {"active": True, "biogui_connected": False, "error": None}

    receiver = threading.Thread(
        target=biogui_receiver_thread,
        args=(predictor, buffer, unity, running),
        daemon=True,
    )
    receiver.start()

    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)
    stdscr.timeout(0)

    help1 = "WASD/Arrows: move | I/K: Flex/Ext | O/U: Supination | R: reset rot | Q/Esc: quit"
    help2 = "Neural network controls hand: Fist = close, Open = release"

    last_send = time.perf_counter()
    send_interval = 1.0 / SEND_RATE

    try:
        while running["active"]:
            now = time.perf_counter()

            while True:
                ch = stdscr.getch()
                if ch == -1:
                    break

                if ch in (ord("q"), ord("Q"), 27):
                    running["active"] = False
                    break

                # Movement
                if ch in (ord("a"), ord("A")):
                    unity.position[0] += MOVE_STEP_XZ * 0.05
                if ch in (ord("d"), ord("D")):
                    unity.position[0] -= MOVE_STEP_XZ * 0.05
                if ch in (ord("w"), ord("W")):
                    unity.position[2] -= MOVE_STEP_XZ * 0.05
                if ch in (ord("s"), ord("S")):
                    unity.position[2] += MOVE_STEP_XZ * 0.05
                if ch == curses.KEY_UP:
                    unity.position[1] += MOVE_STEP_Y * 0.05
                if ch == curses.KEY_DOWN:
                    unity.position[1] -= MOVE_STEP_Y * 0.05

                # Rotation
                if ch in (ord("i"), ord("I")):
                    unity.rotation[0] = clamp_flexion(unity.rotation[0] - ROT_STEP)
                if ch in (ord("k"), ord("K")):
                    unity.rotation[0] = clamp_flexion(unity.rotation[0] + ROT_STEP)
                if ch in (ord("o"), ord("O")):
                    unity.rotation[2] = clamp_supination(unity.rotation[2] + ROT_STEP)
                if ch in (ord("u"), ord("U")):
                    unity.rotation[2] = clamp_supination(unity.rotation[2] - ROT_STEP)
                if ch in (ord("r"), ord("R")):
                    unity.reset_rotation()

            # Display status
            state = unity.get_state()
            stdscr.clear()
            stdscr.addstr(0, 0, help1)
            stdscr.addstr(1, 0, help2)
            stdscr.addstr(2, 0, "=" * 70)

            biogui_status = "Connected" if running["biogui_connected"] else "Waiting..."
            stdscr.addstr(
                3, 0, f"BioGUI: {biogui_status:<20} Unity: {UNITY_HOST}:{UNITY_PORT}"
            )

            if buffer.is_ready():
                stdscr.addstr(4, 0, f"Buffer:  {buffer.get_fill_status()}")
            else:
                stdscr.addstr(4, 0, f"Buffer:  {buffer.get_fill_status()} (filling...)")

            stdscr.addstr(
                5,
                0,
                f"Position: x={state['position'][0]: .2f} "
                f"y={state['position'][1]: .2f} z={state['position'][2]: .2f}",
            )
            stdscr.addstr(
                6,
                0,
                f"Rotation: flex={state['rotation'][0]: 6.1f}  "
                f"supin={state['rotation'][2]: 6.1f}",
            )

            hand_visual = "✊ FIST" if state["curls"][0] > 0.5 else "✋ OPEN"
            stdscr.addstr(
                7,
                0,
                f"Gesture:  {state['gesture']:<10} ({state['confidence']:>5.1%})  "
                f"Hand: {hand_visual}",
            )

            if running["error"]:
                stdscr.addstr(9, 0, f"ERROR: {running['error']}", curses.A_BOLD)

            stdscr.refresh()

            if now - last_send >= send_interval:
                unity.send()
                last_send = now

            time.sleep(0.005)

    except Exception:
        running["active"] = False
        raise
    finally:
        unity.close()
        receiver.join(timeout=2.0)


def main():
    print("=" * 70)
    print("Live Gesture Recognition Control for Unity")
    print("=" * 70)
    print(f"BioGUI connection: {BIOGUI_HOST}:{BIOGUI_PORT}")
    print(f"Unity connection:  {UNITY_HOST}:{UNITY_PORT}")
    print(f"Model: {DEFAULT_MODEL_PATH.name}")
    print(f"Send rate: {SEND_RATE} Hz")
    print("=" * 70)
    print()
    print("Loading model...")

    try:
        curses.wrapper(main_curses)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except FileNotFoundError as e:
        print(f"\nModel not found: {e}")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
