"""The push button that asks the stoplight to change its mode.

Author: TODO your name
"""

from time import sleep

from machine import Pin


class Button:
    """A push button that counts each new press."""

    def __init__(self, pin_number):
        """Make a button on the pin numbered pin_number, not yet pressed."""
        # TODO: Make an input Pin with PULL_UP on pin_number and store it as an attribute
        # TODO: Store presses (0), and an attribute that remembers whether the button was down
        # at the last check (False)
        pass

    def check(self):
        """Return True when the button went down since the last check, and False otherwise."""
        # TODO: The button is down when its pin reads 0. When it is down now and was not down
        # at the last check, add 1 to presses and return True. Either way, remember whether it
        # is down for the next check
        return False

    def watch(self, seconds):
        """Watch the button for a number of seconds, and return True if it was pressed."""
        # TODO: Loop over range(int(seconds * 10)), which is one trip/iteration for each tenth of
        # a second. In each one, sleep(0.1), then call self.check()
        # TODO: Keep watching until the time is up, then return True if any check returned True
        return False
