import unittest
from unittest.mock import patch, PropertyMock, call
from types import SimpleNamespace

from statusline.git import Git, AheadBehind, Status


class Test_Git(unittest.TestCase):
    def setUp(self):
        self.instance = Git()

    def test__run_command(self):
        tests = [
                (["stash", "list", "--porcelain"], SimpleNamespace(stdout=b"stash@{0}\nstash@{1}\n"), "stash@{0}\nstash@{1}\n", call(["git", "stash", "list", "--porcelain"], check=True, capture_output=True)),
        ]
        for cmd, mock, expectedReturn, expectedCall in tests:
            with patch("statusline.git.run", return_value=mock) as mock:
                self.assertEqual(expectedReturn, self.instance._run_command(cmd))
                mock.assert_has_calls([expectedCall])

    def test__count(self):
        tests = [
            (["stash", "list"], "stash@{0}\nstash@{1}\n", 2),
            (["stash", "list", "--porcelain"], None, None),
        ]
        for cmd, mock, expected in tests:
            with patch("statusline.git.Git._run_command", return_value=mock) as mock:
                self.assertEqual(expected, self.instance._count(cmd))
                mock.assert_called_once_with(cmd)

    @patch("statusline.git.Git._run_command", return_value="~/.local/chezmoi\n")
    def test_root_dir_cached(self, mock):
        self.instance._root = "/path/"
        self.assertEqual("/path/", self.instance.root_dir)
        mock.assert_not_called()

    @patch("statusline.git.Git._run_command", return_value="~/.local/chezmoi\n")
    def test_root_dir_calculate(self, mock):
        self.assertEqual("~/.local/chezmoi", self.instance.root_dir)
        mock.assert_called_once_with(["rev-parse", "--show-toplevel"])

    @patch("statusline.git.Git._run_command", return_value="  master  ")
    def test_branch(self, mock):
        self.assertEqual("master", self.instance.branch)
        mock.assert_called_once_with(
            ["rev-parse", "--symbolic-full-name", "--abbrev-ref", "HEAD"]
        )

    @patch("statusline.git.path.getmtime", return_value=1604363715.999)
    def test_last_fetch(self, mock):
        self.instance._root = "root"
        self.assertEqual(1604363715, self.instance.last_fetch)
        mock.assert_called_once_with("root/.git/FETCH_HEAD")

    def test_has_vcs(self):
        tests = [
                (True, None, True),
                (False, "root", True),
                (False, "", False),
                (False, None, False),
                ]
        for exists, root, expected in tests:
            with patch("statusline.git.path.exists", return_value=exists) as mockExists, \
                patch("statusline.git.Git.root_dir", new_callable=PropertyMock, return_value=root) as mockRoot:
                self.assertEqual(expected, self.instance.has_vcs())
                mockExists.called_once_with(".git")

    def test_ahead_behind(self):
        tests = [
            ([0, 0], (0, 0)),
            ([5, 10], (5, 10)),
        ]
        for porcelain, expected in tests:
            with patch("statusline.git.Git._count", side_effect=porcelain) as mock:
                self.assertEqual(expected, self.instance.ahead_behind())
                mock.assert_has_calls(
                    [
                        call(["rev-list", "@{u}..HEAD"]),
                        call(["rev-list", "HEAD..@{u}"]),
                    ]
                )

    def test_status(self):
        tests = [
            ("", (0, 0, 0)),
            ("?? untrack.ed\nM  stag.ed\n M unstag.ed", (1, 1, 1)),
        ]
        for porcelain, expected in tests:
            with patch("statusline.git.Git._run_command", return_value=porcelain) as mock:
                self.assertEqual(expected, self.instance.status())
                mock.assert_called_once_with(["status", "--porcelain"])

    @patch("statusline.git.Git._count", return_value=1)
    def test_stashes(self, mock):
        self.assertEqual(1, self.instance.stashes())
        mock.assert_called_once_with(["stash", "list"])

    # TODO should we mock more of the ansi calls here?
    @patch("statusline.git.rgb.rgb256", return_value="")
    def test_short_stats(self, mockRGB):
        tests = [
            ("master", AheadBehind(0, 0), Status(0, 0, 0), 0, "\uE0A0\033[0mmaster"),
            (
                "master",
                AheadBehind(1, 0),
                Status(3, 2, 0),
                0,
                "\uE0A0\033[0mmaster↑1(\033[32m3\033[31m2\033[0m)",
            ),
            (
                "master",
                AheadBehind(0, 1),
                Status(0, 0, 5),
                0,
                "\uE0A0\033[0mmaster↓1(\033[90m5\033[0m)",
            ),
            (
                "master",
                AheadBehind(3, 2),
                Status(0, 0, 0),
                1,
                "\uE0A0\033[0mmaster\033[30;101m↕5\033[0m{1}",
            ),
        ]
        for branch, ab, status, stashes, expected in tests:
            with patch(
                "statusline.git.Git.branch", new_callable=PropertyMock, return_value=branch
            ) as mockBranch, patch(
                "statusline.git.Git.ahead_behind", return_value=ab
            ) as mockAB, patch(
                "statusline.git.Git.status", return_value=status
            ) as mockStatus, patch(
                "statusline.git.Git.stashes", return_value=stashes
            ) as mockStashes:
                self.assertEqual(expected, self.instance.short_stats())


if __name__ == "__main__":
    unittest.main()
