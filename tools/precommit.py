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


if __name__ == "__main__":
    main()
