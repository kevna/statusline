# statusline
A minified path inspired by functionality of vim-airline's tabline feature with additional git repository information.
The design allows the user to infer their location using their knowledge of their directory structure whilst taking up significantly less space especially for heavily nested paths.or long directory names.

Each segment of the path is shortened to a minimum meaningful length (see the examples section) with the exception of the basename.
This method may include duplicates for different paths eg. `~/Documents` and `~/Downloads` will both shorten to `~/D`.
The duplication has been considered an acceptable cost since the subdirectories give further context and walking each directory would require significantly more work.
In the case of overbearing doubt (or needing the full path) it's always possible to use pwd.

When the working directory is within a git repository the name of the repo directory is left whole and git repository information is added before the remaining path.
This includes the current branch name, distance ahead/behind upstream and counts of staged, unstaged and untracked files and stash entries.
The remaining path is also minified in the usual manner.

## Code Quality
We have a number of checks in place to ensure the quality of the codebase for this project.
Static analysis is performed using `pylint` for linting and `mypy` for type checking.
Unit testing is done with `pytest` with the `pytest-cov` module also evaluates the test coverage.

In order to install and maintain these development dependencies we use `poetry` which manages the dependency lists and also installed versions within a virtual environment.
This also allows us to run a github workflow to run the static analysis and testing, we require these to pass in order to permit a pull request.
We manually self-review our code however we do not require reviews for PRs since this project is a one-man team and github doesn't allow the developer to review their own code.

## Examples

The current user's home dir is shortened to ~, ordinary directory names are shortened to their first letter.
```
/home/currentuser/Documents/python/statusline -> ~/D/p/statusline
/etc/apt/sources.list.d -> /e/a/sources.list.d
```

Hidden directories which start with dot then include the first character.
Note that this uses regex word characters so other conventions may still fool it
especially the use of `_`.
```
~/.config/git -> ~/.c/git
/._Trashes/subdir -> /._/subdir
```
Since this uses python3 regex this should also work for unicode letters and ideograms - though this is not officially supported.

