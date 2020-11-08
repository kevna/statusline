#!/usr/bin/python3
import os
import re

from .git import Git

class DirectoryMinify(object):
    VCS = Git()

    def _minify_dir(self, name: str, regex=re.compile("^(\W*\w)")):
        match = regex.match(name)
        if match:
            return match.group(0)
        return name

    def hi(self, text):
        return "\033[94m%s\033[m" % text

    def minify_path(self, path: str, home=os.path.expanduser("~"), keep = 1):
        pathlist = path.replace(home, "~", 1).split(os.sep)
        if len(pathlist) > keep:
            pathlist = list(map(self._minify_dir, pathlist[:-keep])) + pathlist[-keep:]
        return self.hi(os.sep.join(pathlist))

    def _apply_vcs(self, path: str):
        common = os.path.commonpath([path, self.VCS.root_dir])
        return self.minify_path(common) \
                + self.VCS.short_stats() \
                + self.minify_path(path[len(common):])

    def get_statusline(self):
        path = os.getcwd()
        if self.VCS.has_vcs():
            return self._apply_vcs(path)
        return self.minify_path(path)


if __name__ == "__main__":
    print(DirectoryMinify().get_statusline())
