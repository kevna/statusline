from unittest.mock import patch, PropertyMock, call
from subprocess import CalledProcessError
from types import SimpleNamespace

import pytest

from statusline.git import AheadBehind, Status, Git


@pytest.fixture()
def git():
    return Git()


#@pytest.mark.parametrize('branch, ab, status, stashes, expected', (
#    ('master', AheadBehind(0, 0), Status(0, 0, 0), 0, '\001\033[38;5;202m\002\uE0A0\001\033[0m\002master'),
#    (
#        'master',
#        AheadBehind(1, 0),
#        Status(3, 2, 0),
#        0,
#        '\001\033[38;5;202m\002\uE0A0\001\033[0m\002master↑1(\001\033[32m\0023\001\033[31m\0022\001\033[0m\002)',
#    ),
#    (
#        'master',
#        AheadBehind(0, 1),
#        Status(0, 0, 5),
#        0,
#        '\001\033[38;5;202m\002\uE0A0\001\033[0m\002master↓1(\001\033[90m\0025\001\033[0m\002)',
#    ),
#    (
#        'master',
#        AheadBehind(3, 2),
#        Status(0, 0, 0),
#        1,
#        '\001\033[38;5;202m\002\uE0A0\001\033[0m\002master\001\033[30;101m\002↕5\001\033[0m\002{1}',
#    ),
#))
class Test_AheadBehind:
    @pytest.mark.parametrize('args, expected', (
        ((), ''),
        ((4, 0), '↑4'),
        ((0, 2), '↓2'),
        ((2, 4), '\001\033[30;101m\002↕6\001\033[0m\002'),
    ))
    def test_str(self, args, expected):
        ahead_behind = AheadBehind(*args)
        assert f'{ahead_behind}' == expected


class Test_Status:
    @pytest.mark.parametrize('args, expected', (
        ((), False),
        ((1, 0, 0), True),
        ((0, 1, 0), True),
        ((0, 0, 1), True),
        ((5, 7, 2), True),
    ))
    def test_bool(self, args, expected):
        status = Status(*args)
        assert bool(status) == expected

    @pytest.mark.parametrize('args, expected', (
        ((), ''),
        ((1, 0, 0), '\001\033[32m\0021\001\033[0m\002'),
        ((0, 1, 0), '\001\033[31m\0021\001\033[0m\002'),
        ((0, 0, 1), '\001\033[90m\0021\001\033[0m\002'),
        ((5, 7, 2), '\001\033[32m\0025\001\033[31m\0027\001\033[90m\0022\001\033[0m\002'),
    ))
    def test_str(self, args, expected):
        status = Status(*args)
        assert f'{status}' == expected



class Test_Git:
    @pytest.mark.parametrize('cmd, mock, expected_return, expected_call', (
        (
            ['stash', 'list', '--porcelain'],
            SimpleNamespace(stdout=b'stash@{0}\nstash@{1}\n'),
            'stash@{0}\nstash@{1}\n',
            call(['git', 'stash', 'list', '--porcelain'], check=True, capture_output=True)
        ),
    ))
    def test__run_command(self, cmd, mock, expected_return, expected_call, git):
        with patch('statusline.git.run', return_value=mock) as mock:
            actual = git._run_command(cmd)
            assert actual == expected_return
            assert mock.call_args == expected_call

    @pytest.mark.parametrize('cmd, mock, expected', (
        (['stash', 'list'], '', 0),
        (['stash', 'list'], 'stash@{0}\nstash@{1}\n', 2),
    ))
    def test__count(self, cmd, mock, expected, git):
        with patch('statusline.git.Git._run_command', return_value=mock) as mock:
            actual = git._count(cmd)
            assert actual == expected
            assert mock.call_args == call(cmd)

    @patch('statusline.git.Git._run_command', return_value='~/.local/chezmoi\n')
    def test_root_dir_cached(self, mock, git):
        git._root = '/path/'
        assert git.root_dir == '/path/'
        assert not mock.called

    @patch('statusline.git.Git._run_command', return_value='~/.local/chezmoi\n')
    def test_root_dir_calculate(self, mock, git):
        assert git.root_dir == '~/.local/chezmoi'
        assert mock.call_args == call(['rev-parse', '--show-toplevel'])

    @patch('statusline.git.Git._run_command', return_value='  master  ')
    def test_branch(self, mock, git):
        assert git.branch == 'master'
        assert mock.call_args == call(
            ['rev-parse', '--symbolic-full-name', '--abbrev-ref', 'HEAD']
        )

    @patch('statusline.git.path.getmtime', return_value=1604363715.999)
    def test_last_fetch(self, mock, git):
        git._root = 'root'
        assert git.last_fetch == 1604363715
        assert mock.call_args == call('root/.git/FETCH_HEAD')

    @pytest.mark.parametrize('exists, root, expected', (
        (True, None, True),
        (False, 'root', True),
        (False, '', False),
        (False, None, False),
    ))
    def test_has_vcs(self, exists, root, expected, git):
        with patch('statusline.git.path.exists', return_value=exists) as mock_exists, \
            patch('statusline.git.Git.root_dir', new_callable=PropertyMock, return_value=root):
            actual = git.has_vcs()
            assert actual == expected
            mock_exists.called_once_with('.git')

    def test_has_vcs_error(self, git):
        with patch('statusline.git.path.exists', return_value=False), \
            patch('statusline.git.Git._run_command', side_effect=CalledProcessError(128, '')):
            actual = git.has_vcs()
            assert not actual

    @pytest.mark.parametrize('porcelain, expected', (
        ([0, 0], AheadBehind()),
        ([5, 10], AheadBehind(5, 10)),
    ))
    def test_ahead_behind(self, porcelain, expected, git):
        with patch('statusline.git.Git._count', side_effect=porcelain) as mock:
            actual = git.ahead_behind()
            assert actual == expected
            assert mock.call_args_list == [
                call(['rev-list', '@{u}..HEAD']),
                call(['rev-list', 'HEAD..@{u}']),
            ]

    def test_ahead_behind_noupstream(self, git):
        with patch('statusline.git.Git._count', side_effect=CalledProcessError(128, '')) as mock:
            actual = git.ahead_behind()
            assert actual == AheadBehind()
            assert mock.call_args == call(['rev-list', '@{u}..HEAD'])

    @pytest.mark.parametrize('porcelain, expected', (
        ('', Status()),
        ('?? untrack.ed\nM  stag.ed\n M unstag.ed', Status(1, 1, 1)),
    ))
    def test_status(self, porcelain, expected, git):
        with patch('statusline.git.Git._run_command', return_value=porcelain) as mock:
            actual = git.status()
            assert actual == expected
            assert mock.call_args == call(['status', '--porcelain'])

    @patch('statusline.git.Git._count', return_value=1)
    def test_stashes(self, mock, git):
        actual = git.stashes()
        assert actual == 1
        assert mock.call_args == call(['stash', 'list'])

    @pytest.mark.parametrize('branch, ab, status, stashes, expected', (
        ('master', AheadBehind(0, 0), Status(0, 0, 0), 0, '\001\033[38;5;202m\002\uE0A0\001\033[0m\002master'),
        (
            'master',
            AheadBehind(1, 0),
            Status(3, 2, 0),
            0,
            '\001\033[38;5;202m\002\uE0A0\001\033[0m\002master↑1(\001\033[32m\0023\001\033[31m\0022\001\033[0m\002)',
        ),
        (
            'master',
            AheadBehind(0, 1),
            Status(0, 0, 5),
            0,
            '\001\033[38;5;202m\002\uE0A0\001\033[0m\002master↓1(\001\033[90m\0025\001\033[0m\002)',
        ),
        (
            'master',
            AheadBehind(3, 2),
            Status(0, 0, 0),
            1,
            '\001\033[38;5;202m\002\uE0A0\001\033[0m\002master\001\033[30;101m\002↕5\001\033[0m\002{1}',
        ),
    ))
    def test_short_stats(self, branch, ab, status, stashes, expected, git):
        with patch(
            'statusline.git.Git.branch', new_callable=PropertyMock, return_value=branch
        ), patch(
            'statusline.git.Git.ahead_behind', return_value=ab
        ), patch(
            'statusline.git.Git.status', return_value=status
        ), patch(
            'statusline.git.Git.stashes', return_value=stashes
        ):
            actual = git.short_stats()
            assert actual == expected
