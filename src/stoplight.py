"""A stoplight with three lights, a button, and three modes.

Author: TODO your name
"""

from time import sleep


class Stoplight:
    """Three lights that run one mode at a time, and a button that moves to the next mode."""

    def __init__(self, red, yellow, green, button):
        """Keep the three lights by color, the button, and the mode, starting at normal."""
        # TODO: Store the three Light objects in a dictionary attribute, with the keys
        # "red", "yellow" and "green", and store the button
        # TODO: Store the list of mode names, "normal", "flashing red" and "flashing yellow",
        # and mode (0), requested (False) and cycles (0)
        pass

    def show(self, color):
        """Turn on the light of one color, and turn every other light off."""
        # TODO: Loop over the dictionary of lights
        pass

    def all_off(self):
        """Turn every light off."""
        # TODO
        pass

    def wait(self, seconds):
        """Wait for a number of seconds, checking the button every tenth of a second."""
        # TODO: For each tenth of a second in seconds, sleep(0.1), then check the button.
        # A press sets requested to True
        pass

    def mode_name(self):
        """Return the name of the current mode."""
        # TODO
        return "normal"

    def run_cycle(self):
        """Run one cycle of the current mode, then move to the next mode if the button asked."""
        # TODO: Run the current mode with self.show, self.all_off and self.wait
        # TODO: When requested is True, move mode to the next mode, back to 0 after the last
        # one, and set requested back to False
        # TODO: Add 1 to cycles
        pass
