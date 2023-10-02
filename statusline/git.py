#!/usr/bin/python3
from os import path
from subprocess import run, CalledProcessError
from dataclasses import dataclass
from collections import defaultdict
from typing import Optional

from ansi.colour import fg, bg, fx  # type: ignore

from statusline import ansi_patch


@dataclass
class AheadBehind:
    """Model for the distance ahead/behind the remote."""

    ahead: int = 0
    behind: int = 0

    def __str__(self):
        """Generate a short text summary of how far ahead/behind the remote."""
        result = []
        if self.ahead:
            result.append(f'{fg.green}↑{self.ahead}')
        if self.behind:
            result.append(f'{fg.red}↓{self.behind}')
        if result:
            result.append(fx.reset)
        return ''.join(map(str, result))


@dataclass
class Status:
    """Model for the current working status of the repository."""

    unmerged: int = 0
    staged: int = 0
    unstaged: int = 0
    untracked: int = 0

    def __bool__(self):
        """Test if there is status information in this object to display."""
        # Tested in order of likelyhood for performance
        return bool(self.unstaged or self.untracked or self.staged or self.unmerged)

    def __str__(self):
        """Generate a short text summary of changes in working copy."""
        result = []
        if self.unmerged:
            result.extend([fg.brightred+fx.bold, self.unmerged, fx.reset])
        if self.staged:
            result.extend([fg.green, self.staged])
        if self.unstaged:
            result.extend([fg.red, self.unstaged])
        if self.untracked:
            result.extend([fg.brightblack, self.untracked])
        if result and result[-1] != fx.reset:
            result.append(fx.reset)
        return ''.join(map(str, result))


@dataclass
class Git:
    """Get information about the status of the current git repository."""

    # branch logo in git color #f14e32 (colour 202 is ideal)
    # rgb.rgb256(241, 78, 50)
    ICON = f'{ansi_patch.colour256(202)}\uE0A0{fx.reset}'
    branch: str
    ahead_behind: Optional[AheadBehind]
    status: Status
    stashes: int = 0
    _root = None

    @classmethod
    def from_str(cls, porcelain: str):
        branch = ''
        ab = None
        status = Status()
        stashes = 0
        for line in porcelain.splitlines():
            match line.split(' '):
                case ('#', 'branch.head', *name):
                    branch = ' '.join(name)
                case ('#', 'branch.ab', ahead, behind):
                    ab = AheadBehind(int(ahead), int(behind[1:]))
                case ('#', 'stash', count):
                    stashes += int(count)
                case ('u', *_):
                    status.unmerged += 1
                case ('1', file_stat, *_) | ('2', file_stat, *_):
                    if file_stat[0] != '.':
                        status.staged += 1
                    if file_stat[1] != '.':
                        status.unstaged += 1
                case ('?', *_):
                    status.untracked += 1
        return cls(branch=branch, ahead_behind=ab, status=status, stashes=stashes)

    @classmethod
    def from_cmd(cls):
        porcelain = cls._run_command(
            ['status', '--porcelain=v2', '--branch', '--show-stash']
        )
        return cls.from_str(porcelain)

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
        """Run command and handle failures quietly.
        :param command: subcommand and options used to call git
        :return: the stdout resulting from the git command
        """
        return run(
            ['git'] + command,
            check=True,
            capture_output=True
        ).stdout.decode('utf-8')

    @property
    def root_dir(self) -> str:
        """Property for the root directory.

        This is only generated once so if we
        change repo with this instance it would be wrong.
        :return: the absolute path to the repository root
        """
        if not self._root:
            self._root = self._run_command(
                ['rev-parse', '--show-toplevel']
            ).strip()
        return self._root

    @property
    def last_fetch(self) -> int:
        """Get the timestamp of the last git fetch.
        This information could be used to:
            * run a fetch anytime >3h old †
            * colourise short_stats as a reminder to fetch

            † regular fetches may be problematic for --force-with-lease
            see stackoverflow for details
            https://stackoverflow.com/questions/30542491/push-force-with-lease-by-default/43726130#43726130
        :return: the unix timestamp that the last fetch occurred
        """
        return int(path.getmtime(path.join(self.root_dir, '.git/FETCH_HEAD')))

    def short_stats(self) -> str:
        """Generate a short text summary of the repository status.
        Colour coding is done with terminal escapes.
        :return: a short string which summarises repository status
        """
        result = [self.ICON]
        if not self.root_dir.endswith(self.branch):
            # No need for branch if worktree is repo-branch or repo/branch
            result.append(self.branch)
        if ahead_behind := self.ahead_behind:
            result.append(str(ahead_behind))
        else:
            result.append(f'{fg.brightred+fx.bold}↯{fx.reset}')
        if status := self.status:
            result.append(f'({status})')
        if stashes := self.stashes:
            result.append(f'{{{stashes}}}')
        return ''.join(result)


if __name__ == '__main__':
    if git := Git():
        print(git.short_stats())
