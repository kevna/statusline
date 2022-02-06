# TODO
Features for the future

- [X] add octal 1 and 2 around color escapes
  - this will avoid the escapes messing with line length
- [X] add development venv
  - [X] use pylint and mypy to enforce coding standards
  - [X] move to pytest going forward
- [X] require a github pipeline before reintegration
  - this may require setting up a CI tool to run the tests
  - [ ] we should also check coverage
  - [X] ideally a linting tool
  - [X] turn off requiring code reviews? (currently used to block trunk commits)
  - [ ] potential to build wheel on master?
- [X] indicator for not having an upstream branch set?
- [ ] keep additional segments for worktrees with feature/branch naming convention
- [ ] minify git branch group-name?
  - eg. feature/branch -> f/branch
  - [ ] may need to refactor out the minify to avoid a circular dependacy
  - applyVCS could strip len(branch) from the end of the common path and add minifyPath(branch) in it's place
- [ ] use the last fetch information to avoid getting out of date
  - we could fetch if the it is over some age but this could be dangerous, see `Git.last_fetch` for details
  - highlight the branch name in degrading colours as it ages?
  - use 'remote changes' arrow without number as pull reminder? highlight?
- [ ] consider calculating minimum unique name instead of using regex minify
  - this will mean walking the directory tree and, by extension, filesystem i/o which is likely to be _MUCH_ slower
  - if we do this it might be worth investigating persistant caching
