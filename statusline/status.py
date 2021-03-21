#!/usr/bin/python3
import os
import re

from ansi.colour import fg, fx

from statusline.git import Git


class DirectoryMinify:
    VCS = Git()

    def _minify_dir(self, name: str, regex=re.compile(r'^(\W*\w)')):
        """Shorten a string to the first group that matches regex."""
        match = regex.match(name)
        if match:
            return match.group(0)
        return name

    def hi(self, text):
        return f'{fg.brightblue}{text}{fx.reset}'

    def minify_path(self, path: str, home=os.path.expanduser('~'), keep = 1):
        """Minify a path string.
        Substitutes home to ~. Each name is then reduced with _minify_dir.
        """
        pathlist = path.replace(home, '~', 1).split(os.sep)
        if len(pathlist) > keep:
            pathlist = list(map(self._minify_dir, pathlist[:-keep])) + pathlist[-keep:]
        return self.hi(os.sep.join(pathlist))

    def _apply_vcs(self, path: str):
        """Add VCS status information at the repository root in the path."""
        common = os.path.commonpath([path, self.VCS.root_dir])
        return self.minify_path(common) \
                + self.VCS.short_stats() \
                + self.minify_path(path[len(common):])

    def get_statusline(self):
        """Minified working dir with VCS status if available."""
        path = os.getcwd()
        if self.VCS.has_vcs():
            return self._apply_vcs(path)
        return self.minify_path(path)


if __name__ == '__main__':
    print(DirectoryMinify().get_statusline())
