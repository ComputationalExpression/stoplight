"""Lab 7: Stoplight.

A stoplight at an intersection, built from three Light objects, a Button, Modes and a Stoplight.
Press the button and the light changes its mode when the cycle in progress ends.

This file is provided. Your team writes the four classes it uses.

Author: The Stoplight team
"""

from button import Button
from light import Light
from modes import Modes
from stoplight import Stoplight


def main():
    """Run the stoplight for a number of cycles, then print the stoplight log."""
    print("=" * 50)
    print("STOPLIGHT")
    print("=" * 50)
    intersection = input("Which intersection is this light at? ")
    cycles = int(input("How many cycles should it run? "))

    # The GP numbers match the Lab 5 circuit, so the board needs no new wiring
    red = Light(15, "red")
    yellow = Light(14, "yellow")
    green = Light(13, "green")
    button = Button(16)
    modes = Modes(button)
    stoplight = Stoplight(red, yellow, green, modes)

    print("Press the button to change the mode when the cycle ends")
    for cycle in range(1, cycles + 1):
        stoplight.run_cycle()
        print(f"Cycle {cycle} done, next mode: {modes.mode_name()}")
    # Leave the intersection dark rather than stuck on one color
    stoplight.all_off()

    print()
    print("=" * 50)
    print(f"STOPLIGHT LOG: {intersection}")
    print("=" * 50)
    print(f"Cycles: {modes.cycles}")
    print(f"Mode: {modes.mode_name()}")
    print(f"Presses: {button.presses}")
    print(f"Red lit: {red.times_lit}")


if __name__ == "__main__":
    main()
