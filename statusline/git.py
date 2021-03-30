#!/usr/bin/python3
from os import path
from subprocess import run, CalledProcessError
from dataclasses import dataclass
from collections import defaultdict
from typing import Optional

from ansi.colour import fg, bg, fx # type: ignore

from statusline import ansi_patch


@dataclass
class AheadBehind:
    """Model for the distance ahead/behind the remote."""

    ahead: int = 0
    behind: int = 0

    def __str__(self):
        if self.ahead and self.behind:
            return ''.join([
                str(fg.black+bg.brightred),
                f'↕{self.ahead+self.behind}',
                str(fx.reset),
            ])
        if self.ahead:
            return f'↑{self.ahead}'
        if self.behind:
            return f'↓{self.behind}'
        return ''


@dataclass
class Status:
    """Model for the current working status of the repository."""

    staged: int = 0
    unstaged: int = 0
    untracked: int = 0

    def __bool__(self):
        # Tested in order of likelyhood for performance
        return bool(self.unstaged or self.untracked or self.staged)

    def __str__(self):
        result = []
        if self.staged:
            result.extend([fg.green, self.staged])
        if self.unstaged:
            result.extend([fg.red, self.unstaged])
        if self.untracked:
            result.extend([fg.brightblack, self.untracked])
        if result:
            result.append(fx.reset)
        return ''.join(map(str, result))


class Git:
    """Get information about the status of the current git repository."""

    # branch logo in git color #f14e32 (colour 202 is ideal)
    # rgb.rgb256(241, 78, 50)
    ICON = f'{ansi_patch.colour256(202)}\uE0A0{fx.reset}'

    def __init__(self):
        self._root: Optional[str] = None

    def __bool__(self):
        """Simple check for being in a git repo.
        Testing for .git is faster but only works in project root
        alernatively we'll use the git tool.
        """
        try:
            return path.exists('.git') \
                    or bool(self.root_dir)
        except CalledProcessError:
            return False

    @staticmethod
    def _run_command(command: list) -> str:
        """Run command and handle failures quietly."""
        return run(
                ['git'] + command,
                check=True,
                capture_output=True
                ).stdout.decode('utf-8')

    def _count(self, command: list) -> int:
        """Helper to count the number of records returned from _run_command."""
        rows = self._run_command(command).split('\n')
        rows.remove('')
        return len(rows)

    @property
    def root_dir(self) -> str:
        """Property for the root directory.

        This is only generated once so if we
        change repo with this instance it would be wrong.
        """
        if not self._root:
            self._root = self._run_command(
                    ['rev-parse', '--show-toplevel']
                    ).strip()
        return self._root

    @property
    def branch(self) -> str:
        """Property for the current branch name."""
        return self._run_command(
                ['rev-parse', '--symbolic-full-name', '--abbrev-ref', 'HEAD']
                ).strip()

    @property
    def last_fetch(self) -> int:
        """Get the timestamp of the last git fetch.
        This information could be used to:
            * run a fetch anytime >3h old †
            * colourise short_stats as a reminder to fetch

            † regular fetches may be problematic for --force-with-lease
            see stackoverflow for details
            https://stackoverflow.com/questions/30542491/push-force-with-lease-by-default/43726130#43726130
        """
        return int(path.getmtime(path.join(self.root_dir, '.git/FETCH_HEAD')))

    def ahead_behind(self) -> Optional[AheadBehind]:
        """Count unsynched commits between current branch and it's remote."""
        try:
            ahead = self._count(['rev-list', '@{u}..HEAD'])
            behind = self._count(['rev-list', 'HEAD..@{u}'])
            return AheadBehind(ahead, behind)
        except CalledProcessError:
            # This occurs if there's no upstream repo to compare.
            return None

    def status(self) -> Status:
        """Count the number of changes files in the various statuses git tracks."""
        output = self._run_command(['status', '--porcelain'])
        result: dict = defaultdict(int)
        for line in output.split('\n'):
            if line:
                if line.startswith('??'):
                    result['untracked'] += 1
                else:
                    if line[0] != ' ':
                        result['staged'] += 1
                    if line[1] != ' ':
                        result['unstaged'] += 1
        return Status(**result)

    def stashes(self) -> int:
        """Count the number of records in the git stash."""
        return self._count(['stash', 'list'])

    def short_stats(self) -> str:
        """Generate a short text summary of the repository status.
        Colour coding is done with terminal escapes.
        """
        result = [self.ICON, self.branch]
        if ahead_behind := self.ahead_behind():
            result.append(str(ahead_behind))
        else:
            result.append(f'{fg.brightred}↯{fx.reset}')
        if status := self.status():
            result.append(f'({status})')
        if stashes := self.stashes():
            result.append(f'{{{stashes}}}')
        return ''.join(result)


if __name__ == '__main__':
    if git := Git():
        print(git.short_stats())
