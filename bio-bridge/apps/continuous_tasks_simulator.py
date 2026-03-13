"""
Continuous Tasks Simulator for Unity
=====================================

Pure keyboard control for Unity hand - NO BioGUI/hardware needed.

INPUT:  Keyboard only
OUTPUT: Unity UDP (gesture, position, rotation commands)
TERMINAL: ncurses UI showing current state

Use Case:
- Test Unity tasks without any hardware
- Simulate all gestures, positions, and rotation modes

Controls:
- W/S/D:   Position State → forward/start/right
- ↑/↓:     Y position delta ±
- Space:   Toggle close/open
- B/F/G/H: Gestures → rest/close/open/pinch
- I/K:     Flexion/Extension ± (IMU rotation)
- O/U:     Supination/Pronation ± (IMU rotation)
- R:       Reset rotation
- Q/Esc:   Quit

Usage:
    python -m apps.continuous_tasks_simulator
"""

import curses
import time

from core import (
    MOVE_STEP_Y,
    ROT_STEP,
    SEND_RATE,
    UNITY_HOST,
    UNITY_PORT,
    clamp_flexion,
    clamp_supination,
)
from unity import UnityController


def main(stdscr):
    """Main curses loop for continuous tasks simulation."""

    # Initialize Unity controller
    unity = UnityController(host=UNITY_HOST, port=UNITY_PORT, thread_safe=False)
    unity.reset()

    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)
    stdscr.timeout(0)

    last_send = time.perf_counter()
    send_interval = 1.0 / SEND_RATE
    acc = 0.0

    # Help text
    help_lines = [
        "═══════════════════════════════════════════════════════════════════",
        "  Continuous Tasks Simulator",
        "═══════════════════════════════════════════════════════════════════",
        "",
        "  POSITION:  W = forward   D = right   S = start   ↑/↓ = Y ±",
        "  GESTURE:   Space = toggle   B = rest   F = close   G = open   H = pinch",
        "  ROTATION (IMU):   I/K = Flexion ±   O/U = Supination ±   R = Reset",
        "  QUIT:      Q / Esc",
        "",
        "═══════════════════════════════════════════════════════════════════",
    ]

    for i, line in enumerate(help_lines):
        try:
            stdscr.addstr(i, 0, line)
        except curses.error:
            pass

    running = True
    status_row = len(help_lines) + 1

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

            # Quit
            if ch in (ord("q"), ord("Q"), 27):
                running = False
                break

            # ─────────────────────────────────────────────────────────────
            # Position State (discrete)
            # ─────────────────────────────────────────────────────────────

            if ch in (ord("w"), ord("W")):
                unity.set_position_state("forward")

            if ch in (ord("d"), ord("D")):
                unity.set_position_state("right")

            if ch in (ord("s"), ord("S")):
                unity.set_position_state("start")

            # ─────────────────────────────────────────────────────────────
            # Y Position Delta (for continuous movement)
            # ─────────────────────────────────────────────────────────────

            move_step_y = MOVE_STEP_Y * 0.05
            if ch == curses.KEY_UP:
                unity.set_position_delta(0.0, move_step_y, 0.0)
                unity.send()
                unity.clear_position_delta()
            if ch == curses.KEY_DOWN:
                unity.set_position_delta(0.0, -move_step_y, 0.0)
                unity.send()
                unity.clear_position_delta()

            # ─────────────────────────────────────────────────────────────
            # Gesture
            # ─────────────────────────────────────────────────────────────

            # Space toggles close/open
            if ch == ord(" "):
                if unity.gesture == "close":
                    unity.set_gesture("open")
                else:
                    unity.set_gesture("close")

            if ch in (ord("b"), ord("B")):
                unity.set_gesture("rest")
            if ch in (ord("f"), ord("F")):
                unity.set_gesture("close")
            if ch in (ord("g"), ord("G")):
                unity.set_gesture("open")
            if ch in (ord("h"), ord("H")):
                unity.set_gesture("pinch")

            # ─────────────────────────────────────────────────────────────
            # Rotation (gradual)
            # ─────────────────────────────────────────────────────────────

            # Flexion: I = decrease (extend), K = increase (flex)
            if ch in (ord("i"), ord("I")):
                unity.rotation[0] = clamp_flexion(unity.rotation[0] - ROT_STEP)
            if ch in (ord("k"), ord("K")):
                unity.rotation[0] = clamp_flexion(unity.rotation[0] + ROT_STEP)

            # Supination: O = increase, U = decrease
            if ch in (ord("o"), ord("O")):
                unity.rotation[2] = clamp_supination(unity.rotation[2] + ROT_STEP)
            if ch in (ord("u"), ord("U")):
                unity.rotation[2] = clamp_supination(unity.rotation[2] - ROT_STEP)

            # Reset rotation
            if ch in (ord("r"), ord("R")):
                unity.reset_rotation()

        # ─────────────────────────────────────────────────────────────────
        # Display State
        # ─────────────────────────────────────────────────────────────────

        state = unity.get_state()

        try:
            stdscr.addstr(
                status_row,
                0,
                f"  Position: {state['position_state']:8s}  "
                f"Gesture: {state['gesture']:6s}",
            )
            stdscr.addstr(
                status_row + 1,
                0,
                f"  Rotation (IMU):   flex={state['rotation'][0]:6.1f}°  "
                f"supin={state['rotation'][2]:6.1f}°        ",
            )
            curls = state["curls"]
            stdscr.addstr(
                status_row + 2,
                0,
                f"  Curls:    T={curls[0]:.1f} I={curls[1]:.1f} M={curls[2]:.1f} "
                f"R={curls[3]:.1f} P={curls[4]:.1f}   ",
            )
            delta = state["position_delta"]
            stdscr.addstr(
                status_row + 3,
                0,
                f"  Delta:    dx={delta[0]:.2f} dy={delta[1]:.2f} dz={delta[2]:.2f}   ",
            )
        except curses.error:
            pass

        stdscr.refresh()

        # Send at fixed rate
        while acc >= send_interval:
            unity.send()
            acc -= send_interval

        time.sleep(0.005)

    unity.close()


if __name__ == "__main__":
    print()
    print("═" * 70)
    print("  Continuous Tasks Simulator")
    print("═" * 70)
    print()
    print(f"  Unity: {UNITY_HOST}:{UNITY_PORT}  |  Send rate: {SEND_RATE} Hz")
    print()
    print("  Protocol:")
    print("  ┌─────────────────────────────────────────────────────────────┐")
    print("  │  positionDelta: [dx, dy, dz]                                │")
    print("  │  positionState: 'start' | 'forward' | 'right'               │")
    print("  │  gesture:       'rest' | 'open' | 'close' | 'pinch'         │")
    print("  │  rotation:      [flexion, unused, supination] (absolute)    │")
    print("  │  curls:         [thumb, index, middle, ring, pinky] (abs)   │")
    print("  └─────────────────────────────────────────────────────────────┘")
    print()
    print("  Unity decides which fields to use based on task type.")
    print()
    print("═" * 70)
    print()

    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
