#!/usr/bin/python3
from os import path
from dataclasses import dataclass
from collections import defaultdict
from typing import Optional, cast

from ansi.colour import fg, bg, fx  # type: ignore
from pygit2 import (
    Repository,
    GIT_STATUS_INDEX_NEW, GIT_STATUS_INDEX_MODIFIED, GIT_STATUS_INDEX_DELETED,
    GIT_STATUS_WT_NEW, GIT_STATUS_WT_MODIFIED, GIT_STATUS_WT_DELETED,
)

from statusline import ansi_patch


@dataclass
class AheadBehind:
    """Model for the distance ahead/behind the remote."""

    ahead: int = 0
    behind: int = 0

    def __str__(self):
        """Generate a short text summary of how far ahead/behind the remote."""
        if self.ahead and self.behind:
            return f'{fg.black+bg.brightred}↕{self.ahead+self.behind}{fx.reset}'
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
        """Test if there is status information in this object to display."""
        # Tested in order of likelyhood for performance
        return bool(self.unstaged or self.untracked or self.staged)

    def __str__(self):
        """Generate a short text summary of changes in working copy."""
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
        self._repo = Repository('.')
        self._root: Optional[str] = None

    def __bool__(self):
        """Simple check for being in a git repo.
        Testing for .git is faster but only works in project root
        alernatively we'll use the git tool.
        """
        return path.exists('.git') \
            or bool(self.root_dir)

    @property
    def root_dir(self) -> str:
        """Property for the root directory.

        This is only generated once so if we
        change repo with this instance it would be wrong.
        :return: the absolute path to the repository root
        """
        if not self._root:
            self._root = self._repo.workdir
        return self._root

    @property
    def branch(self) -> str:
        """Property for the current branch name.
        :return: the current local branch name
        """
        return cast(str, self._repo.head.shorthand)

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

    def ahead_behind(self) -> Optional[AheadBehind]:
        """Count unsynched commits between current branch and it's remote.
        :return: AheadBehind comparing local and remote if remote branch exists
        """
        head = self._repo.head
        try:
            remote = self._repo.lookup_branch(self.branch).remote_name
        except ValueError:
            return None
        return AheadBehind(self._repo.ahead_behind(head, remote))

    @staticmethod
    def _match_flag(flag, matches) -> bool:
        for case in matches:
            if flag & case == case:
                return True
        return False

    def status(self) -> Status:
        """Count the number of changes files in the various statuses git tracks.
        :return: A Status which describes the current state of working copy
        """
        status = self._repo.status()
        result: dict = defaultdict(int)
        for _, flags in status.items():
            if self._match_flag(flags, [GIT_STATUS_WT_NEW]):
                result['untracked'] += 1
            if self._match_flag(flags, [GIT_STATUS_WT_MODIFIED, GIT_STATUS_WT_DELETED]):
                result['unstaged'] += 1
            if self._match_flag(flags, [
                GIT_STATUS_INDEX_NEW,
                GIT_STATUS_INDEX_MODIFIED,
                GIT_STATUS_INDEX_DELETED,
            ]):
                result['staged'] += 1
        return Status(**result)

    def stashes(self) -> int:
        """Count the number of records in the git stash.
        :return: current count of stash records
        """
        return len(self._repo.listall_stashes())

    def short_stats(self) -> str:
        """Generate a short text summary of the repository status.
        Colour coding is done with terminal escapes.
        :return: a short string which summarises repository status
        """
        result = [self.ICON]
        if not self.root_dir.endswith(self.branch):
            # No need for branch if worktree is repo-branch or repo/branch
            result.append(self.branch)
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
