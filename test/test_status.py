from unittest.mock import patch, MagicMock, call

import pytest

from statusline.status import DirectoryMinify
from statusline.git import Git


@pytest.fixture()
def instance():
    return DirectoryMinify()

@pytest.fixture()
def mock_vcs():
    return MagicMock(spec=Git)


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
def test__apply_vcs(mock_minify, instance, mock_vcs):
    mock_vcs.root_dir = '/home/kevna/.local/share/chezmoi'
    mock_vcs.short_stats.return_value = '\uE0A0master'
    actual = instance._apply_vcs('/home/kevna/.local/share/chezmoi/private_dot_config/i3', mock_vcs)
    assert actual == '~/.l/s/chezmoi\uE0A0master/p/i3'
    assert mock_minify.call_args_list == [
        call('/home/kevna/.local/share/chezmoi'),
        call('/private_dot_config/i3')
    ]


@patch('statusline.status.DirectoryMinify._apply_vcs', return_value='~/.l/s/chezmoi')
@patch('statusline.status.Git')
def test_get_statusline_git(mock_vcs, mock_minify, instance):
    path = '/home/kevna/.local/share/chezmoi'
    mock_bool = mock_vcs.return_value.__bool__
    mock_bool.return_value = True
    instance.VCS = mock_vcs
    actual = instance.get_statusline(path=path)
    assert actual == mock_minify.return_value
    assert mock_bool.called
    assert mock_minify.call_args == call(path, mock_vcs.return_value)


@patch('statusline.status.DirectoryMinify.minify_path', return_value='~/.l/s/chezmoi')
@patch('statusline.status.Git')
def test_get_statusline_nogit(mock_vcs, mock_minify, instance):
    path = '/home/kevna/.local/share/chezmoi'
    mock_bool = mock_vcs.return_value.__bool__
    mock_bool.return_value = False
    instance.VCS = mock_vcs
    actual = instance.get_statusline(path=path)
    assert actual == mock_minify.return_value
    assert mock_bool.called
    assert mock_minify.call_args == call(path)
