# Contributing to Anytime

Thank you for your interest in contributing to Anytime! This guide will help you get set up for local development and understand our contribution workflow.

## Quick Start

```bash
# Clone the repository
git clone <repo-url>
cd peek

# Install in development mode
pip install -e ".[dev,plot,demo]"

# Run tests
pytest -q

# Run the demo
python -m anytime.demo
```

## Development Setup

### Prerequisites

- Python 3.12+
- Git
- Virtual environment (recommended)

### Installation

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev,plot,demo]"
```

### Development Dependencies

The `[dev]` extra includes:
- **pytest**: Testing framework
- **hypothesis**: Property-based testing
- **mypy**: Type checking
- **ruff**: Fast linter

The `[plot]` extra includes:
- **matplotlib**: Plotting support

The `[demo]` extra includes:
- **streamlit**: Demo application

## Running Tests

### All Tests

```bash
pytest -q
```

### Specific Test File

```bash
pytest tests/test_cs.py -v
```

### Property-Based Tests

```bash
pytest tests/test_properties.py -v
```

### With Coverage

```bash
pytest --cov=anytime tests/
```

## Code Style

### Linting

We use `ruff` for fast linting:

```bash
ruff check anytime/
```

### Auto-fix Issues

```bash
ruff check --fix anytime/
```

### Type Checking

```bash
mypy anytime/
```

## Project Structure

```
peek/
├── anytime/
│   ├── __init__.py          # Public API exports
│   ├── spec.py              # StreamSpec, ABSpec
│   ├── types.py             # Interval, EValue, GuaranteeTier
│   ├── errors.py            # Exception classes
│   ├── recommend.py         # Method recommender
│   ├── config.py            # YAML config loading
│   ├── cli.py               # Command-line interface
│   ├── core/
│   │   └── estimators.py    # Online mean, variance
│   ├── cs/                  # One-sample confidence sequences
│   │   ├── hoeffding.py
│   │   ├── empirical_bernstein.py
│   │   └── bernoulli_exact.py
│   ├── twosample/           # Two-sample confidence sequences
│   │   ├── hoeffding.py
│   │   └── empirical_bernstein.py
│   ├── evalues/             # E-values
│   │   ├── bernoulli_mixture.py
│   │   └── twosample.py
│   ├── diagnostics/         # Diagnostics system
│   │   ├── checks.py        # Range, missingness, drift
│   │   └── tier.py          # GuaranteeTier
│   ├── io/                  # I/O utilities
│   │   └── csv_reader.py    # CSV reading with validation
│   ├── atlas/               # Benchmarking framework
│   │   ├── runner.py        # Monte Carlo simulator
│   │   ├── scenarios.py     # Scenario generators
│   │   └── report.py        # Report generation
│   ├── plotting/            # Plotting utilities
│   │   └── helpers.py
│   └── demo.py              # Demo launcher
├── tests/
│   ├── test_cs.py           # One-sample CS tests
│   ├── test_twosample.py    # Two-sample CS tests
│   ├── test_evalues.py      # E-value tests
│   ├── test_properties.py   # Hypothesis property tests
│   └── ...
├── examples/                # Runnable examples
├── docs/                    # Documentation
├── configs/                 # Atlas config files
└── demos/                   # Streamlit demo
```

## Adding a New Method

### 1. Create the Method Class

```python
# anytime/cs/my_method.py
from dataclasses import dataclass
from anytime.spec import StreamSpec
from anytime.types import Interval
from anytime.core.estimators import OnlineMean

@dataclass
class MyMethodCS:
    """My confidence sequence method."""

    spec: StreamSpec
    _estimator: OnlineMean = field(init=False, default_factory=OnlineMean)
    _t: int = field(init=False, default=0)

    def __post_init__(self):
        # Validate spec compatibility
        if self.spec.kind not in ("bounded", None):
            raise ValueError(f"MyMethodCS only supports bounded data, got {self.spec.kind}")

    def update(self, x: float) -> None:
        """Update with a new observation."""
        self._estimator.update(x)
        self._t += 1

    def interval(self) -> Interval:
        """Get current confidence interval."""
        # Your CS formula here
        lo = self._estimator.mean - width
        hi = self._estimator.mean + width
        return Interval(
            t=self._t,
            lo=lo,
            estimate=self._estimator.mean,
            hi=hi,
            alpha=self.spec.alpha,
        )

    def reset(self) -> None:
        """Reset to initial state."""
        self._estimator.reset()
        self._t = 0
```

### 2. Add Tests

```python
# tests/test_my_method.py
import pytest
from anytime.spec import StreamSpec
from anytime.cs.my_method import MyMethodCS

def test_my_method_basic():
    spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded")
    cs = MyMethodCS(spec)

    for x in [0.3, 0.5, 0.7]:
        cs.update(x)

    iv = cs.interval()
    assert iv.t == 3
    assert 0.0 <= iv.lo <= iv.estimate <= iv.hi <= 1.0
```

### 3. Update Exports

```python
# anytime/cs/__init__.py
from anytime.cs.my_method import MyMethodCS

__all__ = ["HoeffdingCS", "EmpiricalBernsteinCS", "BernoulliCS", "MyMethodCS"]
```

### 4. Update Recommender (Optional)

```python
# anytime/recommend.py
def recommend_cs(spec: StreamSpec) -> Recommendation:
    # Add logic for when to recommend MyMethodCS
    if spec.kind == "bounded" and some_condition:
        return Recommendation(method=MyMethodCS, reason="...")
    # ...
```

## Adding Tests

### Unit Tests

Test specific functionality:

```python
def test_feature_x():
    # Setup
    obj = MyClass()

    # Act
    result = obj.method()

    # Assert
    assert result == expected
```

### Property-Based Tests

Use Hypothesis for invariants:

```python
from hypothesis import given, strategies as st

@given(data=st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=1))
def test_interval_width_non_negative(data):
    """Interval width should always be non-negative."""
    cs = MyMethod(spec)
    for x in data:
        cs.update(x)
    iv = cs.interval()
    assert iv.width >= 0
```

## Documentation

### Docstrings

Use Google style docstrings:

```python
def update(self, x: float) -> None:
    """Update the confidence sequence with a new observation.

    Args:
        x: New observation in [support.lo, support.hi]

    Raises:
        AssumptionViolationError: If x is out of support bounds
    """
```

### Examples

Add runnable examples in the `examples/` directory:
- Make them self-contained
- Include clear comments
- Show expected output

## Pull Request Workflow

### 1. Fork and Branch

```bash
git checkout -b feature/my-feature
```

### 2. Make Changes

- Write clean, readable code
- Add tests for new functionality
- Update documentation
- Run tests locally

### 3. Commit

Use clear commit messages:

```bash
git commit -m "Add MyMethodCS for variance-adaptive inference"
```

### 4. Push and Create PR

```bash
git push origin feature/my-feature
# Create PR on GitHub
```

### PR Checklist

- [ ] Tests pass (`pytest -q`)
- [ ] Code formatted (`ruff check --fix`)
- [ ] Types check (`mypy anytime/`)
- [ ] Documentation updated
- [ ] Examples added (if applicable)
- [ ] CHANGELOG.md updated

## Release Process

See `docs/RELEASE_CHECKLIST.md` for the full release checklist.

### Version Bump

```python
# anytime/__init__.py
__version__ = "0.2.0"
```

### Changelog

```markdown
## [0.2.0] - 2024-XX-XX

### Added
- New MyMethodCS for variance-adaptive inference

### Fixed
- Edge case in EmpiricalBernsteinCS

### Changed
- Improved diagnostics performance
```

## Getting Help

### Questions?

- Check existing issues
- Read the docs in `docs/`
- Ask in a discussion thread

### Bugs?

- Open an issue with:
  - Minimal reproducible example
  - Expected vs actual behavior
  - Python version and OS
  - Full error traceback

### Feature Requests?

- Open an issue describing:
  - The problem you're solving
  - Proposed solution
  - Alternative approaches considered

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to build better tools for anytime-valid inference.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Happy hacking!** 🚀
