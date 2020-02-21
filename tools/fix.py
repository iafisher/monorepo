"""Automatically fix problems in the working directory."""
import subprocess
import sys

from common.pycommon import blue, green, plural, red
from tools.check import check_repo, print_problem


def main():
    problems = check_repo()
    if problems:
        fixable_problems = [problem for problem in problems if problem.fixable]
        if fixable_problems:
            paths_to_fix = set()
            for problem in fixable_problems:
                paths_to_fix.add(problem.path)
                print(f"{green('Applying fix')} for {blue(problem.path)}: ", end="")
                print(f"{problem.message}")
                print()
                if problem.fix_command:
                    _run_command(problem.fix_command)

            # 'git add' all the files that the fixes changed.
            paths_to_fix_as_str = " ".join(map(repr, sorted(paths_to_fix)))
            cmd = f"    git add {paths_to_fix_as_str}"
            print(f"{green('Staging fixed files')} in git")
            print()
            _run_command(cmd)

        msg = f"{len(fixable_problems)} of {plural(len(problems), 'issue')}"
        if len(fixable_problems) == len(problems):
            msg = green(msg)
            print(f"Fixed {msg}.")
        else:
            msg = blue(msg)
            n = len(problems) - len(fixable_problems)
            print(f"Fixed {msg}. {red(plural(n, 'issue'))} remain.")
    else:
        print(f"\n{green('No issues')} detected.")


def _run_command(cmd):
    print("    " + cmd)
    print()
    result = subprocess.run(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    if result.returncode != 0:
        print(
            f"{red('ERROR')}: "
            + f"command returned with non-zero exit code ({result.returncode})",
            file=sys.stderr,
        )
        stderr_lines = result.stderr.decode("utf-8").splitlines()
        if stderr_lines:
            print()
            for line in result.stderr.decode("utf-8").splitlines():
                print("    " + line)
        sys.exit(1)


if __name__ == "__main__":
    main()
