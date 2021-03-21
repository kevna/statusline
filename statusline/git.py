#!/usr/bin/python3
from os import path
from subprocess import run, CalledProcessError
from collections import namedtuple, defaultdict

from statusline import ansi_patch
from ansi.colour import fg, bg, fx, rgb

AheadBehind = namedtuple('AheadBehind', ('ahead', 'behind'), defaults=(0, 0))
Status = namedtuple(
        'Status',
        ('staged', 'unstaged', 'untracked'),
        defaults=(0, 0, 0)
        )

class Git:
    """Get information about the status of the current git repository."""

    def __init__(self, path=''):
        self.path = path
        self._root = None

    def _run_command(self, command: list) -> str:
        """Run command and handle failures quietly."""
        if self.path:
            command = ['-C', self._root or self.path] + command
        return run(
                ['git'] + command,
                check=True,
                capture_output=True,
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

    def has_vcs(self) -> bool:
        """Simple check for being in a git repo.
        Testing for .git is faster but only works in project root
        alernatively we'll use the git tool.
        """
        try:
            return path.exists(path.join(self.path, '.git')) \
                    or bool(self.root_dir)
        except CalledProcessError:
            return False

    def ahead_behind(self) -> AheadBehind:
        """Count unsynched commits between current branch and it's remote."""
        try:
            ahead = self._count(['rev-list', '@{u}..HEAD'])
            behind = self._count(['rev-list', 'HEAD..@{u}'])
        except CalledProcessError:
            # This occurs if there's no upstream repo to compare.
            return AheadBehind()
        return AheadBehind(ahead, behind)

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
        # branch logo in git color #f14e32 (colour 202 is ideal)
        # rgb.rgb256(241, 78, 50)
        result = [ansi_patch.colour256(202), '\uE0A0', fx.reset, self.branch]
        ahead_behind = self.ahead_behind()
        if ahead_behind.ahead and ahead_behind.behind:
            result.extend([fg.black+bg.brightred, '↕%d' % sum(ahead_behind), fx.reset])
        elif ahead_behind.ahead:
            result.append('↑%d' % ahead_behind.ahead)
        elif ahead_behind.behind:
            result.append('↓%d' % ahead_behind.behind)
        status = self.status()
        if sum(status):
            result.append('(')
            if status.staged:
                result.extend([fg.green, status.staged])
            if status.unstaged:
                result.extend([fg.red, status.unstaged])
            if status.untracked:
                result.extend([fg.brightblack, status.untracked])
            result.extend([fx.reset, ')'])
        stashes = self.stashes()
        if stashes:
            result.append('{%d}' % stashes)
        return ''.join(map(str, result))


if __name__ == '__main__':
    git = Git()
    if git.has_vcs():
        print(git.short_stats())
