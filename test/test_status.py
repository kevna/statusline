from unittest.mock import patch, Mock, call

import pytest

from statusline.status import DirectoryMinify
from statusline.git import Git


@pytest.fixture()
def instance():
    result = DirectoryMinify()
    result.VCS = Mock(spec=Git)
    return result


@pytest.mark.parametrize('name, expected', (
    ('~', '~'),
    ('~root', '~r'),
    ('private_dot_config', 'p'),
    ('._shares', '._'),
))
def test__minify_dir(name, expected, instance):
    actual = instance._minify_dir(name)
    assert actual == expected


@pytest.mark.parametrize('path, expected', (
    ('~', '~'),
    ('/etc/X11/xorg.conf.d', '/e/X/xorg.conf.d'),
    ('~/.local/share/chezmoi/private_dot_config/i3', '~/.l/s/c/p/i3'),
))
@patch('statusline.status.DirectoryMinify.hi', side_effect=lambda x: x)
def test_minify_path(mock, path, expected, instance):
    actual = instance.minify_path(path)
    assert actual == expected


@pytest.mark.parametrize('path, expected', (
    ('/home/kevna', '~'),
    ('/home/kevna/.config', '~/.config'),
))
@patch('statusline.status.DirectoryMinify.hi', side_effect=lambda x: x)
def test_minify_path_home(mock, path, expected, instance):
    actual = instance.minify_path(path, home='/home/kevna')
    assert actual == expected


@patch('statusline.status.DirectoryMinify.minify_path', side_effect=['~/.l/s/chezmoi', '/p/i3'])
def test__apply_vcs(mock_minify, instance):
    instance.VCS.root_dir = '/home/kevna/.local/share/chezmoi'
    instance.VCS.short_stats.return_value = '\uE0A0master'
    actual = instance._apply_vcs('/home/kevna/.local/share/chezmoi/private_dot_config/i3')
    assert actual == '~/.l/s/chezmoi\uE0A0master/p/i3'
    mock_minify.assert_has_calls([
        call('/home/kevna/.local/share/chezmoi'),
        call('/private_dot_config/i3')
    ])


@patch('statusline.status.os.getcwd', return_value='/home/kevna/.local/share/chezmoi')
@patch('statusline.status.DirectoryMinify._apply_vcs', return_value='~/.l/s/chezmoi')
def test_get_statusline_git(mock_minify, mock_cwd, instance):
    instance.VCS.has_vcs.return_value = True
    actual = instance.get_statusline()
    assert actual == mock_minify.return_value
    assert instance.VCS.has_vcs.called
    mock_minify.assert_called_once_with(mock_cwd.return_value)


@patch('statusline.status.os.getcwd', return_value='/home/kevna/.local/share/chezmoi')
@patch('statusline.status.DirectoryMinify.minify_path', return_value='~/.l/s/chezmoi')
def test_get_statusline_nogit(mock_minify, mock_cwd, instance):
    instance.VCS.has_vcs.return_value = False
    actual = instance.get_statusline()
    assert actual == mock_minify.return_value
    assert instance.VCS.has_vcs.called
    mock_minify.assert_called_once_with(mock_cwd.return_value)
