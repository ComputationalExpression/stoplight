"""One light of the stoplight.

Author: TODO your name
"""

from machine import Pin


class Light:
    """An LED on one pin, with the color it stands for."""

    def __init__(self, pin_number, color):
        """Make a light on the pin numbered pin_number, starting off."""
        # TODO: Make an output Pin on pin_number and store it as an attribute
        # TODO: Store color, lit (False) and times_lit (0) as attributes
        # TODO: Turn the LED off, so the light starts dark
        pass

    def on(self):
        """Turn the light on, and count one more time it was lit."""
        # TODO: Turn the LED on, set lit to True, and add 1 to times_lit
        pass

    def off(self):
        """Turn the light off."""
        # TODO: Turn the LED off and set lit to False
        pass
