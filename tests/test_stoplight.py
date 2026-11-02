"""Automated checks for Lab 7: Stoplight.

Each class is checked on its own. The Light and Button checks make objects of your
class on a pretend board. The Stoplight checks hand your class pretend lights and
a pretend button, so they pass or fail on stoplight.py alone, whatever state the
other files are in. The program check runs main with all four files together and
reads only the stoplight log at the end, never the narrative lines. Log values
forgive extra spaces, letter case, and a missing colon.

Time passes only when your code calls sleep, so a loop that watches the button
without sleeping is stopped. When a check fails, the assertion message says what
came out wrong and what was expected. gatorgrade does not show that message
itself; it prints the pytest command to run.
"""

import re
from unittest.mock import patch

import mockro
from machine import Pin

# More button reads than this means the program is stuck waiting.
MOST_READS = 20000


class Board:
    """The pins of a pretend Pico, told apart by GP number.

    `presses` is a list of (start, end) times in seconds: the button reads 0 while
    the clock is inside one of them. `reads` is a list of values the button reads
    in turn instead, for checks that never sleep. `clock` adds up every sleep.
    """

    def __init__(self, presses=None, reads=None):
        self.presses = list(presses or [])
        self.reads_left = list(reads) if reads is not None else None
        self.clock = 0.0
        self.reads = 0
        self.numbers = {}
        self.inputs = set()
        self.lit = {}
        self.on_calls = {}

    def sleep(self, seconds=0, *rest):
        self.clock += seconds

    def number(self, pin):
        if id(pin) not in self.numbers:
            for args, _ in mockro.get_recorder().calls("machine.Pin.init"):
                if len(args) >= 3 and args[0] is pin:
                    self.numbers[id(pin)] = args[2]
                    if len(args) >= 4 and args[3] == Pin.IN:
                        self.inputs.add(args[2])
        return self.numbers.get(id(pin))

    def value(self, pin, *rest):
        # mockro passes the Pin twice, then the argument: (pin, pin, x)
        x = rest[-1] if rest and rest[-1] is not pin else None
        number = self.number(pin)
        if x is None:
            return self.read() if number in self.inputs else int(self.lit.get(number, False))
        self.set(number, bool(x))
        return 0

    def read(self):
        self.reads += 1
        if self.reads > MOST_READS:
            raise AssertionError(
                f"the button was read {MOST_READS} times with the clock at {self.clock:.1f} seconds, "
                f"so the program was stuck: every loop that watches the button has to sleep"
            )
        if self.reads_left is not None:
            return self.reads_left.pop(0) if self.reads_left else 1
        return 0 if any(start <= self.clock < end for start, end in self.presses) else 1

    def on(self, pin, *rest):
        self.set(self.number(pin), True)

    def off(self, pin, *rest):
        self.set(self.number(pin), False)

    def set(self, number, lit):
        self.lit[number] = lit
        if lit:
            self.on_calls[number] = self.on_calls.get(number, 0) + 1


def on_board(board, action):
    """Run `action()` with the pins wired to `board` and sleep patched."""
    mockro.get_recorder().clear()
    stubs = [patch("time.sleep", side_effect=board.sleep)]
    try:
        import stoplight

        if hasattr(stoplight, "sleep"):
            stubs.append(patch.object(stoplight, "sleep", side_effect=board.sleep))
    except Exception:
        pass
    try:
        with mockro.override(machine_Pin_value=board.value, machine_Pin_on=board.on, machine_Pin_off=board.off):
            for stub in stubs:
                stub.start()
            try:
                return action()
            finally:
                for stub in stubs:
                    stub.stop()
    except AssertionError:
        raise
    except Exception as exc:
        raise AssertionError(f"the code stopped with {type(exc).__name__}: {exc}") from None


def test_a_light_turns_on_and_off_and_counts():
    from light import Light

    board = Board()

    def action():
        light = Light(15, "red")
        seen = [(light.color, light.lit, light.times_lit, board.lit.get(15, False))]
        light.on()
        seen.append((light.color, light.lit, light.times_lit, board.lit.get(15)))
        light.off()
        seen.append((light.color, light.lit, light.times_lit, board.lit.get(15)))
        light.on()
        seen.append((light.color, light.lit, light.times_lit, board.lit.get(15)))
        return seen

    seen = on_board(board, action)
    want = [("red", False, 0, False), ("red", True, 1, True), ("red", False, 1, False), ("red", True, 2, True)]
    steps = ["after Light(15, 'red')", "after on()", "after off()", "after on() again"]
    for step, got, expected in zip(steps, seen, want):
        assert got == expected, (
            f"{step}, (color, lit, times_lit, LED on GP15) was {got}, expected {expected}: "
            f"__init__ stores color, lit as False and times_lit as 0; on() lights the LED, sets lit and adds 1 "
            f"to times_lit; off() turns the LED off and sets lit to False"
        )


def test_a_button_counts_each_new_press():
    from button import Button

    # Up, down for two checks (one press), up, down, up: two presses
    board = Board(reads=[1, 0, 0, 1, 0, 1])

    def action():
        button = Button(16)
        start = button.presses
        results = [button.check() for _ in range(6)]
        return start, results, button.presses

    start, results, presses = on_board(board, action)
    want = [False, True, False, False, True, False]
    assert start == 0, f"presses was {start} right after Button(16), expected 0"
    assert results == want, (
        f"the button read up, down, down, up, down, up, and check() returned {results}, expected {want}: "
        f"return True only when the button reads 0 now and was_down is False"
    )
    assert presses == 2, f"presses was {presses} after two presses, expected 2: add 1 in check() for each new press"


class FakeLight:
    """A pretend Light that writes down what happens to it."""

    def __init__(self, color, timeline, clock):
        self.color = color
        self.lit = False
        self.times_lit = 0
        self.timeline = timeline
        self.clock = clock

    def on(self):
        self.lit = True
        self.times_lit += 1
        self.timeline.append((round(self.clock[0], 1), self.color))

    def off(self):
        self.lit = False


class FakeButton:
    """A pretend Button that is pressed once at each time in `at`."""

    def __init__(self, at, clock):
        self.at = list(at)
        self.clock = clock
        self.presses = 0

    def check(self):
        if self.at and self.clock[0] >= self.at[0]:
            self.at.pop(0)
            self.presses += 1
            return True
        return False


def make_stoplight(presses_at=()):
    """A Stoplight of pretend parts, the timeline of lights turned on, and the clock."""
    from stoplight import Stoplight

    clock = [0.0]
    timeline = []
    lights = {color: FakeLight(color, timeline, clock) for color in ("red", "yellow", "green")}
    button = FakeButton(presses_at, clock)
    stoplight = Stoplight(lights["red"], lights["yellow"], lights["green"], button)
    return stoplight, lights, timeline, clock


def run(stoplight, clock, method, *args):
    """Call a Stoplight method with sleep moving the pretend clock."""

    def tick(seconds=0, *rest):
        clock[0] += seconds

    import stoplight as module

    stubs = [patch("time.sleep", side_effect=tick)]
    if hasattr(module, "sleep"):
        stubs.append(patch.object(module, "sleep", side_effect=tick))
    for stub in stubs:
        stub.start()
    try:
        return getattr(stoplight, method)(*args)
    except AssertionError:
        raise
    except Exception as exc:
        raise AssertionError(f"Stoplight.{method} stopped with {type(exc).__name__}: {exc}") from None
    finally:
        for stub in stubs:
            stub.stop()


def lit_colors(lights):
    return sorted(color for color, light in lights.items() if light.lit)


def test_show_lights_one_color_and_turns_the_others_off():
    stoplight, lights, timeline, clock = make_stoplight()
    run(stoplight, clock, "show", "green")
    assert lit_colors(lights) == ["green"], f"after show('green') the lit lights were {lit_colors(lights)}, expected ['green']"
    run(stoplight, clock, "show", "red")
    assert lit_colors(lights) == ["red"], (
        f"after show('green') then show('red') the lit lights were {lit_colors(lights)}, expected ['red']: "
        f"loop over the lights dictionary and turn off every light that is not the color asked for"
    )
    run(stoplight, clock, "all_off")
    assert lit_colors(lights) == [], f"after all_off() the lit lights were {lit_colors(lights)}, expected none"


def test_the_normal_cycle_is_red_green_yellow():
    stoplight, lights, timeline, clock = make_stoplight()
    assert stoplight.mode_name() == "normal", f"mode_name() was {stoplight.mode_name()!r} for a new Stoplight, expected 'normal'"
    run(stoplight, clock, "run_cycle")
    want = [(0.0, "red"), (3.0, "green"), (6.0, "yellow")]
    assert timeline == want, (
        f"one normal cycle turned on (seconds, color) {timeline}, expected {want}: red for 3 seconds, "
        f"green for 3, yellow for 1, with self.wait between them"
    )
    assert round(clock[0], 1) == 7.0, f"one normal cycle took {clock[0]:.1f} seconds, expected 7.0"
    assert lit_colors(lights) == ["yellow"], f"after one normal cycle the lit lights were {lit_colors(lights)}, expected ['yellow']"
    assert stoplight.cycles == 1, f"cycles was {stoplight.cycles} after one cycle, expected 1"


def test_the_flashing_modes_flash_once_per_cycle():
    for mode, color in ((1, "red"), (2, "yellow")):
        stoplight, lights, timeline, clock = make_stoplight()
        stoplight.mode = mode
        name = stoplight.mode_name()
        run(stoplight, clock, "run_cycle")
        assert timeline == [(0.0, color)], (
            f"one {name!r} cycle turned on (seconds, color) {timeline}, expected [(0.0, {color!r})]: "
            f"{color} on for half a second, then every light off for half a second"
        )
        assert round(clock[0], 1) == 1.0, f"one {name!r} cycle took {clock[0]:.1f} seconds, expected 1.0"
        assert lit_colors(lights) == [], f"after one {name!r} cycle the lit lights were {lit_colors(lights)}, expected none"


def test_a_press_changes_the_mode_when_the_cycle_ends():
    # Pressed one second into a normal cycle: the cycle still finishes as normal.
    stoplight, lights, timeline, clock = make_stoplight(presses_at=[1.0])
    run(stoplight, clock, "run_cycle")
    assert [color for _, color in timeline] == ["red", "green", "yellow"], (
        f"a press during a normal cycle turned on {timeline}, expected red, green and yellow: the cycle in "
        f"progress finishes, and wait only sets requested"
    )
    assert stoplight.mode_name() == "flashing red", (
        f"after a press during a normal cycle the mode was {stoplight.mode_name()!r}, expected 'flashing red'"
    )
    assert stoplight.requested is False, "requested was still True after the mode changed: set it back to False"
    run(stoplight, clock, "run_cycle")
    assert stoplight.mode_name() == "flashing red", (
        f"a cycle with no press changed the mode to {stoplight.mode_name()!r}: change it only when requested is True"
    )
    # From the last mode, a press goes back to the first.
    stoplight, lights, timeline, clock = make_stoplight(presses_at=[0.2])
    stoplight.mode = 2
    run(stoplight, clock, "run_cycle")
    assert stoplight.mode == 0, f"a press during the flashing yellow mode left mode at {stoplight.mode}, expected 0: after the last mode comes the first"


def log_value(out, label):
    """Return the value printed after `label` in the stoplight log, normalized."""
    starts = [line.start() for line in re.finditer(r"^\s*STOPLIGHT\s+LOG", out, re.IGNORECASE | re.MULTILINE)]
    if not starts:
        return None
    words = r"\s+".join(re.escape(word) for word in label.split())
    match = re.search(rf"^[ \t]*{words}[ \t]*:?[ \t]*([^\n]*)", out[starts[-1]:], re.IGNORECASE | re.MULTILINE)
    if match is None:
        return None
    return " ".join(match.group(1).split()).upper().rstrip(".")


def run_program(capsys, presses, cycles, name):
    import main as program

    board = Board(presses=presses)
    answers = [name, str(cycles)]
    with patch("builtins.input", side_effect=lambda prompt="": answers.pop(0) if answers else ""):
        on_board(board, program.main)
    out, err = capsys.readouterr()
    assert err == "", "the program wrote to the error stream:\n" + err
    return out, board


def test_the_program_runs_the_stoplight_and_logs_it(capsys):
    cases = [
        # (presses, cycles, name, Cycles, Mode, Presses, Red lit)
        ([], 2, "Main and Chestnut", "2", "normal", "0", "2"),
        ([(1.0, 1.4)], 3, "Park and North", "3", "flashing red", "1", "3"),
        ([(1.0, 1.4), (7.5, 7.9)], 3, "JJ", "3", "flashing yellow", "2", "2"),
    ]
    for presses, cycles, name, *want in cases:
        out, board = run_program(capsys, presses, cycles, name)
        context = f"{cycles} cycles, button pressed at {[start for start, _ in presses]} seconds"
        for label, expected in zip(("STOPLIGHT LOG", "Cycles", "Mode", "Presses", "Red lit"), [name] + want):
            got = log_value(out, label)
            assert got is not None, f'no "{label}" line was printed in the stoplight log ({context})'
            assert got == expected.upper(), f'the "{label}" line said {got}, expected {expected} ({context})'
        assert not any(board.lit.get(number) for number in (13, 14, 15)), (
            f"a light was still on when the program ended ({context}): call all_off() after the last cycle"
        )
