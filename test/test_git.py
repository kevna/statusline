from unittest.mock import patch, PropertyMock, call
from subprocess import CalledProcessError
from types import SimpleNamespace

import pytest

from statusline.git import Git, AheadBehind, Status


@pytest.fixture()
def instance():
    return Git()


@pytest.mark.parametrize('cmd, mock, expected_return, expected_call', (
    (
        ['stash', 'list', '--porcelain'],
        SimpleNamespace(stdout=b'stash@{0}\nstash@{1}\n'),
        'stash@{0}\nstash@{1}\n',
        call(['git', 'stash', 'list', '--porcelain'], check=True, capture_output=True)
    ),
))
def test__run_command(cmd, mock, expected_return, expected_call, instance):
    with patch('statusline.git.run', return_value=mock) as mock:
        actual = instance._run_command(cmd)
        assert actual == expected_return
        assert mock.call_args == expected_call


@pytest.mark.parametrize('cmd, mock, expected', (
    (['stash', 'list'], '', 0),
    (['stash', 'list'], 'stash@{0}\nstash@{1}\n', 2),
))
def test__count(cmd, mock, expected, instance):
    with patch('statusline.git.Git._run_command', return_value=mock) as mock:
        actual = instance._count(cmd)
        assert actual == expected
        assert mock.call_args == call(cmd)


@patch('statusline.git.Git._run_command', return_value='~/.local/chezmoi\n')
def test_root_dir_cached(mock, instance):
    instance._root = '/path/'
    assert instance.root_dir == '/path/'
    assert not mock.called


@patch('statusline.git.Git._run_command', return_value='~/.local/chezmoi\n')
def test_root_dir_calculate(mock, instance):
    assert instance.root_dir == '~/.local/chezmoi'
    assert mock.call_args == call(['rev-parse', '--show-toplevel'])


@patch('statusline.git.Git._run_command', return_value='  master  ')
def test_branch(mock, instance):
    assert instance.branch == 'master'
    assert mock.call_args == call(
        ['rev-parse', '--symbolic-full-name', '--abbrev-ref', 'HEAD']
    )


@patch('statusline.git.path.getmtime', return_value=1604363715.999)
def test_last_fetch(mock, instance):
    instance._root = 'root'
    assert instance.last_fetch == 1604363715
    assert mock.call_args == call('root/.git/FETCH_HEAD')


@pytest.mark.parametrize('exists, root, expected', (
    (True, None, True),
    (False, 'root', True),
    (False, '', False),
    (False, None, False),
))
def test_has_vcs(exists, root, expected, instance):
    with patch('statusline.git.path.exists', return_value=exists) as mock_exists, \
        patch('statusline.git.Git.root_dir', new_callable=PropertyMock, return_value=root):
        actual = instance.has_vcs()
        assert actual == expected
        mock_exists.called_once_with('.git')


@pytest.mark.parametrize('porcelain, expected', (
    ([0, 0], (0, 0)),
    ([5, 10], (5, 10)),
))
def test_ahead_behind(porcelain, expected, instance):
    with patch('statusline.git.Git._count', side_effect=porcelain) as mock:
        actual = instance.ahead_behind()
        assert actual == expected
        assert mock.call_args_list == [
            call(['rev-list', '@{u}..HEAD']),
            call(['rev-list', 'HEAD..@{u}']),
        ]


def test_ahead_behind_noupstream(instance):
    with patch('statusline.git.Git._count', side_effect=CalledProcessError(128, '')) as mock:
        actual = instance.ahead_behind()
        assert actual == (0, 0)
        assert mock.call_args == call(['rev-list', '@{u}..HEAD'])


@pytest.mark.parametrize('porcelain, expected', (
    ('', (0, 0, 0)),
    ('?? untrack.ed\nM  stag.ed\n M unstag.ed', (1, 1, 1)),
))
def test_status(porcelain, expected, instance):
    with patch('statusline.git.Git._run_command', return_value=porcelain) as mock:
        actual = instance.status()
        assert actual == expected
        assert mock.call_args == call(['status', '--porcelain'])


@patch('statusline.git.Git._count', return_value=1)
def test_stashes(mock, instance):
    actual = instance.stashes()
    assert actual == 1
    assert mock.call_args == call(['stash', 'list'])


@pytest.mark.parametrize('branch, ab, status, stashes, expected', (
    ('master', AheadBehind(0, 0), Status(0, 0, 0), 0, '\uE0A0\033[0mmaster'),
    (
        'master',
        AheadBehind(1, 0),
        Status(3, 2, 0),
        0,
        '\uE0A0\033[0mmaster↑1(\033[32m3\033[31m2\033[0m)',
    ),
    (
        'master',
        AheadBehind(0, 1),
        Status(0, 0, 5),
        0,
        '\uE0A0\033[0mmaster↓1(\033[90m5\033[0m)',
    ),
    (
        'master',
        AheadBehind(3, 2),
        Status(0, 0, 0),
        1,
        '\uE0A0\033[0mmaster\033[30;101m↕5\033[0m{1}',
    ),
))
# TODO should we mock more of the ansi calls here?
@patch('statusline.git.rgb.rgb256', return_value='')
def test_short_stats(mock, branch, ab, status, stashes, expected, instance):
    with patch(
        'statusline.git.Git.branch', new_callable=PropertyMock, return_value=branch
    ), patch(
        'statusline.git.Git.ahead_behind', return_value=ab
    ), patch(
        'statusline.git.Git.status', return_value=status
    ), patch(
        'statusline.git.Git.stashes', return_value=stashes
    ):
        actual = instance.short_stats()
        assert actual == expected
