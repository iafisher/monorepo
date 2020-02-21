"""
Check staged files before committing them.

This script is called by .git/hooks/pre-commit, which runs before every git commit
unless the --no-verify flag is passed.
"""
import sys

from common.pycommon import blue, green, plural, red
from tools.check import check_repo, print_problem


def main():
    problems = check_repo()
    if problems:
        for problem in problems:
            print_problem(problem)

        fixable_problems = [problem for problem in problems if problem.fixable]
        if fixable_problems:
            msg = f"Fix {len(fixable_problems)} of {plural(len(problems), 'issue')}"
            if len(fixable_problems) == len(problems):
                msg = green(msg)
            else:
                msg = blue(msg)
            print(file=sys.stderr)
            print(f"{msg} with {blue('mn fix')}", file=sys.stderr)

        sys.exit(1)
    else:
        print(f"\n{green('No issues')} detected.", file=sys.stderr)


if __name__ == "__main__":
    main()
