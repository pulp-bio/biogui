"""
Keyboard Control for Unity
===========================

Pure keyboard control - NO BioGUI/hardware needed.

INPUT:  Keyboard only
OUTPUT: Unity UDP (position, rotation, finger curls)
TERMINAL: ncurses UI showing current state

Use Case:
- Test Unity hand visualization without hardware
- Test individual finger curl values
- Simple position/rotation control

Controls:
- W/A/S/D: Position X/Z
- ↑/↓:     Position Y
- I/K:     Flexion/Extension
- O/U:     Supination/Pronation
- Space:   Toggle close/open (classification mode)
- 1-5:     Individual finger curls (regression mode)
- M:       Toggle classification/regression mode
- R:       Reset position/rotation
- Q:       Quit

Usage:
    python -m apps.keyboard_control
"""

import curses
import time

from core import (
    MOVE_STEP_XZ,
    MOVE_STEP_Y,
    ROT_STEP,
    SEND_RATE,
    UNITY_HOST,
    UNITY_PORT,
    Mode,
    clamp01,
    clamp_flexion,
    clamp_supination,
)
from unity import UnityController

# Curl step per key press in regression mode
CURL_STEP = 0.08


def main(stdscr):
    """Main curses loop for keyboard control."""
    # Initialize Unity controller
    unity = UnityController(host=UNITY_HOST, port=UNITY_PORT, thread_safe=False)

    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)
    stdscr.timeout(0)

    last_send = time.perf_counter()
    send_interval = 1.0 / SEND_RATE
    acc = 0.0

    help1 = "M: toggle mode | WASD/Arrows move | Q/Esc quit"
    help2 = "CLASS: Space open/close, P pinch | REG: 1-5 bend, 6-0 unbend"
    help3 = "Rotation: I/K = Flexion/Extension,  O/U = Supination,  R=reset"

    stdscr.addstr(0, 0, help1)
    stdscr.addstr(1, 0, help2)
    stdscr.addstr(2, 0, help3)

    running = True
    pinch_on = False

    # Track which keys are currently pressed (for continuous movement)
    keys_pressed = set()

    while running:
        now = time.perf_counter()
        dt = now - last_send
        last_send = now
        acc += dt

        # Process keyboard input
        while True:
            ch = stdscr.getch()
            if ch == -1:
                break

            if ch in (ord("q"), ord("Q"), 27):
                running = False
                break

            # Toggle mode
            if ch in (ord("m"), ord("M")):
                if unity.mode == Mode.CLASSIFICATION:
                    unity.mode = Mode.REGRESSION
                else:
                    unity.mode = Mode.CLASSIFICATION

            # Space toggles close/open (works in both modes)
            if ch == ord(" "):
                if unity.gesture == "close":
                    unity.set_gesture("open")
                else:
                    unity.set_gesture("close")
                pinch_on = False

            if unity.mode == Mode.CLASSIFICATION and ch in (ord("p"), ord("P")):
                pinch_on = not pinch_on
                if pinch_on:
                    unity.set_curls([0.92, 0.8, 0.2, 0.16, 0.12])
                else:
                    unity.set_curls([0.0, 0.0, 0.0, 0.0, 0.0])

            # Regression: 1..5 increase curl, 6..0 decrease curl
            if unity.mode == Mode.REGRESSION:
                curls = unity.curls.copy()
                if ch in (ord("1"), ord("2"), ord("3"), ord("4"), ord("5")):
                    i = ch - ord("1")
                    curls[i] = clamp01(curls[i] + CURL_STEP)
                    unity.set_curls(curls)
                if ch in (ord("6"), ord("7"), ord("8"), ord("9"), ord("0")):
                    i = [ord("6"), ord("7"), ord("8"), ord("9"), ord("0")].index(ch)
                    curls[i] = clamp01(curls[i] - CURL_STEP)
                    unity.set_curls(curls)

            # Movement keys - nur in Set aufnehmen
            if ch in (ord("a"), ord("A")):
                keys_pressed.add("a")
            if ch in (ord("d"), ord("D")):
                keys_pressed.add("d")
            if ch in (ord("w"), ord("W")):
                keys_pressed.add("w")
            if ch in (ord("s"), ord("S")):
                keys_pressed.add("s")
            if ch == curses.KEY_UP:
                keys_pressed.add("up")
            if ch == curses.KEY_DOWN:
                keys_pressed.add("down")

            # Rotation (discrete, not continuous)
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

        # Display state
        rot = unity.rotation
        curls = unity.curls

        stdscr.addstr(
            4,
            0,
            f"mode: {unity.mode:>12}                           ",
        )
        stdscr.addstr(
            5,
            0,
            f"rot:  flex={rot[0]: 6.1f}  supin={rot[2]: 6.1f}                           ",
        )
        stdscr.addstr(
            6,
            0,
            f"curls T I M R P: {curls[0]:.2f} {curls[1]:.2f} "
            f"{curls[2]:.2f} {curls[3]:.2f} {curls[4]:.2f}   ",
        )
        stdscr.refresh()

        # Send at fixed rate
        if acc >= send_interval:
            delta_x = 0.0
            delta_y = 0.0
            delta_z = 0.0

            if "a" in keys_pressed:
                delta_x -= MOVE_STEP_XZ
            if "d" in keys_pressed:
                delta_x += MOVE_STEP_XZ
            if "w" in keys_pressed:
                delta_z += MOVE_STEP_XZ
            if "s" in keys_pressed:
                delta_z -= MOVE_STEP_XZ
            if "up" in keys_pressed:
                delta_y += MOVE_STEP_Y
            if "down" in keys_pressed:
                delta_y -= MOVE_STEP_Y

            unity.set_position_delta(delta_x, delta_y, delta_z)
            unity.send()

            # Clear keys after sending
            keys_pressed.clear()

            acc -= send_interval

        time.sleep(0.005)

    unity.close()


if __name__ == "__main__":
    print("=" * 70)
    print("Keyboard Control for Unity Hand Visualization")
    print("=" * 70)
    print(f"Unity connection: {UNITY_HOST}:{UNITY_PORT}")
    print(f"Send rate: {SEND_RATE} Hz")
    print("=" * 70)
    print()

    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
