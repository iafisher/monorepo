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


Problem = namedtuple("Problem", ["path", "message", "fixable", "fix_command"])
Problem.__new__.__defaults__ = (False, None)

RepoInfo = namedtuple("RepoInfo", ["unstaged_files"])


def main():
    # TODO(2020-02-07): For file paths with non-ASCII characters, git diff will print
    # a quoted string with backslash escapes rather than the actual non-ASCII bytes,
    # which hinders detection of non-ASCII file paths. I'd prefer to have git diff print
    # the raw bytes of the file path so this check can detect and reject non-ASCII file
    # paths.
    cmd = ["git", "diff", "--name-only", "--cached"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    staged_files = result.stdout.decode("ascii").splitlines()
    repo_info = get_repo_info()

    problems = []
    for staged_file in staged_files:
        staged_file_problems = check_file(staged_file, repo_info)
        problems.extend(staged_file_problems)

    if problems:
        for problem in problems:
            print_problem(problem)

        print(f"\n{len(problems)} issue(s) detected.", file=sys.stderr)

        fixable_problems = [problem for problem in problems if problem.fixable]
        if fixable_problems:
            print(file=sys.stderr)
            print(
                f"Fix {len(fixable_problems)} of {len(problems)} issue(s) with:",
                file=sys.stderr,
            )
            for i, problem in enumerate(fixable_problems):
                suffix = " && \\" if i != len(fixable_problems) - 1 else ""
                print(f"    {problem.fix_command}{suffix}", file=sys.stderr)
        sys.exit(1)


def check_file(path, repo_info):
    """Return a list of Problem objects."""
    problems = []

    if path in repo_info.unstaged_files:
        problems.append(Problem(path, "file has both staged and unstaged changes"))

    if any(not c.isprintable() for c in path):
        problems.append(Problem(path, "non-printable character in file path"))

    if any(c.isspace() for c in path):
        problems.append(Problem(path, "whitespace character in file path"))

    if any(c == "-" for c in path):
        problems.append(Problem(path, "hyphen in file path"))

    if any(c == "\\" for c in path):
        problems.append(Problem(path, "backslash in file path"))

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
            message="black would reformat",
            fixable=True,
            fix_command=f"black {path!r}",
        )
        problems.append(problem)

    return problems


FILETYPE_CHECKS = {".py": check_python_file}


def get_repo_info():
    cmd = ["git", "diff", "--name-only"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    unstaged_files = result.stdout.decode("ascii").splitlines()
    return RepoInfo(unstaged_files=unstaged_files)


def print_problem(problem):
    print(f"ERROR for {problem.path}: {problem.message}", file=sys.stderr)


if __name__ == "__main__":
    main()
