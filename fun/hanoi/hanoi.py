"""
Visual solution to Towers of Hanoi problem.

Version: December 2019
"""
import sys
import time


class TowerOfHanoi:
    def __init__(self, n=3):
        letters = [chr(ord("a") + i) for i in range(n)]
        self.pegs = [letters, [], []]
        self.moves = 0

    def move(self, src, dest, restricted=False):
        if restricted and src != 1 and dest != 1:
            raise ValueError(
                "all moves must begin or end at the middle peg in restricted mode"
            )
        if self.pegs[src]:
            disk = self.pegs[src][-1]
            if not self.pegs[dest] or self.pegs[dest][-1] < disk:
                self.pegs[src].pop()
                self.pegs[dest].append(disk)
                self.moves += 1
            else:
                raise ValueError(
                    "cannot put a heavier disk ({}) on top of a lighter one ({})".format(
                        disk, self.pegs[dest][-1]
                    )
                )
        else:
            raise ValueError("there is no disk at peg {}".format(src))

    def move_and_print(self, *args, **kwargs):
        self.move(*args, **kwargs)
        print()
        print()
        print("#{}".format(self.moves))
        print("\n".join("  >  {}".format(" ".join(peg)) for peg in self.pegs))
        time.sleep(0.4)

    def move_between(self, src, dest):
        """
        Move (and print) a disk from src to dest if possible, or from dest to src
        otherwise. If the puzzle is already finished then no move is made, even if one
        was possible.
        """
        if self.finished():
            return
        try:
            self.move_and_print(src, dest)
        except ValueError:
            self.move_and_print(dest, src)

    def finished(self):
        return all(len(peg) == 0 for peg in self.pegs[:-1])


def solve(n):
    """Solve the Tower of Hanoi problem for n disks and three pegs."""
    tower = TowerOfHanoi(n)

    def solve_rec(disks, src, dest, aux):
        if disks == 1:
            tower.move_and_print(src, dest)
        else:
            solve_rec(disks - 1, src, aux, dest)
            tower.move_and_print(src, dest)
            solve_rec(disks - 1, aux, dest, src)

    print(tower)
    try:
        solve_rec(n, 0, 2, 1)
    except ValueError as e:
        print("Error:", e)
    else:
        print("\nSolved in {0.moves} moves.".format(tower))


def solve_iterative(n):
    """
    Solve the problem iteratively.
    
    Algorithm adapted from en.wikipedia.org/wiki/Tower_of_Hanoi
    """
    tower = TowerOfHanoi(n)
    while not tower.finished():
        if n % 2 == 0:
            # A to B
            tower.move_between(0, 1)
            # A to C
            tower.move_between(0, 2)
            # B to C
            tower.move_between(1, 2)
        elif n % 2 == 1:
            # A to C
            tower.move_between(0, 2)
            # A to B
            tower.move_between(0, 1)
            # B to C
            tower.move_between(1, 2)
    print("\nSolved in {0.moves} moves.".format(tower))


def solve_restricted(n):
    """
    Solve the restricted version where all moves must either originate or terminate at
    the middle peg.
    """
    tower = TowerOfHanoi(n)

    def solve(disks, src, dest):
        if disks == 1:
            tower.move_and_print(src, 1, restricted=True)
            tower.move_and_print(1, dest, restricted=True)
        else:
            solve(disks - 1, src, dest)
            tower.move_and_print(src, 1, restricted=True)
            solve(disks - 1, dest, src)
            tower.move_and_print(1, dest, restricted=True)
            solve(disks - 1, src, dest)

    print(tower)
    try:
        solve(n, 0, 2)
    except ValueError as e:
        print("Error:", e)
    else:
        print("\nSolved in {0.moves} moves.".format(tower))


if __name__ == "__main__":
    solve_iterative(int(sys.argv[1]))
