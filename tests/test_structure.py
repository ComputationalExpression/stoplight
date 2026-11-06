"""Structure, history and comment checks for Lab 7: Stoplight.

The comment check reads the files in src as Python, not as text. The history
checks read the repository's git log: the merges GitHub makes for pull requests,
and who committed to src.
"""

import io
import subprocess
import tokenize
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
FILES = ("light.py", "button.py", "modes.py", "stoplight.py", "main.py")


def git(*args):
    result = subprocess.run(["git", *args], cwd=SRC.parent, capture_output=True, text=True, check=False)
    return result.stdout


def test_pull_requests_were_merged():
    subjects = git("log", "--merges", "--format=%s").splitlines()
    merged = [subject for subject in subjects if "pull request" in subject.lower()]
    assert len(merged) >= 4, (
        f"Found {len(merged)} merged pull requests, expected at least 4: one for each of light.py, button.py, "
        f"modes.py and stoplight.py. Merge with Merge pull request, not Squash and merge, and pull main "
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
