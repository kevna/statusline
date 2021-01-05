# TODO
Features for the future

- [ ] require a github pipeline before reintegration
  - this will require setting up a CI tool to run the tests
  - [ ] we should also check coverage
  - [ ] ideally a linting tool
  - [ ] turn off requiring code reviews? (currently used to block trunk commits)
- [ ] indicator for not having an upstream branch set?
- [ ] minify git branch group-name?
  - eg. feature/branch -> f/branch
  - [ ] would need to refactor out the minify to avoid a circular dependacy
- [ ] use the last fetch information to avoid getting out of date
  - we could fetch if the it is over some age but this could be dangerous, see `Git.last_fetch` for details

