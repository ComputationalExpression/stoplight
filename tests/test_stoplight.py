"""Automated checks for Lab 7: Stoplight.

Each class is checked on its own. The Light and Button checks make objects of your
class on a pretend board. The Light, Modes and Stoplight checks give your class
pretend versions of the objects it talks to, so they pass or fail on your file
alone, whatever state the other files are in. The program check runs main with all
four classes together and reads only the stoplight log at the end, never the
narrative lines. Log values forgive extra spaces, letter case, and a missing colon.

Time passes only when your code calls sleep, so a loop that watches the button
without sleeping is stopped. When a check fails, the assertion message says what
came out wrong and what was expected. gatorgrade does not show that message
itself; it prints the pytest command to run.
"""

import importlib
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
    for name in ("light", "button", "modes", "stoplight"):
        try:
            module = importlib.import_module(name)
        except Exception:
            continue
        if hasattr(module, "sleep"):
            stubs.append(patch.object(module, "sleep", side_effect=board.sleep))
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
        f"return True only when the button reads 0 now and was not down at the last check"
    )
    assert presses == 2, f"presses was {presses} after two presses, expected 2: add 1 in check() for each new press"


def test_a_button_watches_for_a_number_of_seconds():
    from button import Button

    def watch(presses, *lengths):
        board = Board(presses=presses)

        def action():
            button = Button(16)
            return [button.watch(length) for length in lengths], button.presses

        results, presses_counted = on_board(board, action)
        return results, presses_counted, board.clock

    results, presses, clock = watch([], 1)
    assert results == [False], f"watch(1) returned {results[0]} with no press, expected False"
    assert abs(clock - 1.0) < 0.25, (
        f"watch(1) took {clock:.1f} seconds, expected 1.0: sleep(0.1) on each trip/iteration of range(int(seconds * 10))"
    )
    results, presses, clock = watch([(0.45, 0.62)], 1)
    assert results == [True], f"watch(1) returned {results[0]} with a press partway through, expected True"
    assert presses == 1, f"presses was {presses} after one press during watch, expected 1: call self.check()"
    assert abs(clock - 1.0) < 0.25, (
        f"watch(1) with a press partway through took {clock:.1f} seconds, expected 1.0: keep watching until the time "
        f"is up, then return"
    )
    results, presses, clock = watch([(0.5, 1.5)], 1, 1)
    assert results == [True, False], (
        f"a press held across two calls of watch(1) returned {results}, expected [True, False]: "
        f"a held button is one press, which self.check() already knows"
    )


class FakeModes:
    """Pretend Modes that writes down each wait, and moves a pretend clock."""

    def __init__(self, name="normal", on_wait=None):
        self.name = name
        self.mode = ["normal", "flashing red", "flashing yellow"].index(name)
        self.requested = False
        self.cycles = 0
        self.clock = 0.0
        self.waits = []
        self.ended_at = []
        self.on_wait = on_wait

    def wait(self, seconds):
        self.waits.append(seconds)
        if self.on_wait is not None:
            self.on_wait(seconds)
        self.clock += seconds

    def mode_name(self):
        return self.name

    def end_cycle(self):
        self.ended_at.append(round(self.clock, 1))


def test_a_light_shines_and_flashes():
    from light import Light

    board = Board()

    def action():
        light = Light(15, "red")
        seen = []
        modes = FakeModes(on_wait=lambda seconds: seen.append((seconds, board.lit.get(15, False))))
        light.shine(3, modes)
        after_shine = (list(seen), board.lit.get(15), light.lit, light.times_lit)
        seen.clear()
        light.flash(0.5, modes)
        return after_shine, (list(seen), board.lit.get(15), light.lit, light.times_lit)

    after_shine, after_flash = on_board(board, action)
    want = ([(3, True)], False, False, 1)
    assert after_shine == want, (
        f"after shine(3, modes), (waits with the LED on or off, LED on GP15, lit, times_lit) was {after_shine}, "
        f"expected {want}: call self.on(), then modes.wait(seconds), then self.off()"
    )
    want = ([(0.5, True), (0.5, False)], False, False, 2)
    assert after_flash == want, (
        f"after flash(0.5, modes), (waits with the LED on or off, LED on GP15, lit, times_lit) was {after_flash}, "
        f"expected {want}: call self.shine(seconds, modes), then modes.wait(seconds)"
    )


class ScriptedButton:
    """A pretend Button whose watch returns the next answer in a list."""

    def __init__(self, answers):
        self.answers = list(answers)
        self.watched = []

    def watch(self, seconds):
        self.watched.append(seconds)
        return self.answers.pop(0) if self.answers else False


def test_modes_remember_a_press_while_waiting():
    from modes import Modes

    button = ScriptedButton([False, True, False])
    modes = Modes(button)
    assert modes.mode == 0 and modes.requested is False and modes.cycles == 0, (
        f"a new Modes had (mode, requested, cycles) {(modes.mode, modes.requested, modes.cycles)}, expected (0, False, 0)"
    )
    assert modes.mode_name() == "normal", f"mode_name() was {modes.mode_name()!r} for a new Modes, expected 'normal'"
    modes.wait(3)
    assert button.watched == [3], f"wait(3) called the button's watch with {button.watched}, expected [3]"
    assert modes.requested is False, "requested became True though watch returned False"
    modes.wait(1)
    assert modes.requested is True, "requested stayed False though watch returned True: a press sets it to True"
    modes.wait(1)
    assert modes.requested is True, (
        "requested went back to False when a later watch returned False: only end_cycle sets it back"
    )
    assert modes.mode == 0, f"wait moved mode to {modes.mode}, expected 0: the mode changes only in end_cycle"


def test_modes_move_on_only_when_a_cycle_ends():
    from modes import Modes

    modes = Modes(ScriptedButton([]))
    modes.end_cycle()
    assert modes.cycles == 1, f"cycles was {modes.cycles} after one end_cycle, expected 1"
    assert modes.mode_name() == "normal", (
        f"a cycle with no press changed the mode to {modes.mode_name()!r}: change it only when requested is True"
    )
    for want in ("flashing red", "flashing yellow", "normal"):
        modes.requested = True
        modes.end_cycle()
        assert modes.mode_name() == want, (
            f"after a requested change the mode was {modes.mode_name()!r}, expected {want!r}: after the last mode "
            f"comes the first"
        )
        assert modes.requested is False, "requested was still True after the mode changed: set it back to False"
    assert modes.cycles == 4, f"cycles was {modes.cycles} after four end_cycle calls, expected 4"


class FakeLight:
    """A pretend Light that writes down when it comes on."""

    def __init__(self, color, timeline):
        self.color = color
        self.lit = False
        self.times_lit = 0
        self.timeline = timeline

    def on(self):
        self.lit = True
        self.times_lit += 1

    def off(self):
        self.lit = False

    def shine(self, seconds, modes):
        self.on()
        self.timeline.append((round(modes.clock, 1), self.color))
        modes.wait(seconds)
        self.off()

    def flash(self, seconds, modes):
        self.shine(seconds, modes)
        modes.wait(seconds)


def make_stoplight(name="normal"):
    """A Stoplight of pretend parts, its lights, the timeline of lights turned on, and its modes."""
    from stoplight import Stoplight

    timeline = []
    lights = {color: FakeLight(color, timeline) for color in ("red", "yellow", "green")}
    modes = FakeModes(name)
    stoplight = Stoplight(lights["red"], lights["yellow"], lights["green"], modes)
    return stoplight, lights, timeline, modes


def lit_colors(lights):
    return sorted(color for color, light in lights.items() if light.lit)


def run(stoplight, method):
    """Call a Stoplight method, turning a crash into a sentence."""
    try:
        return getattr(stoplight, method)()
    except AssertionError:
        raise
    except Exception as exc:
        raise AssertionError(f"Stoplight.{method} stopped with {type(exc).__name__}: {exc}") from None


def test_the_stoplight_keeps_its_lights_in_a_dictionary():
    stoplight, lights, timeline, modes = make_stoplight()
    stored = [value for value in vars(stoplight).values() if isinstance(value, dict)]
    assert any(set(value) == {"red", "yellow", "green"} for value in stored), (
        'found no dictionary attribute with the keys "red", "yellow" and "green"'
    )
    for light in lights.values():
        light.on()
    run(stoplight, "all_off")
    assert lit_colors(lights) == [], f"after all_off() the lit lights were {lit_colors(lights)}, expected none"


def test_the_normal_cycle_is_red_green_yellow():
    stoplight, lights, timeline, modes = make_stoplight()
    run(stoplight, "run_cycle")
    want = [(0.0, "red"), (3.0, "green"), (6.0, "yellow")]
    assert timeline == want, (
        f"one normal cycle turned on (seconds, color) {timeline}, expected {want}: red shines for 3 seconds, "
        f"green for 3, yellow for 1"
    )
    assert abs(modes.clock - 7.0) < 0.25, f"one normal cycle took {modes.clock:.1f} seconds, expected 7.0"
    assert modes.ended_at == [7.0], (
        f"end_cycle was called at {modes.ended_at} seconds, expected once, at 7.0, after the last light"
    )


def test_the_flashing_modes_flash_once_per_cycle():
    for name, color in (("flashing red", "red"), ("flashing yellow", "yellow")):
        stoplight, lights, timeline, modes = make_stoplight(name)
        run(stoplight, "run_cycle")
        assert timeline == [(0.0, color)], (
            f"one {name!r} cycle turned on (seconds, color) {timeline}, expected [(0.0, {color!r})]: "
            f"flash the {color} light with 0.5 seconds"
        )
        assert round(modes.clock, 1) == 1.0, f"one {name!r} cycle took {modes.clock:.1f} seconds, expected 1.0"
        assert lit_colors(lights) == [], f"after one {name!r} cycle the lit lights were {lit_colors(lights)}, expected none"
        assert modes.ended_at == [1.0], (
            f"end_cycle was called at {modes.ended_at} seconds in a {name!r} cycle, expected once, at 1.0"
        )


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
            f"a light was still on when the program ended ({context}): shine and flash leave a light off, and all_off turns every light off"
        )
