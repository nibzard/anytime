# Release Checklist

Use this checklist when preparing a new release of the anytime inference library.

## Pre-release

### Code Quality
- [ ] All tests pass: `python -m pytest tests/ -v`
- [ ] Test coverage is adequate (check with `python -m pytest --cov=anytime tests/`)
- [ ] No new warnings introduced
- [ ] Code passes type checking: `mypy anytime/`
- [ ] Linting passes: `ruff check anytime/`

### Documentation
- [ ] Version number updated in `anytime/__init__.py`
- [ ] CHANGELOG.md updated with version and changes
- [ ] README.md reflects current capabilities
- [ ] API documentation is up to date

### Testing
- [ ] Unit tests cover all major code paths
- [ ] Integration tests pass
- [ ] Performance benchmarks run and results are acceptable
- [ ] Optional stopping coverage tests pass

## Release

### Build
- [ ] Build package: `python -m build`
- [ ] Check build output in `dist/`

### Publishing
- [ ] Test on TestPyPI first
- [ ] Tag release in git: `git tag -a vX.Y.Z -m "Release X.Y.Z"`
- [ ] Push tag: `git push origin vX.Y.Z`
- [ ] Publish to PyPI: `twine upload dist/*`

## Post-release

### Verification
- [ ] Install from PyPI in clean environment: `pip install anytime-inference`
- [ ] Run basic sanity checks:
  ```python
  from anytime.cs.hoeffding import HoeffdingCS
  from anytime.spec import StreamSpec
  spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded")
  cs = HoeffdingCS(spec)
  for x in [0.3, 0.5, 0.7]:
      cs.update(x)
  iv = cs.interval()
  assert iv.t == 3
  ```

### Announcements
- [ ] GitHub release created with release notes
- [ ] Update documentation website if applicable

## Version History

### v0.1.0 - Initial Release
- Basic confidence sequences: Hoeffding, Empirical Bernstein, Bernoulli exact
- Two-sample A/B testing methods
- E-values for optional stopping
- CLI for batch analysis
- Demo application
- Comprehensive test suite (87+ tests)
- Scenario generators for benchmarking
