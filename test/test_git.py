from unittest.mock import patch, PropertyMock, call
from subprocess import CalledProcessError
from types import SimpleNamespace

import pytest

from statusline.git import AheadBehind, Status, Git


@pytest.fixture()
def git():
    return Git('master', None, Status())


class TestAheadBehind:
    @pytest.mark.parametrize('args, expected', (
        ((), ''),
        ((4, 0), '\001\033[32m\002↑4\001\033[0m\002'),
        ((0, 2), '\001\033[31m\002↓2\001\033[0m\002'),
        ((2, 4), '\001\033[32m\002↑2\001\033[31m\002↓4\001\033[0m\002'),
    ))
    def test_str(self, args, expected):
        ahead_behind = AheadBehind(*args)
        assert f'{ahead_behind}' == expected


class TestStatus:
    @pytest.mark.parametrize('args, expected', (
        ((), False),
        ((1, 0, 0, 0), True),
        ((0, 1, 0, 0), True),
        ((0, 0, 1, 0), True),
        ((0, 0, 0, 1), True),
        ((0, 5, 7, 2), True),
    ))
    def test_bool(self, args, expected):
        status = Status(*args)
        assert bool(status) == expected

    @pytest.mark.parametrize('args, expected', (
        ((), ''),
        ((1, 0, 0, 0), '\001\033[91;1m\0021\001\033[0m\002'),
        ((0, 1, 0, 0), '\001\033[32m\0021\001\033[0m\002'),
        ((0, 1, 0, 0), '\001\033[32m\0021\001\033[0m\002'),
        ((0, 0, 1, 0), '\001\033[31m\0021\001\033[0m\002'),
        ((0, 0, 0, 1), '\001\033[90m\0021\001\033[0m\002'),
        ((1, 5, 7, 2), '\001\033[91;1m\0021\001\033[0m\002\001\033[32m\0025\001\033[31m\0027\001\033[90m\0022\001\033[0m\002'),
    ))
    def test_str(self, args, expected):
        status = Status(*args)
        assert f'{status}' == expected



class TestGit:
    @pytest.mark.parametrize('porcelain, expected', (
        ('''
# branch.oid (initial)
# branch.head (detached)
1 MM N... 100644 100644 100644 3e2ceb914cf9be46bf235432781840f4145363fd 3e2ceb914cf9be46bf235432781840f4145363fd README.md
        ''', Git('(detached)', None, Status(0, 1, 1, 0))),
        ('''
# branch.oid 51c9c58e2175b768137c1e38865f394c76a7d49d
# branch.head master
# branch.upstream origin/master
# branch.ab +1 -10
# stash 3
1 .M N... 100644 100644 100644 3e2ceb914cf9be46bf235432781840f4145363fd 3e2ceb914cf9be46bf235432781840f4145363fd Gopkg.lock
1 .M N... 100644 100644 100644 cecb683e6e626bcba909ddd36d3357d49f0cfd09 cecb683e6e626bcba909ddd36d3357d49f0cfd09 Gopkg.toml
1 .M N... 100644 100644 100644 aea984b7df090ce3a5826a854f3e5364cd8f2ccd aea984b7df090ce3a5826a854f3e5364cd8f2ccd porcelain.go
1 .D N... 100644 100644 000000 6d9532ba55b84ec4faf214f9cdb9ce70ec8f4f5b 6d9532ba55b84ec4faf214f9cdb9ce70ec8f4f5b porcelain_test.go
2 R. N... 100644 100644 100644 44d0a25072ee3706a8015bef72bdd2c4ab6da76d 44d0a25072ee3706a8015bef72bdd2c4ab6da76d R100 hm.rb     hw.rb
u UU N... 100644 100644 100644 100644 ac51efdc3df4f4fd328d1a02ad05331d8e2c9111 36c06c8752c78d2aff89571132f3bf7841a7b5c3 e85207e04dfdd5eb0a1e9febbc67fd837c44a1cd hw.rb
? _porcelain_test.go
? git.go
? git_test.go
? goreleaser.yml
? vendor/
        ''', Git('master', AheadBehind(1, 10), Status(1, 1, 4, 5), 3)),
    ))
    def test_from_str(self, porcelain, expected):
        actual = Git.from_str(porcelain)
        assert actual == expected

    @pytest.mark.parametrize('cmd, mock, expected_return, expected_call', (
        (
            ['stash', 'list', '--porcelain'],
            SimpleNamespace(stdout=b'stash@{0}\nstash@{1}\n'),
            'stash@{0}\nstash@{1}\n',
            call(['git', 'stash', 'list', '--porcelain'], check=True, capture_output=True),
        ),
    ))
    def test__run_command(self, cmd, mock, expected_return, expected_call, git):
        with patch('statusline.git.run', return_value=mock) as mock_run:
            actual = git._run_command(cmd)
            assert actual == expected_return
            assert mock_run.call_args == expected_call

    @patch('statusline.git.Git._run_command', return_value='~/.local/chezmoi\n')
    def test_root_dir_cached(self, mock, git):
        git._root = '/path/'
        assert git.root_dir == '/path/'
        assert not mock.called

    @patch('statusline.git.Git._run_command', return_value='~/.local/chezmoi\n')
    def test_root_dir_calculate(self, mock, git):
        assert git.root_dir == '~/.local/chezmoi'
        assert mock.call_args == call(['rev-parse', '--show-toplevel'])

    @patch('statusline.git.path.getmtime', return_value=1604363715.999)
    def test_last_fetch(self, mock, git):
        git._root = 'root'
        assert git.last_fetch == 1604363715
        assert mock.call_args == call('root/.git/FETCH_HEAD')

    @pytest.mark.parametrize('exists, root, expected', (
        (True, [None], True),
        (False, ['root'], True),
        (False, [''], False),
        (False, [None], False),
        (False, [CalledProcessError(128, '')], False),
    ))
    def test_bool(self, exists, root, expected, git):
        with patch('statusline.git.path.exists', return_value=exists) as mock_exists, \
            patch('statusline.git.Git.root_dir', new_callable=PropertyMock, side_effect=root):
            assert bool(git) == expected
            mock_exists.called_once_with('.git')

    @pytest.mark.parametrize('root, git, expected', (
        # Normal clean repo
        ('~/statusline', Git('master', AheadBehind(), Status()), f'{Git.ICON}master'),
        # Worktree format repo/branch
        ('~/statusline/master', Git('master', AheadBehind(), Status()), f'{Git.ICON}'),
        # Worktree format repo-branch
        ('~/statusline-master', Git('master', AheadBehind(), Status()), f'{Git.ICON}'),
        ('~/statusline/feature', Git('feature/vcs_path_support', AheadBehind(), Status()), f'{Git.ICON}feature/vcs_path_support'),
        (
            '~/statusline',
            Git('feature/vcs_path_support', None, Status()),
            f'{Git.ICON}feature/vcs_path_support\001\033[91;1m\002↯\001\033[0m\002'
        ),
        (
            '~/statusline',
            Git('master', AheadBehind(1, 0), Status(0, 3, 2, 0)),
            f'{Git.ICON}master\001\033[32m\002↑1\001\033[0m\002(\001\033[32m\0023\001\033[31m\0022\001\033[0m\002)',
        ),
        (
            '~/statusline',
            Git('master', AheadBehind(0, 1), Status(untracked=5)),
            f'{Git.ICON}master\001\033[31m\002↓1\001\033[0m\002(\001\033[90m\0025\001\033[0m\002)',
        ),
        (
            '~/statusline',
            Git('DI-121-email_validation', AheadBehind(3, 2), Status(), 1),
            f'{Git.ICON}DI-121-email_validation\001\033[32m\002↑3\001\033[31m\002↓2\001\033[0m\002{{1}}',
        ),
        (
            '~/statusline/DI-121-email_validation',
            Git('DI-121-email_validation', AheadBehind(3, 2), Status(), 1),
            f'{Git.ICON}\001\033[32m\002↑3\001\033[31m\002↓2\001\033[0m\002{{1}}',
        ),
    ))
    def test_short_stats(self, root, git, expected):
        git._root = root
        actual = git.short_stats()
        assert actual == expected
