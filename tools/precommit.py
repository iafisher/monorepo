#!/usr/bin/env python3
"""
Check staged files before committing them.

This script is called by .git/hooks/pre-commit, which runs before every git commit
unless the --no-verify flag is passed.
"""
import os
import subprocess
import sys
from collections import namedtuple

from common.pycommon import blue, green, plural, red


Problem = namedtuple("Problem", ["path", "message", "fixable", "fix_command"])
Problem.__new__.__defaults__ = (False, None)

RepoInfo = namedtuple("RepoInfo", ["staged_files", "unstaged_files"])


def main():
    repo_info = get_repo_info()

    affected_tests_result = check_affected_tests(repo_info)
    if not affected_tests_result:
        print(f"{red('ERROR')}: affected tests did not pass.", file=sys.stderr)
        sys.exit(1)

    problems = []
    for staged_file in repo_info.staged_files:
        staged_file_problems = check_file(staged_file, repo_info)
        problems.extend(staged_file_problems)

    if problems:
        for problem in problems:
            print_problem(problem)

        print(f"\n{red(plural(len(problems), 'issue'))} detected.", file=sys.stderr)

        fixable_problems = [problem for problem in problems if problem.fixable]
        if fixable_problems:
            msg = f"Fix {len(fixable_problems)} of {plural(len(problems), 'issue')}"
            if len(fixable_problems) == len(problems):
                msg = green(msg)
            else:
                msg = blue(msg)

            print(file=sys.stderr)
            print(f"{msg} with:", file=sys.stderr)

            paths_to_fix = set()
            for problem in fixable_problems:
                paths_to_fix.add(problem.path)
                # The only time that problem.fix_command should be falsey when
                # problem.fixable is True is for unstaged changes to a staged file,
                # because that problem is solved by the 'git add' command which must be
                # applied at the end.
                if problem.fix_command:
                    print(f"    {problem.fix_command} && \\", file=sys.stderr)

            # 'git add' all the files that the fixes changed.
            paths_to_fix_as_str = " ".join(map(repr, sorted(paths_to_fix)))
            print(f"    git add {paths_to_fix_as_str}")
        sys.exit(1)
    else:
        print(f"\n{green('No issues')} detected.", file=sys.stderr)


def check_file(path, repo_info):
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


def check_python_file(path, repo_info):
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


FILETYPE_CHECKS = {".py": check_python_file}


def check_affected_tests(repo_info):
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


def get_repo_info():
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
    return RepoInfo(staged_files=staged_files, unstaged_files=unstaged_files)


def print_problem(problem):
    print(
        f"{red('ERROR')} for {blue(problem.path)}: {problem.message}", file=sys.stderr
    )


if __name__ == "__main__":
    main()
