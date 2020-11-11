#!/usr/bin/python3
from os import path
from subprocess import run, CalledProcessError
from collections import namedtuple, defaultdict
from typing import Optional

from ansi.colour import fg, bg, fx

AheadBehind = namedtuple("AheadBehind", ("ahead", "behind"), defaults=(0, 0))
Status = namedtuple(
        "Status",
        ("staged", "unstaged", "untracked"),
        defaults=(0, 0, 0)
        )

class Git(object):
    def __init__(self):
        self._root = None

    def _run_command(self, command: list) -> Optional[str]:
        try:
            return run(
                    ["git"] + command,
                    check=True,
                    capture_output=True
                    ).stdout.decode("utf-8")
        except CalledProcessError as e:
            return None

    def _count(self, command: list) -> int:
        results = self._run_command(command).split("\n")
        results.remove("")
        return len(results)

    @property
    def root_dir(self) -> Optional[str]:
        if not self._root:
            try:
                self._root = self._run_command(
                        ["rev-parse", "--show-toplevel"]
                        ).strip()
            except AttributeError as e:
                pass
        return self._root

    @property
    def branch(self) -> Optional[str]:
        return self._run_command(
                ["rev-parse", "--symbolic-full-name", "--abbrev-ref", "HEAD"]
                ).strip()

    @property
    def last_fetch(self) -> int:
        """
        Get the timestamp of the last git fetch
        this information could be used to:
            * run a fetch anytime >3h old †
            * colourise short_stats as a reminder to fetch

            † regular fetches may be problematic for --force-with-lease
            see stackoverflow for details
            https://stackoverflow.com/questions/30542491/push-force-with-lease-by-default/43726130#43726130
        """
        return int(path.getmtime(path.join(self.root_dir, ".git/FETCH_HEAD")))

    def has_vcs(self) -> bool:
        return path.exists(".git") \
                or bool(self.root_dir)

    def ahead_behind(self) -> AheadBehind:
        ahead = self._count(["rev-list", "@{u}..HEAD"])
        behind = self._count(["rev-list", "HEAD..@{u}"])
        return AheadBehind(ahead, behind)

    def status(self) -> Status:
        output = self._run_command(["status", "--porcelain"])
        result = defaultdict(int)
        for line in output.split("\n"):
            if line:
                if line.startswith("??"):
                    result["untracked"] += 1
                else:
                    if line[0] != " ":
                        result["staged"] += 1
                    if line[1] != " ":
                        result["unstaged"] += 1
        return Status(**result)

    def stashes(self) -> int:
        return self._count(["stash", "list", "--porcelain"])

    def short_stats(self) -> str:
        result = ["\uE0A0", self.branch]
        ab = self.ahead_behind()
        if ab.ahead and ab.behind:
            result.append(bg.brightred("↕%d" % sum(ab)))
        elif ab.ahead:
            result.append("↑%d" % ab.ahead)
        elif ab.behind:
            result.append("↓%d" % ab.behind)
        status = self.status()
        if sum(status):
            result.append("(")
            if status.staged:
                result.extend([fg.green, status.staged])
            if status.unstaged:
                result.extend([fg.red, status.unstaged])
            if status.untracked:
                result.extend([fg.brightblack, status.untracked])
            result.extend([fx.reset, ")"])
        stashes = self.stashes()
        if stashes:
            result.append("{%d}" % stashes)
        return "".join(map(str, result))


if __name__ == "__main__":
    git = Git()
    if git.has_vcs():
        print(git.short_stats())
