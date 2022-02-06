from unittest.mock import patch, MagicMock

import pytest

from statusline.status import DirectoryMinify
from statusline.git import Git


@pytest.fixture()
def instance():
    result = DirectoryMinify()
    result.VCS = vcs = MagicMock(spec=Git)
    vcs.branch = 'master'
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
@patch('statusline.status._hilight', side_effect=lambda x: x)
def test_minify_path(mock, path, expected, instance):
    actual = instance.minify_path(path)
    assert actual == expected


@pytest.mark.parametrize('path, expected', (
    ('/home/kevna', '~'),
    ('/home/kevna/.config', '~/.config'),
))
@patch('statusline.status._hilight', side_effect=lambda x: x)
def test_minify_path_home(mock, path, expected, instance):
    actual = instance.minify_path(path, home='/home/kevna')
    assert actual == expected


@pytest.mark.parametrize('root, stats, path, expected', (
    (
        '~/.local/share/chezmoi',
        '\uE0A0master',
        '~/.local/share/chezmoi/private_dot_config/i3',
        '~/.l/s/chezmoi\uE0A0master/p/i3',
    ),
    (
        '~/Documents/python/statusline/master',
        '\uE0A0',
        '~/Documents/python/statusline/master/statusline',
        '~/D/p/statusline/master\uE0A0/statusline',
    ),
    (
        '~/Documents/python/statusline-master',
        '\uE0A0',
        '~/Documents/python/statusline-master/statusline',
        '~/D/p/statusline-master\uE0A0/statusline',
    ),
))
@patch('statusline.status._hilight', side_effect=lambda x: x)
def test__apply_vcs(mock, root, stats, path, expected, instance):
    instance.VCS.root_dir = root
    instance.VCS.short_stats.return_value = stats
    actual = instance._apply_vcs(path)
    assert actual == expected

@pytest.mark.parametrize('root, stats, path, expected', (
    (
        '~/Documents/python/statusline/feature/newfeature',
        '\uE0A0',
        '~/Documents/python/statusline/feature/newfeature/statusline',
        '~/D/p/s/f/newfeature\uE0A0/statusline',
    ),
))
@patch('statusline.status._hilight', side_effect=lambda x: x)
def test__apply_vcs_with_branch(mock, root, stats, path, expected, instance):
    instance.VCS.root_dir = root
    instance.VCS.branch = 'feature/newfeature'
    instance.VCS.short_stats.return_value = stats
    actual = instance._apply_vcs(path)
    assert actual == expected


@patch('statusline.status.os.getcwd', return_value='/home/kevna/.local/share/chezmoi')
@patch('statusline.status.DirectoryMinify._apply_vcs', return_value='~/.l/s/chezmoi')
def test_get_statusline_git(mock_minify, mock_cwd, instance):
    instance.VCS.__bool__.return_value = True
    actual = instance.get_statusline()
    assert actual == mock_minify.return_value
    assert instance.VCS.__bool__.called
    mock_minify.assert_called_once_with(mock_cwd.return_value)


@patch('statusline.status.os.getcwd', return_value='/home/kevna/.local/share/chezmoi')
@patch('statusline.status.DirectoryMinify.minify_path', return_value='~/.l/s/chezmoi')
def test_get_statusline_nogit(mock_minify, mock_cwd, instance):
    instance.VCS.__bool__.return_value = False
    actual = instance.get_statusline()
    assert actual == mock_minify.return_value
    assert instance.VCS.__bool__.called
    mock_minify.assert_called_once_with(mock_cwd.return_value)
