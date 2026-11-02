"""Structure, history and comment checks for Lab 7: Stoplight.

The structure checks read the files in src as Python, not as text, so words in
comments and strings do not count. The history checks read the repository's
git log: the merges GitHub makes for pull requests, and who committed to src.
"""

import ast
import io
import subprocess
import tokenize
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
FILES = ("light.py", "button.py", "stoplight.py", "main.py")


def tree(name):
    return ast.parse((SRC / name).read_text(encoding="utf-8"))


def find_class(name, file_name):
    for node in tree(file_name).body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise AssertionError(f"found no class named {name} in src/{file_name}")


def method(cls, name):
    for node in cls.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"found no method named {name} in class {cls.name}")


def self_calls(node):
    """The names of methods called as self.name(...) inside a node."""
    names = set()
    for call in ast.walk(node):
        if (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id == "self"
        ):
            names.add(call.func.attr)
    return names


def git(*args):
    result = subprocess.run(["git", *args], cwd=SRC.parent, capture_output=True, text=True, check=False)
    return result.stdout


def test_the_stoplight_keeps_its_lights_in_a_dictionary_and_uses_its_own_methods():
    cls = find_class("Stoplight", "stoplight.py")
    init = method(cls, "__init__")
    stores = [
        node for node in ast.walk(init)
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Dict)
        and any(isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self" for t in node.targets)
    ]
    assert stores, "found no dictionary stored as an attribute in Stoplight.__init__: self.lights = {...}"
    called = self_calls(method(cls, "run_cycle"))
    for name in ("show", "wait"):
        assert name in called, f"run_cycle does not call self.{name}(...): use the Stoplight's own methods"
    assert "check" in {
        call.func.attr for call in ast.walk(method(cls, "wait"))
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
    }, "wait does not call the button's check(): check the button on every trip/iteration of its loop"


def test_main_imports_each_class_and_makes_the_objects():
    body = tree("main.py")
    imported = {
        (node.module, alias.name) for node in ast.walk(body)
        if isinstance(node, ast.ImportFrom) for alias in node.names
    }
    for module, name in (("light", "Light"), ("button", "Button"), ("stoplight", "Stoplight")):
        assert (module, name) in imported, f"main.py does not have from {module} import {name}"
    made = [
        call.func.id for call in ast.walk(body)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
    ]
    for name, count in (("Light", 3), ("Button", 1), ("Stoplight", 1)):
        assert made.count(name) >= count, f"main.py makes {made.count(name)} {name} object(s), expected at least {count}"


def test_pull_requests_were_merged():
    subjects = git("log", "--merges", "--format=%s").splitlines()
    merged = [subject for subject in subjects if "pull request" in subject.lower()]
    assert len(merged) >= 4, (
        f"Found {len(merged)} merged pull requests, expected at least 4: one for each of light.py, button.py, "
        f"stoplight.py and main.py. Merge with Merge pull request, not Squash and merge, and pull main "
        f"before you run this check."
    )


def test_teammates_each_committed_to_src():
    roots = git("rev-list", "--max-parents=0", "HEAD").split()
    span = [f"{root}..HEAD" for root in roots] or ["HEAD"]
    authors = set(git("log", "--no-merges", "--format=%ae", *span, "--", "src").split())
    assert len(authors) >= 2, (
        f"Found commits to src from {len(authors)} email address(es). Each teammate commits their own "
        f"file from their own computer."
    )


def comments(name):
    text = (SRC / name).read_text(encoding="utf-8")
    return [tok for tok in tokenize.generate_tokens(io.StringIO(text).readline) if tok.type == tokenize.COMMENT]


def test_no_file_has_a_todo():
    for name in FILES:
        assert "TODO" not in (SRC / name).read_text(encoding="utf-8"), (
            f"src/{name} still has a TODO marker: delete each one once its code is written, including Author"
        )


def test_each_file_has_two_comments():
    for name in FILES:
        found = [tok.string for tok in comments(name) if "TODO" not in tok.string]
        assert len(found) >= 2, (
            f"src/{name} has {len(found)} comment(s) besides TODO markers, expected at least 2: say why, not what"
        )
