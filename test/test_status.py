import unittest
from unittest.mock import patch, Mock, call

from statusline.status import DirectoryMinify
from statusline.git import Git

class Test_DirectoryMinify(unittest.TestCase):
    def setUp(self):
        self.instance = DirectoryMinify()

    def test__minify_dir(self):
        tests = [
                ("~", "~"),
                ("~root", "~r"),
                ("private_dot_config", "p"),
                ("._shares", "._"),
                ]
        for name, expected in tests:
            self.assertEqual(expected, self.instance._minify_dir(name))

    @patch("statusline.status.DirectoryMinify.hi", side_effect=lambda x: x)
    def test_minify_path(self, mock):
        tests = [
                ("~", "~"),
                ("/etc/X11/xorg.conf.d", "/e/X/xorg.conf.d"),
                ("~/.local/share/chezmoi/private_dot_config/i3", "~/.l/s/c/p/i3"),
                ]
        for path, expected in tests:
            self.assertEqual(expected, self.instance.minify_path(path))

    @patch("statusline.status.DirectoryMinify.hi", side_effect=lambda x: x)
    def test_minify_path_home(self, mock):
        tests = [
                ("/home/kevna", "~"),
                ("/home/kevna/.config", "~/.config"),
                ]
        for path, expected in tests:
            self.assertEqual(
                    expected,
                    self.instance.minify_path(
                        path,
                        home="/home/kevna"
                        )
                    )

    @patch("statusline.status.DirectoryMinify.minify_path", side_effect=["~/.l/s/chezmoi", "/p/i3"])
    def test__apply_vcs(self, mockMinify):
        self.instance.VCS = Mock(spec=Git)
        self.instance.VCS.root_dir = "/home/kevna/.local/share/chezmoi"
        self.instance.VCS.short_stats.return_value = "\uE0A0master"
        self.assertEqual("~/.l/s/chezmoi\uE0A0master/p/i3", self.instance._apply_vcs("/home/kevna/.local/share/chezmoi/private_dot_config/i3"))
        mockMinify.assert_has_calls([call("/home/kevna/.local/share/chezmoi"), call("/private_dot_config/i3")])

    @patch("statusline.status.os.getcwd", return_value="/home/kevna/.local/share/chezmoi")
    @patch("statusline.status.Git.has_vcs", return_value=True)
    @patch("statusline.status.DirectoryMinify._apply_vcs", return_value="~/.l/s/chezmoi")
    def test_get_statusline_git(self, mockMinify, mockVCS, mockCWD):
        self.assertEqual(mockMinify.return_value, self.instance.get_statusline())
        mockVCS.assert_called_once_with()
        mockMinify.assert_called_once_with(mockCWD.return_value)

    @patch("statusline.status.os.getcwd", return_value="/home/kevna/.local/share/chezmoi")
    @patch("statusline.status.Git.has_vcs", return_value=False)
    @patch("statusline.status.DirectoryMinify.minify_path", return_value="~/.l/s/chezmoi")
    def test_get_statusline_nogit(self, mockMinify, mockVCS, mockCWD):
        self.assertEqual(mockMinify.return_value, self.instance.get_statusline())
        mockVCS.assert_called_once_with()
        mockMinify.assert_called_once_with(mockCWD.return_value)


if __name__ == '__main__':
    unittest.main()
