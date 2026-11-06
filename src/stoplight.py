"""A stoplight with three lights and three modes.

Author: TODO your name
"""


class Stoplight:
    """Three lights that run one cycle at a time, in the mode that Modes names."""

    def __init__(self, red, yellow, green, modes):
        """Keep the three lights by color, and the modes."""
        # TODO: Store the three Light objects in a dictionary attribute, with the keys
        # "red", "yellow" and "green", and store modes
        pass

    def all_off(self):
        """Turn every light off."""
        # TODO: Loop over the dictionary of lights
        pass

    def run_cycle(self):
        """Run one cycle of the current mode, then tell the modes that the cycle ended."""
        # TODO: Ask modes for the name of the current mode, and run that mode's cycle with the
        # lights' shine and flash methods
        # TODO: Call the end_cycle method of modes
        pass
