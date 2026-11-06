"""The modes of the stoplight, and when to move to the next one.

Author: TODO your name
"""


class Modes:
    """The list of modes, the current mode, and whether the button asked for the next one."""

    def __init__(self, button):
        """Keep the button and the list of mode names, starting at normal."""
        # TODO: Store the button
        # TODO: Store the list of mode names, "normal", "flashing red" and "flashing yellow",
        # and mode (0), requested (False) and cycles (0)
        pass

    def wait(self, seconds):
        """Wait for a number of seconds, remembering a press of the button."""
        # TODO: Call the button's watch(seconds). When it returns True, set requested to True
        pass

    def mode_name(self):
        """Return the name of the current mode."""
        # TODO
        return "normal"

    def end_cycle(self):
        """Count a finished cycle, and move to the next mode if the button asked."""
        # TODO: Add 1 to cycles
        # TODO: When requested is True, move mode to the next mode, back to 0 after the last
        # one, and set requested back to False
        pass
