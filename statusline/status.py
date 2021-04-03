#!/usr/bin/python3
import os
import re
from typing import cast

from ansi.colour import fg, fx # type: ignore

from statusline.git import Git


def _hilight(text: str) -> str:
    """Helper to colourise path strings.
    :param text: the text to highlight
    :return: the string with colour escapes applied
    """
    return f'{fg.brightblue}{text}{fx.reset}'


class DirectoryMinify:
    """Handle directory shortening and applying VCS."""
    VCS = Git

    @staticmethod
    def _minify_dir(name: str, regex: re.Pattern = re.compile(r'^(\W*\w)')) -> str:
        """Shorten a string to the first group that matches regex.
        :param name: the single name from the path that is being shrunk
        :param regex: the pattern used to minify the name (using group 0)
        :return: the minified name if possible, else the whole name
        """
        if match := regex.match(name):
            return cast(str, match[0])
        return name

    def minify_path(self, path: str, home: str = os.path.expanduser('~'), keep: int = 1) -> str:
        """Minify a path string.
        Substitutes {home} to ~. Each name (every os.sep) is then reduced
        with _minify_dir except for the last {keep} items.
        :param path: the whole path to minify
        :param home: the user's home directory (will be replaced with ~)
        :param keep: the number of complete names to keep at the end
        :return: the minified path
        """
        pathlist = path.replace(home, '~', 1).split(os.sep)
        if len(pathlist) > keep:
            pathlist = list(map(self._minify_dir, pathlist[:-keep])) + pathlist[-keep:]
        return _hilight(os.sep.join(pathlist))

    def _apply_vcs(self, path: str, vcs: Git) -> str:
        """Add VCS status information at the repository root in the path.
        :param path: the original path to generate details from
        :param vcs: the VCS object to apply to the path
        :return: the minified path with repository information inserted
        """
        common = os.path.commonpath([path, vcs.root_dir])
        return self.minify_path(common) \
                + vcs.short_stats() \
                + self.minify_path(path[len(common):])

    def get_statusline(self, path = os.getcwd()) -> str:
        """Generate a string of information to be used in bash prompt.
        This will include the working dir and the short summary from VCS.
        :return: minified working dir with VCS status if available
        """
        path = os.path.abspath(path)
        if vcs := self.VCS(path=path):
            return self._apply_vcs(path, vcs)
        return self.minify_path(path)


if __name__ == '__main__':
    print(DirectoryMinify().get_statusline())
