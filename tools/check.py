"""Library to support pre-commit check and fix command."""
import os
import subprocess
import sys
from collections import namedtuple

from common.pycommon import blue, red


Problem = namedtuple("Problem", ["path", "message", "fixable", "fix_command"])
Problem.__new__.__defaults__ = (False, None)

_RepoInfo = namedtuple("_RepoInfo", ["staged_files", "unstaged_files"])


def check_repo():
    """Returns a list of Problem objects."""
    problems = []
    repo_info = _get_repo_info()

    affected_tests_result = _check_affected_tests(repo_info)
    if not affected_tests_result:
        problems.append(Problem(None, "affected tests did not pass"))

    for staged_file in repo_info.staged_files:
        staged_file_problems = _check_file(staged_file, repo_info)
        problems.extend(staged_file_problems)

    return problems


def _check_file(path, repo_info):
    """Returns a list of Problem objects."""
    problems = []

    if path in repo_info.unstaged_files:
        problems.append(
            Problem(path, "file has both staged and unstaged changes", fixable=True)
        )

    if any(not c.isprintable() for c in path):
        problems.append(Problem(path, "non-printable character in file path"))

    if any(c.isspace() for c in path):
        problems.append(Problem(path, "whitespace character in file path"))

    if any(c == "-" for c in path):
        problems.append(Problem(path, "hyphen in file path"))

    if any(c == "\\" for c in path):
        problems.append(Problem(path, "backslash in file path"))

    with open(path, "r", encoding="utf-8") as f:
        contents = f.read()

    do_not_submit = "DO NOT " + "SUBMIT"
    if do_not_submit in contents.upper():
        problems.append(Problem(path, "file contains " + do_not_submit))

    extension = os.path.splitext(path)[1]
    filetype_check = FILETYPE_CHECKS.get(extension)
    if filetype_check:
        filetype_problems = filetype_check(path, repo_info)
        problems.extend(filetype_problems)

    return problems


def _check_python_file(path, repo_info):
    problems = []

    cmd = ["black", "--check", path]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        problem = Problem(
            path=path,
            message="bad formatting",
            fixable=True,
            fix_command=f"black {path!r}",
        )
        problems.append(problem)

    return problems


FILETYPE_CHECKS = {".py": _check_python_file}


def _check_affected_tests(repo_info):
    """Runs the test suite for all packages that were changed.

    Returns True if all tests pass (or if there are no affected tests), False otherwise.

    This check does not run tests for packages that were indirectly affected, e.g. if
    package A depends on package B and a source file in B was changed, only the tests
    for B are run.
    """
    if not repo_info.staged_files:
        return True

    # Get the set of packages that the staged files are in.
    affected_files_as_str = "+".join(repo_info.staged_files)
    cmd = ["bazel", "query", affected_files_as_str, "--output=package"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    affected_packages_as_str = "+".join(
        set(f"//{pkg}:all" for pkg in result.stdout.decode("ascii").splitlines())
    )

    # Get the list of test targets in the affected packages.
    cmd = ["bazel", "query", f"kind(_test, {affected_packages_as_str})"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    affected_tests = set(result.stdout.decode("ascii").splitlines())

    if not affected_tests:
        return True

    for affected_test in affected_tests:
        cmd = ["bazel", "test", affected_test]
        result = subprocess.run(cmd)
        if result.returncode != 0:
            return False

    return True


def _get_repo_info():
    # TODO(2020-02-07): For file paths with non-ASCII characters, git diff will print
    # a quoted string with backslash escapes rather than the actual non-ASCII bytes,
    # which hinders detection of non-ASCII file paths. I'd prefer to have git diff print
    # the raw bytes of the file path so this check can detect and reject non-ASCII file
    # paths.
    cmd = ["git", "diff", "--name-only", "--cached"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    staged_files = result.stdout.decode("ascii").splitlines()

    cmd = ["git", "diff", "--name-only"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    unstaged_files = result.stdout.decode("ascii").splitlines()
    return _RepoInfo(staged_files=staged_files, unstaged_files=unstaged_files)


def print_problem(problem):
    print(
        f"{red('ERROR')} for {blue(problem.path)}: {problem.message}", file=sys.stderr
    )
