PHASE 1 — Candidate Generation (5 concepts)

Candidate 1 — Anytime-Valid Inference Atlas (Confidence Sequences + E-values)

A) Pitch (1 sentence)
A drop-in library + CLI that makes “peeking-safe” online inference (confidence intervals + hypothesis tests) the default for streaming metrics and A/B tests.

B) Mathematical contract (plain + formal-ish)
	•	Plain English: Your intervals and decisions remain valid even if you continuously monitor results and stop at an arbitrary (data-dependent) time.
	•	Formal-ish: For a parameter \theta (mean or mean-difference) and confidence sequence (C_t)_{t\ge1}:
\Pr\left(\forall t\ge1:\ \theta \in C_t\right) \ge 1-\alpha
And for an e-process (E_t)_{t\ge1} under H_0:
\Pr_{H_0}\left(\exists t:\ E_t \ge \tfrac{1}{\alpha}\right) \le \alpha
(Optional stopping safe.)

C) Why it historically “didn’t get built right”
	•	Huge taxonomy (Hoeffding-style, empirical-Bernstein, stitching, mixture bounds, Bernoulli-exact, two-arm variants, etc.).
	•	Hard UX: users want “one function that works” but the method depends on assumptions (boundedness, variance knowledge, tails).
	•	Evaluation burden: validity must be tested across stopping rules + regimes; most repos ship one method with minimal experiments.
	•	Integration pain: streaming ingestion, dashboards, deterministic experiments, and reporting are usually out-of-scope.

D) What becomes possible with zero-cost iteration (agent unlock)
	•	Implement 10+ theoretically sound variants with a single stable API.
	•	Systematically sweep: distributions × stopping rules × effect sizes × horizons → generate a searchable “atlas” of behavior.
	•	Auto-recommender that picks a method based on declared assumptions + measured diagnostics (range violations, drift signals, variance regime).
	•	“Trust but verify” harness that repeatedly checks the anytime guarantee empirically.

E) Practical value today (who uses it, where it fits)
	•	Growth/product engineers running A/B tests who currently “promise not to peek.”
	•	ML/infra teams monitoring online metrics with alert thresholds.
	•	Data scientists who need sequential decision-making without statistical footguns.
Fits as a small library, a CLI in CI, and a demo app for education.

F) Demo hook (visually/interactive compelling)
A live plot where you stream observations and watch:
	•	confidence sequence band shrink over time,
	•	optional-stopping decisions remain valid,
	•	e-values spike when the effect is real,
	•	and “naive p-values” fail under peeking (side-by-side).

G) Differentiator vs typical research repos
	•	One API for mean and mean-difference, one-sided/two-sided, bounded/Bernoulli/sub-Gaussian.
	•	Built-in stopping rule suite (fixed horizon, threshold stop, “stop when CI excludes 0”, etc.).
	•	Atlas generator (HTML/Markdown report + plots) producing regimes + failure modes.
	•	Default recommender with explicit assumption declarations and diagnostics.
	•	“Contract-first” docs: every method states assumptions + what is guaranteed.

H) v1 feasibility rating + biggest risks
	•	Risk: Low–Medium.
	•	Biggest risks: (1) picking a tight but correct set of methods (avoid subtle math bugs), (2) balancing simplicity vs coverage of many regimes, (3) keeping the UI/CLI polished.

⸻

Candidate 2 — Conformal Uncertainty Studio (Unified Conformal Prediction + Atlas + Defaults)

A) Pitch
A unified conformal prediction wrapper that turns any model into calibrated prediction sets/intervals with distribution-free coverage—plus an atlas that shows when each conformal variant wins.

B) Mathematical contract
	•	Plain: Under exchangeability, coverage holds without modeling assumptions.
	•	Formal-ish (marginal coverage):
\Pr\left(Y_{n+1}\in \Gamma_\alpha(X_{n+1})\right) \ge 1-\alpha
(for split conformal / variants under standard conditions).

C) Why not built right
	•	Many variants (split, CV+, jackknife+, Mondrian, adaptive, CQR); repos are fragmented.
	•	Evaluation is a combinatorial mess: models × data shifts × group-wise behavior × calibration sizes.
	•	UX gap: users need “do the right thing automatically,” including sharp warnings about violated assumptions (non-exchangeability).

D) Agent unlock
	•	Implement canonical taxonomy + run massive regime sweeps: covariate shift, label noise, heteroscedasticity, group imbalance.
	•	Auto-configuration that chooses between split/CV+/Mondrian based on measured regime signals.
	•	Built-in “coverage audit” and debugging utilities.

E) Practical value
ML practitioners deploying models who need reliable uncertainty without Bayesian overhead.

F) Demo hook
Upload data → train model → see prediction intervals; toggle variants and watch coverage/size tradeoffs.

G) Differentiator
	•	One stable wrapper API across tasks (regression/classification).
	•	“Atlas-first” reports showing size vs coverage vs drift.
	•	Group coverage dashboards (clearly labeled as not guaranteed unless conditions hold).
	•	Auto-choice of nonconformity scores and calibration splits.
	•	Reproducible configs and cached artifacts.

H) Feasibility
	•	Risk: Medium.
Main risk: scope creep (too many tasks/models), plus careful messaging around conditional coverage limitations.

⸻

Candidate 3 — Streaming Matrix Sketching Workbench (Frequent Directions / CountSketch / SRHT + Certificates)

A) Pitch
A practical streaming linear algebra toolkit that maintains approximate covariance/PCA with provable error bounds and a benchmark harness that maps accuracy–throughput tradeoffs.

B) Mathematical contract
	•	Plain: The sketch preserves quadratic forms / covariance up to a controlled error.
	•	Formal-ish (typical form): with sketch B sized by \varepsilon, for all unit vectors x:
0 \le \|Ax\|_2^2 - \|Bx\|_2^2 \le \varepsilon \|A\|_F^2
(algorithm-dependent constants; v1 would pick one primary algorithm with a crisp guarantee).

C) Why not built right
	•	Engineering is brutal: streaming IO, numerical stability, benchmarking across matrices (sparse/dense, tall/skinny), and verifying bounds.
	•	Research repos often omit robust APIs, tests, and end-to-end reproducibility.

D) Agent unlock
	•	Implement multiple sketches + run systematic sweeps across matrix regimes.
	•	Automated bound-checking + “certificate” reports that tell you when the sketch is trustworthy.

E) Practical value
Infra/ML systems teams needing approximate PCA/covariance for monitoring, embeddings, or dimensionality reduction at scale.

F) Demo hook
Stream rows of a matrix; watch approximate singular values converge; compare throughput vs error live.

G) Differentiator
	•	Unified API across sketches; consistent output types.
	•	Deterministic benchmarking and profiling.
	•	Synthetic + real matrix generators with regime knobs.
	•	Numerical robustness checks.
	•	“Atlas” plots: error vs memory vs time.

H) Feasibility
	•	Risk: Medium.
Risk: choosing tight guarantees + numerical stability + performance in pure Python (may need numba).

⸻

Candidate 4 — Kernel Hypothesis Testing Studio (MMD/HSIC/KSD + Exact Type-I via Permutation + Power Atlas)

A) Pitch
A “testing studio” that lets you run kernel two-sample and independence tests with exact Type I control (via permutation) and a power atlas across regimes.

B) Mathematical contract
	•	Plain: Under the null and exchangeability, permutation p-values control false positives exactly.
	•	Formal-ish:
\Pr_{H_0}(p \le \alpha) \le \alpha
with permutation-based calibration.

C) Why not built right
	•	Many kernels, bandwidth heuristics, and test statistics → huge taxonomy.
	•	Power is extremely regime-dependent; proper sweeping is expensive.
	•	Integration pain: fast permutation, batching, GPU optionality, reproducibility.

D) Agent unlock
	•	Full factorial sweeps over kernels/bandwidths/sample sizes/shift types.
	•	Auto-selector for kernel/bandwidth based on diagnostic metrics.

E) Practical value
Dataset shift detection, independence checks, feature selection diagnostics.

F) Demo hook
Interactive “shift simulator”: toggle shift type and see test power and false positive control.

G) Differentiator
	•	Canonical kernel + bandwidth API.
	•	Exact p-value calibration defaults.
	•	Power atlas + failure mode documentation.
	•	Caching + deterministic reports.
	•	“What kernel should I use?” recommender grounded in sweeps.

H) Feasibility
	•	Risk: Medium.
Risk: performance for large n (kernel matrices), and careful messaging about computational cost.

⸻

Candidate 5 — Diverse Subset Optimizer (Submodular + DPP + Constraints + Approximation Certificates)

A) Pitch
A library that selects diverse subsets (data summarization, batch active learning, prompt-set selection) using submodular optimization and DPPs, with approximation guarantees and an atlas of constraint regimes.

B) Mathematical contract
	•	Plain: Greedy gives a provable near-optimal solution for monotone submodular objectives.
	•	Formal-ish (cardinality constraint): for greedy set S_g and optimum S^*,
f(S_g) \ge (1-\tfrac{1}{e}) f(S^*)
(when f is monotone submodular and |S|\le k).

C) Why not built right
	•	Dozens of objectives/constraints (knapsack, matroid, streaming).
	•	Hard to compare across datasets and similarity metrics.
	•	Getting robust, well-tested implementations is rare; most code is “paper demo.”

D) Agent unlock
	•	Implement variants + constraints with unified API.
	•	Massive benchmark atlas across similarity definitions and budgets.
	•	Auto-choice of objective + constraints and sanity-check certificates.

E) Practical value
Curating training sets, summarizing logs, selecting evaluation/prompt sets, dataset dedup + diversity.

F) Demo hook
Drag a budget slider; watch chosen points diversify while coverage/utility metrics update.

G) Differentiator
	•	Stable constraint abstraction.
	•	Approximation ratio notes + certificates where possible.
	•	Benchmark atlas across similarity regimes.
	•	Defaults that “just work” for embeddings and tabular.
	•	Failure mode docs (e.g., non-metric similarities).

H) Feasibility
	•	Risk: Medium.
Risk: defining universally satisfying defaults and similarity metrics.

⸻

Ranking

“Show HN success probability” (most → least)
	1.	Candidate 1 (Anytime-valid inference) — immediate pain (“peeking invalidates p-values”), clear demo, strong engineering + math story.
	2.	Candidate 2 (Conformal studio) — strong demand for uncertainty, but messaging is harder (conditional vs marginal coverage nuance).
	3.	Candidate 5 (Diverse subset optimizer) — broadly useful, but many will ask “why not just k-means?”; needs sharp positioning.
	4.	Candidate 3 (Streaming sketching) — very cool for systems folks, but narrower audience; performance expectations are high.
	5.	Candidate 4 (Kernel testing studio) — valuable but many dismiss kernels as slow or finicky; needs a strong power atlas to win skeptics.

“Mathematical elegance” (most → least)
	1.	Candidate 1 — optional stopping safety is a clean, profound contract; guarantees are crisp and testable.
	2.	Candidate 5 — approximation guarantees are canonical and easy to state.
	3.	Candidate 3 — linear algebra sketch guarantees are beautiful (though constants/assumptions can be tricky).
	4.	Candidate 2 — distribution-free coverage is elegant, but “what it does not guarantee” complicates the story.
	5.	Candidate 4 — exactness via permutation is clean, but power depends heavily on choices (less “one theorem explains it all”).

Selected concept to fully scope

Candidate 1 — Anytime-Valid Inference Atlas (Confidence Sequences + E-values).
Best balance of practical value + crisp contract + strongest “agent unlock” via systematic regime exploration + defaults.

⸻

PHASE 2 — Ultimate Build Plan (Selected Project)

SECTION 1 — Title + pitch + elevator problem statement

Hacker News style title

Show HN: Anytime — peeking-safe A/B tests with confidence sequences + e-values (plus a benchmark atlas)

1-sentence pitch

A small Python tool that provides always-valid confidence intervals and hypothesis tests for streaming metrics, so you can monitor and stop whenever you want—without breaking your error guarantees.

Elevator problem statement (6–10 lines)
	•	Teams run experiments and dashboards that update every minute, but classical p-values assume you only look once at a fixed sample size.
	•	In practice, people peek, stop early when it “looks good,” and ship changes—silently inflating false positives.
	•	Even careful teams struggle: you need sequential methods, but the ecosystem is fragmented and hard to trust.
	•	Most implementations are “paper demos” without robust APIs, reproducible configs, or comprehensive validation.
	•	Engineers want a simple interface: stream data in, get a valid interval and a valid stopping rule out.
	•	Managers want an audit trail: what assumptions were used, what method was chosen, and what the validity contract is.
	•	This project makes anytime-valid inference a product: unified methods, a recommender, and an atlas that shows when each method works best (or fails).

⸻

SECTION 2 — Mathematical Contract (the “rules of the world”)

Key objects and setup

We focus v1 on means and mean differences, because they cover most online metrics and are the cleanest setting for rigorous anytime guarantees.

Data (one-sample):
	•	Observations X_1, X_2, \dots revealed sequentially.
	•	Target parameter: \mu = \mathbb{E}[X_t] (assumed time-homogeneous).

Data (two-sample / A/B):
	•	Two streams X^{(A)}_1, X^{(A)}_2, \dots and X^{(B)}_1, X^{(B)}_2, \dots.
	•	Target: \Delta = \mu_B - \mu_A.

Assumptions (v1 “guarantee tier”):
	1.	Conditional independence / martingale difference for each stream:
X_t is adapted to filtration \mathcal{F}_t, and satisfies a boundedness/sub-Gaussian condition conditional on \mathcal{F}_{t-1}.
	2.	Bounded outcomes (primary): user declares X_t \in [a,b] (common for conversion rates, bounded KPIs, normalized scores).
	3.	For two-sample, either independent streams or randomized assignment so that each arm is conditionally i.i.d./martingale-like.

(We explicitly do not promise correctness for arbitrary nonstationary drift unless stated.)

Guarantees the tool provides

Guarantee 1: Anytime-valid confidence sequences for the mean
	•	Plain English: At any time you choose to stop, the reported interval contains the true mean with probability at least 1-\alpha, and it’s valid even if you stop based on what you see.
	•	Formal-ish: The tool outputs intervals C_t such that:
\Pr\left(\forall t\ge1:\ \mu \in C_t\right) \ge 1-\alpha
under the stated assumptions.

Guarantee 2: Anytime-valid tests via e-values / stopping thresholds
	•	Plain English: Under the null, the chance you ever (at any time) cross the decision threshold is at most \alpha.
	•	Formal-ish: The tool constructs E_t with \mathbb{E}_{H_0}[E_t]\le 1 and reports rejection when E_t \ge 1/\alpha. Then:
\Pr_{H_0}\left(\exists t:\ E_t \ge \tfrac{1}{\alpha}\right) \le \alpha

Guarantee 3: Two-sample mean-difference sequences
	•	Plain English: The reported interval for \Delta is valid under continuous monitoring.
	•	Formal-ish: For intervals C^{\Delta}_t:
\Pr\left(\forall t\ge1:\ \Delta \in C^{\Delta}_t\right) \ge 1-\alpha
(constructed via valid one-sample sequences + unioning or a direct two-sample e-process, depending on method).

What breaks assumptions (and what the tool should do)

Assumption violations and tool behavior
	1.	Out-of-range values when the user declared bounded support [a,b].
	•	Break: The boundedness-based guarantee no longer applies.
	•	Tool behavior:
	•	Default: hard error with a clear message and sample offending values.
	•	Optional mode: clip with disclosure (“Guarantee applies to clipped stream X'_t=\min(\max(X_t,a),b)”), and mark outputs as “clipped-tier guarantee.”
	2.	Strong nonstationarity / drift (mean changes over time).
	•	Break: The target \mu is ill-defined; even martingale-style assumptions may fail.
	•	Tool behavior: Run drift diagnostics; if triggered, warn and switch UI to “monitoring mode” (report rolling estimates + no validity claim), unless the user explicitly chooses a change-point method (out of v1 scope).
	3.	Dependence from adaptive sampling (e.g., selecting which data to include based on outcomes).
	•	Break: conditional mgf bounds may not hold.
	•	Tool behavior: Require explicit “sampling policy declared” flag; otherwise warn that guarantee may not hold.
	4.	Missingness correlated with outcomes (NaNs dropped non-randomly).
	•	Break: bias.
	•	Tool behavior: warn + report missingness rate; optionally refuse to compute “guarantee-tier” outputs unless a missingness policy is specified.
	5.	Heavy tails when using sub-Gaussian methods (rare extreme values).
	•	Break: bounds become too optimistic.
	•	Tool behavior: detect via tail diagnostics (extreme z-scores vs declared bounds); recommend bounded/clipped method or refuse guarantee-tier.

Failure modes (3–5) and expected tool responses
	1.	User sets impossible bounds (e.g., [0,1] but sees 1.2). → error; suggest correct bounds or clip-with-disclosure.
	2.	Alpha too small + early time → intervals may be vacuously wide; tool should explain and optionally delay displaying decisions until minimum n.
	3.	Tiny sample sizes with two-sample → unstable variance estimates; tool switches to conservative method (Hoeffding) automatically.
	4.	Drift flagged → tool marks “guarantee invalid under drift,” recommends restarting experiment window or using fixed-time analysis.
	5.	Ingested CSV has mixed groups / label errors → tool validates schema and group labels; refuses if inconsistent.

⸻

SECTION 3 — The Original Take (what’s new here)

“Implementations exist somewhere” isn’t enough because the hard part is not writing one bound—it’s:
	•	choosing the right one for a given regime,
	•	validating it under stopping rules,
	•	comparing variants fairly,
	•	and packaging it so engineers actually use it.

Agent-unlocked novelty: unified taxonomy + atlas + defaults + reproducibility

Concrete novel features (v1)
	1.	One stable API for sequential mean inference and A/B mean-difference inference.
	2.	Method zoo with consistent semantics: every method returns the same interface, with explicit assumption tags.
	3.	Stopping-rule suite: fixed horizon, “stop when CI excludes threshold,” “stop when e-value crosses,” periodic looks, etc.
	4.	Atlas generator that sweeps regimes automatically and emits a report answering:
	•	Does it maintain anytime coverage / Type I error?
	•	How tight is it vs alternatives?
	•	When does it break (drift, mis-specified bounds)?
	5.	Default recommender: given a StreamSpec + observed diagnostics, it picks a conservative but competitive default (and explains why).
	6.	Assumption audit: boundedness checks, missingness summaries, drift tests; outputs carry a “guarantee tier” badge (Guaranteed / Clipped / Diagnostic).
	7.	Deterministic experiments: seeds, configs, code version hash, and environment snapshot are logged for every run.
	8.	Golden benchmark snapshots: small, deterministic “smoke atlas” that must match before release.
	9.	Side-by-side invalid baseline: naive fixed-horizon p-values shown to fail under peeking (educational + persuasive).
	10.	Polished UX: CLI for real data streams + a minimal interactive demo app for intuition.

⸻

SECTION 4 — Scope & Deliverables (v1 must be shippable)

You will ship exactly these five deliverables.

1) Core library/package

Name: anytime (package), repo name e.g. anytime-inference

Modules/components
	•	anytime/spec.py — StreamSpec, ABSpec, enums for assumptions/tier
	•	anytime/core/estimators.py — online mean/var, arm trackers
	•	anytime/cs/ — confidence sequence implementations
	•	hoeffding.py, empirical_bernstein.py, mixture.py, bernoulli_exact.py
	•	anytime/evalues/ — e-process / e-value constructions
	•	anytime/twosample/ — AB mean-difference wrappers
	•	anytime/diagnostics/ — range checks, drift checks, missingness report
	•	anytime/recommend.py — default recommender + explanation strings
	•	anytime/logging.py — artifact logger (jsonl) + env capture
	•	anytime/plotting.py — plot helpers (CS bands, e-values, decision time hist)

Definition of done (acceptance criteria)
	•	Importable package; pip install -e . works.
	•	At least 4 confidence sequence methods for one-sample mean.
	•	At least 2 two-sample methods for mean-difference.
	•	At least 2 e-value methods (one-sample and two-sample).
	•	Each method has:
	•	declared assumptions,
	•	parameter validation,
	•	deterministic behavior given seed/config.

Must-have
	•	Bounded-mean CS (Hoeffding + empirical Bernstein).
	•	Bernoulli-specialized method (exact or tight).
	•	Two-sample wrapper and e-value thresholding.

Nice-to-have
	•	Sub-Gaussian mixture CS (still valid under boundedness).
	•	Optional clipping tier.

Out-of-scope (hard exclusions)
	•	Generalized linear models, regression conformal, multiple metrics correction beyond simple union bounds.
	•	Change-point detection methods with guarantees.
	•	Bayesian sequential methods (no priors tuning in v1).

⸻

2) CLI tool

Command: anytime

Commands (v1)
	•	anytime abtest run --config configs/ab.yaml --csv data.csv
	•	anytime mean run --config configs/mean.yaml --csv data.csv
	•	anytime simulate --config configs/sim.yaml
	•	anytime atlas run --config configs/atlas.yaml
	•	anytime report open path/to/report.html (optional convenience)

Definition of done
	•	anytime --help lists commands with examples.
	•	CLI validates configs and fails fast with actionable errors.
	•	CLI can stream from:
	•	CSV file (batch read but processed sequentially),
	•	stdin (line-delimited JSON) for “tail -f” style pipelines.

Must-have
	•	simulate and atlas run.
	•	abtest run from CSV with schema validation.

Nice-to-have
	•	Live terminal UI (rich) showing current interval/e-value.

Out-of-scope
	•	Connecting directly to databases or warehouses.
	•	Distributed execution.

⸻

3) Interactive demo (choose ONE) — Minimal local web app

Tech: Streamlit (simple, local-first)

What it does
	•	User chooses scenario (Bernoulli, bounded continuous), effect size, alpha, method.
	•	Streams synthetic data and displays:
	•	confidence sequence band,
	•	e-value trajectory,
	•	“stop now” validity explanation,
	•	naive p-value baseline comparison.

Definition of done
	•	One command runs it:
	•	python -m anytime.demo (which launches streamlit internally)
	•	Demo runs offline with only synthetic data.
	•	Demo includes “assumption violation” toggle (inject out-of-range) and shows tool response.

Must-have
	•	Visual CS + decisions; baseline invalid method.

Nice-to-have
	•	Download a JSON artifact log.

Out-of-scope
	•	Hosted demo, user accounts, remote compute.

⸻

4) Benchmark suite + report generator

Components
	•	anytime/atlas/scenarios.py — scenario definitions
	•	anytime/atlas/runner.py — run sweeps, cache results
	•	anytime/atlas/metrics.py — coverage, width, Type I, power, runtime
	•	anytime/atlas/report.py — generate HTML/Markdown report + plots
	•	configs/atlas.yaml — sweep definitions

Definition of done
	•	One command:
	•	python -m anytime.atlas --config configs/atlas.yaml --out runs/atlas_001
	•	Produces:
	•	report.html (or report.md + images),
	•	results.parquet (or CSV),
	•	manifest.json capturing config + git hash + env.

Must-have
	•	Coverage and Type I error checks under optional stopping.
	•	Power/width tradeoffs.
	•	Runtime micro-bench.

Nice-to-have
	•	Heatmaps across regimes and automatic “best default” summary.

Out-of-scope
	•	GPU acceleration; huge-scale distributed sweeps.

⸻

5) Docs skeleton (README + 3 guides + 5 cookbook recipes)

Docs tree
	•	README.md — quickstart + contract + one-line install/run
	•	docs/guides/01_anytime_validity.md
	•	docs/guides/02_ab_testing.md
	•	docs/guides/03_atlas_and_defaults.md
	•	docs/cookbook/01_conversion_rate.md
	•	docs/cookbook/02_bounded_kpi.md
	•	docs/cookbook/03_threshold_alerting.md
	•	docs/cookbook/04_sequential_ci_stop_rule.md
	•	docs/cookbook/05_streaming_from_stdin.md

Definition of done
	•	Each guide includes:
	•	a “contract” box (assumptions + guarantee),
	•	a runnable snippet,
	•	failure modes and responses.

Out-of-scope
	•	Full website; extensive theory textbook.

⸻

SECTION 5 — API Specification (concrete)

Core data specs and results

from dataclasses import dataclass
from typing import Optional, Tuple, Literal, Dict, Any, Protocol

GuaranteeTier = Literal["guaranteed", "clipped", "diagnostic"]

@dataclass(frozen=True)
class StreamSpec:
    alpha: float                      # e.g., 0.05
    support: Optional[Tuple[float, float]] = None  # (a,b) if bounded
    kind: Literal["bounded", "bernoulli", "subgaussian"] = "bounded"
    two_sided: bool = True
    name: str = "metric"

@dataclass(frozen=True)
class ABSpec:
    alpha: float
    support: Optional[Tuple[float, float]] = None
    kind: Literal["bounded", "bernoulli"] = "bounded"
    two_sided: bool = True
    name: str = "delta"

@dataclass(frozen=True)
class Interval:
    t: int
    lo: float
    hi: float
    estimate: float
    tier: GuaranteeTier
    meta: Dict[str, Any]  # method name, assumptions, diagnostics summary

Confidence sequences

class ConfidenceSequence(Protocol):
    spec: StreamSpec
    def update(self, x: float) -> None: ...
    def interval(self) -> Interval: ...
    def reset(self, seed: Optional[int] = None) -> None: ...

Concrete implementations (v1 public)

class HoeffdingCS:
    def __init__(self, spec: StreamSpec): ...
    def update(self, x: float) -> None: ...
    def interval(self) -> Interval: ...

class EmpiricalBernsteinCS:
    def __init__(self, spec: StreamSpec, v_min: float = 1e-12): ...
    def update(self, x: float) -> None: ...
    def interval(self) -> Interval: ...

class BernoulliExactCS:
    """Tight CS specialized for Bernoulli outcomes (0/1)."""
    def __init__(self, spec: StreamSpec): ...
    def update(self, x: float) -> None: ...
    def interval(self) -> Interval: ...

Two-sample A/B confidence sequences

class TwoSampleCS:
    spec: ABSpec
    def update(self, x: float, arm: Literal["A", "B"]) -> None: ...
    def interval(self) -> Interval: ...

Concrete v1:

class TwoSampleHoeffdingCS:
    def __init__(self, spec: ABSpec): ...

class TwoSampleEmpiricalBernsteinCS:
    def __init__(self, spec: ABSpec): ...

E-values / e-processes

@dataclass(frozen=True)
class EValue:
    t: int
    e: float
    decision: bool          # True if e >= 1/alpha
    tier: GuaranteeTier
    meta: Dict[str, Any]

class EProcess(Protocol):
    def update(self, x: float) -> None: ...
    def evalue(self) -> EValue: ...

Concrete v1:

class BernoulliMixtureE:
    """E-process for testing H0: p <= p0 (or p = p0) with optional stopping validity."""
    def __init__(self, alpha: float, p0: float, side: Literal["le", "ge", "two"]): ...

class TwoSampleMeanMixtureE:
    """E-process for testing H0: Δ <= 0 (or Δ = 0) for bounded outcomes."""
    def __init__(self, spec: ABSpec, delta0: float = 0.0, side: Literal["le","ge","two"]="two"): ...

Default recommender

@dataclass(frozen=True)
class Recommendation:
    method: str
    reason: str
    assumptions: Dict[str, Any]
    tier: GuaranteeTier

def recommend_cs(spec: StreamSpec, diagnostics: Optional[Dict[str, Any]] = None) -> Recommendation: ...
def recommend_ab(spec: ABSpec, diagnostics: Optional[Dict[str, Any]] = None) -> Recommendation: ...

Error handling and validation
	•	All constructors validate:
	•	0 < alpha < 1
	•	if kind="bounded" then support=(a,b) with a < b
	•	if kind="bernoulli" then support must be (0,1) or omitted but values must be {0,1}
	•	update(x):
	•	rejects NaN/inf by default (raises ValueError)
	•	checks range; behavior depends on mode:
	•	strict: raise AssumptionViolationError
	•	clip: clip + set tier to "clipped" + log event

Config system + reproducibility
	•	YAML config defines:
	•	method name + parameters
	•	alpha, support, side
	•	scenario + seed
	•	Every run writes a manifest.json containing:
	•	config (exact)
	•	package version
	•	git commit hash (if available)
	•	python + numpy version
	•	seed(s)

End-to-end usage examples

Example 1 — Sequential CI for a bounded KPI

from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS

spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True, name="kpi")
cs = EmpiricalBernsteinCS(spec)

for x in stream_values():     # yields floats in [0,1]
    cs.update(x)
    iv = cs.interval()
    if iv.t % 100 == 0:
        print(iv.t, iv.estimate, (iv.lo, iv.hi), iv.tier)

    # Valid stopping rule:
    if iv.lo > 0.55:          # “metric is above threshold”
        print("Stop & ship: anytime-valid.")
        break

Example 2 — A/B test with e-values (optional stopping safe)

from anytime.evalues import TwoSampleMeanMixtureE
from anytime import ABSpec

spec = ABSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=False, name="lift")
etest = TwoSampleMeanMixtureE(spec, delta0=0.0, side="ge")  # test Δ >= 0

for arm, x in ab_stream():     # arm in {"A","B"}, x in [0,1]
    etest.update((arm, x))     # (implementation may accept tuple or two args)
    ev = etest.evalue()
    if ev.decision:
        print(f"Reject H0 at t={ev.t} with e={ev.e:.2f} (optional stopping safe).")
        break


⸻

SECTION 6 — Benchmark/Atlas Plan (the credibility engine)

Benchmark scenarios (16 total; synthetic-first, offline)

Each scenario is parameterized by horizon T, effect size, and stopping rule.

One-sample (mean) scenarios
	1.	Bernoulli(p=0.1), bounded [0,1], fixed horizon
	2.	Bernoulli(p=0.1), stop when CI excludes 0.1
	3.	Bernoulli(p=0.1), periodic looks every 50 samples
	4.	Bounded Beta(2,8) scaled to [0,1], low variance
	5.	Bounded uniform [0,1], high variance
	6.	Bounded mixture (90% near 0.2, 10% near 0.8), bimodal
	7.	Drift: p(t) ramps from 0.1→0.2 halfway (should trigger drift warning)
	8.	Out-of-range injection: 1% values at 1.2 (should error or clip)

Two-sample (A/B) scenarios
9) Bernoulli A:0.10 vs B:0.11, stop when CI excludes 0
10) Bernoulli A:0.10 vs B:0.10 (null), stop when e-value crosses (Type I check)
11) Bounded continuous A: Beta(2,8) vs B: Beta(2.2,7.8)
12) Heteroscedastic: A low variance, B high variance but same mean (variance adaptivity test)
13) Small effect regime: Δ=0.002 with large T
14) Strong effect regime: Δ=0.05 with early stopping
15) Randomized assignment with imbalance (70/30)
16) Dependence stress test: AR(1)-like noise within each arm (diagnostic-only; expect warnings)

Metrics (correctness + utility + performance)

Correctness
	•	Anytime coverage rate: fraction of runs where \theta stayed inside C_t for all t\le T.
	•	Anytime Type I error under optional stopping: fraction of null runs where decision triggered.
	•	Calibration check: empirical crossing probability vs \alpha (should be ≤ α within Monte Carlo error).

Utility
	•	Average interval width at selected times (t=100, 500, 1000, …).
	•	Median stopping time under alternatives (speed).
	•	Power at horizon and under stopping rules.

Performance
	•	Updates/sec for each method (micro-benchmark).
	•	Peak memory per run.

Method variants / ablations to compare (≥ 8)
	1.	HoeffdingCS (bounded, conservative baseline)
	2.	EmpiricalBernsteinCS (variance-adaptive)
	3.	BernoulliExactCS (Bernoulli-specialized)
	4.	TwoSampleHoeffdingCS
	5.	TwoSampleEmpiricalBernsteinCS
	6.	BernoulliMixtureE (one-sample e-values)
	7.	TwoSampleMeanMixtureE (two-sample e-values)
	8.	Naive fixed-horizon p-value with repeated peeking (intentionally invalid baseline)
	9.	(Optional nice-to-have) “Stitching” vs “mixture” tuning ablation

Expected trends (sanity expectations)
	•	EB should dominate Hoeffding (narrower intervals) when variance is low/moderate.
	•	BernoulliExact should be tightest for Bernoulli regimes.
	•	Under null with optional stopping, e-value decision should trigger at rate ≤ α; naive peeking baseline should exceed α.
	•	Drift scenario should show elevated violations or unstable behavior; tool should flag drift and downgrade tier.

Scalability targets (v1)
	•	O(1) per-update memory and time per method (no storing full history).
	•	Benchmark target: process 1e6 updates in < ~3 seconds total for the simplest methods on a typical laptop-class CPU (record actual results; do not promise if not met).

Auto-generated plots/tables
	•	Coverage vs time curves (and a single “anytime coverage” summary number).
	•	Type I error bar chart per method under peeking stopping rules.
	•	Power vs effect size curves (two-sample).
	•	Median stopping time vs effect size.
	•	Interval width vs time for selected regimes.
	•	Runtime throughput table (updates/sec).
	•	“Default recommender choices” table: which method it picks per scenario + outcomes.

⸻

SECTION 7 — Testing Strategy (prove you didn’t fool yourself)

Unit tests (core math)
	•	Verify online estimators: mean/variance updates match batch computations.
	•	Verify that interval endpoints are within declared support for bounded methods.
	•	Verify alpha monotonicity: smaller alpha ⇒ wider or equal intervals at same t.

Property-based tests (invariants)

Use hypothesis to generate bounded streams and check:
	•	No NaNs/infs produced in intervals for valid inputs.
	•	Interval width is nonnegative and typically shrinks with t (allow rare non-monotonicity depending on method, but enforce “eventual shrinkage” trend).
	•	Two-sample symmetry: swapping A and B flips sign of estimate and interval appropriately.

Simulation checks (empirical guarantee verification)

For each guarantee-tier method:
	•	Run Monte Carlo under null with multiple stopping rules.
	•	Assert empirical anytime Type I error ≤ α + tolerance (tolerance computed from binomial CI, e.g. Wilson upper bound).
	•	Assert empirical anytime coverage ≥ 1-α - tolerance.

(These become “slow tests” in CI; smoke subset runs by default, full suite on demand.)

Regression tests
	•	Golden snapshot: deterministic seed + small atlas config must reproduce identical summary metrics (within tiny tolerance).
	•	If numbers drift, CI fails until explicitly updated.

Performance tests (runtime budgets)
	•	Micro-benchmark update() for 1e5 iterations; fail if regression > X% from baseline.
	•	Record throughput in artifacts; gate only on regressions, not absolute speed.

“Stop the line” checklist before release
	•	pytest passes (unit + property tests).
	•	“Smoke atlas” runs and report is generated.
	•	Demo app launches and basic interactions work.
	•	README quickstart commands execute end-to-end.
	•	Version bumped; manifest includes environment and git hash.

⸻

SECTION 8 — Skeptical Reviewer / HN Comment Defense

Below are 10 likely technical comments, with evidence-based responses and which artifacts address them.
	1.	“Sequential methods are too conservative; you lose all power.”
	•	Response: Atlas shows EB and Bernoulli-specialized sequences are substantially tighter than Hoeffding while maintaining anytime validity; median stopping times improve under alternatives.
	•	Artifact: Power curves + stopping time histograms.
	2.	“I don’t trust your math. How do I know it’s actually anytime-valid?”
	•	Response: We run Monte Carlo Type I/coverage checks under multiple stopping rules; results are in the report with confidence intervals.
	•	Artifact: Type I error table + anytime coverage rates.
	3.	“Why not just use alpha spending / group sequential designs?”
	•	Response: Those require pre-specified look schedules; confidence sequences/e-values support arbitrary stopping and continuous monitoring. Atlas includes periodic-look and arbitrary stop rules.
	•	Artifact: Stopping rule comparison section.
	4.	“Your guarantees depend on boundedness; real metrics aren’t bounded.”
	•	Response: v1 is explicit: guarantee-tier outputs require declared bounds; otherwise we either refuse or use clipped-tier with clear disclosure.
	•	Artifact: Assumption audit + out-of-range scenario + docs “What breaks assumptions.”
	5.	“Drift kills this; online systems drift constantly.”
	•	Response: Correct—drift changes the problem. Tool detects drift signals and downgrades from “guaranteed” to “diagnostic.”
	•	Artifact: Drift scenario plots + warning behavior in demo.
	6.	“Permutation/bootstrap would be more robust.”
	•	Response: Those aren’t naturally streaming and expensive under continuous monitoring. This tool targets streaming O(1) updates and optional stopping validity.
	•	Artifact: Throughput benchmarks + streaming API.
	7.	“Why e-values? Everyone understands p-values.”
	•	Response: e-values provide a clean optional-stopping-safe decision threshold and accumulate evidence; demo shows how peeking inflates naive p-values but not e-values.
	•	Artifact: Side-by-side demo panel and Type I peeking plot.
	8.	“Isn’t this just reimplementing known results?”
	•	Response: The novelty is productization: unified taxonomy + defaults + atlas + reproducibility + integration-ready CLI.
	•	Artifact: Method matrix + recommender outputs + report generator.
	9.	“Your default recommender will choose wrong in edge cases.”
	•	Response: Recommender decisions are logged with reasons; atlas includes “recommender audit” showing where each choice wins/loses. Users can always override.
	•	Artifact: Recommender audit table + override examples.
	10.	“How do you prevent silent misuse?”

	•	Response: Strong input validation, assumption tags, tier badges, and explicit refusal modes.
	•	Artifact: Error messages + docs “Failure modes & responses.”

⸻

SECTION 9 — Launch Assets

Show HN post text (short, factual, non-hype)

Hi HN — I built Anytime, a small Python library/CLI for peeking-safe streaming inference.

It provides:
	•	Confidence sequences for means and mean differences (A/B tests) that remain valid under continuous monitoring and optional stopping.
	•	E-values with a simple “reject if e ≥ 1/α” rule that’s optional-stopping safe.
	•	An atlas generator that runs systematic simulations (different distributions + stopping rules) and produces a report showing coverage, Type I error, power, and runtime.

The repo includes a local demo app that contrasts anytime-valid methods with naive repeated p-value peeking.

The goal is to make the statistical contract explicit and testable: every method states assumptions, and the atlas tries to falsify them.

1-minute demo script
	1.	Open the demo app. Select “A/B Bernoulli conversion” and set α=0.05.
	2.	Start streaming data. Show the confidence sequence band and the e-value curve.
	3.	Toggle “peek + stop early” — show naive p-value triggers too often under null.
	4.	Switch to “small lift” vs “big lift” and show stopping time shifts.
	5.	Flip “inject out-of-range values” to show the tool refusing or clipping with disclosure.
	6.	End with: “Run python -m anytime.atlas to reproduce all plots and see which methods win where.”

What this is NOT (avoid overclaiming)
	•	Not a general solution for nonstationary drift (it detects and warns; it doesn’t “fix drift”).
	•	Not a causal inference engine.
	•	Not a replacement for experiment design; it makes monitoring/stopping safe under stated assumptions.
	•	Not guaranteed for unbounded heavy-tailed metrics unless you provide a valid bounding/clipping policy.

5 short social posts / thread bullets
	1.	Optional stopping is the silent killer of A/B testing: peeking turns 5% false positives into “who knows.” Anytime-valid inference fixes that.
	2.	Confidence sequences give intervals that are valid at every time, not just at a pre-chosen sample size.
	3.	E-values give a simple streaming decision rule: reject when e ≥ 1/α — safe under peeking.
	4.	The hard part isn’t one formula; it’s validating across stopping rules and regimes. So I built an “atlas” benchmark report.
	5.	Everything is reproducible: configs + seeds + artifact logs. If the contract fails, the benchmark should catch it.

⸻

SECTION 10 — Agent-Optimized Build Order (18 tasks)

Each task includes: goal, files touched, acceptance tests, done definition.

Task 1 — Repo skeleton + tooling
	•	Goal: Create pyproject.toml, package layout, lint/test scaffolding.
	•	Files: pyproject.toml, anytime/__init__.py, tests/, Makefile (or justfile).
	•	Acceptance tests: python -c "import anytime" works; pytest runs empty suite.
	•	Done: Clean install/editable install works; CI-like commands documented.

Task 2 — StreamSpec / ABSpec + validation utilities
	•	Goal: Define specs, tier enum, shared validation.
	•	Files: anytime/spec.py, anytime/errors.py.
	•	Tests: invalid alpha/support raises; kind mismatches raise.
	•	Done: Specs are stable and used everywhere.

Task 3 — Online estimators (mean/var trackers)
	•	Goal: Implement O(1) mean and variance updates.
	•	Files: anytime/core/estimators.py.
	•	Tests: match batch mean/var on random data; numerical stability checks.
	•	Done: Estimators used by CS implementations.

Task 4 — Hoeffding confidence sequence (one-sample)
	•	Goal: Implement bounded Hoeffding-style CS with anytime guarantee.
	•	Files: anytime/cs/hoeffding.py.
	•	Tests: endpoints in [a,b], alpha monotonicity, basic smoke simulation.
	•	Done: Produces Interval objects with metadata.

Task 5 — Empirical Bernstein confidence sequence (one-sample)
	•	Goal: Variance-adaptive CS for bounded outcomes.
	•	Files: anytime/cs/empirical_bernstein.py.
	•	Tests: width ≤ Hoeffding on low-variance synthetic; no NaNs at small t.
	•	Done: Works for streams; handles early-time edge cases.

Task 6 — Bernoulli-specialized CS
	•	Goal: Implement Bernoulli-tight CS (or a known tight construction) with clear assumptions.
	•	Files: anytime/cs/bernoulli_exact.py.
	•	Tests: only accepts 0/1; empirical width improvements vs Hoeffding in Bernoulli scenarios.
	•	Done: Included in recommender when kind="bernoulli".

Task 7 — Two-sample wrappers (Hoeffding + EB)
	•	Goal: Mean-difference CS from two streams.
	•	Files: anytime/twosample/hoeffding.py, anytime/twosample/empirical_bernstein.py.
	•	Tests: symmetry under swapping arms; null simulations show correct Type I under stopping.
	•	Done: update(x, arm) works and yields Interval for Δ.

Task 8 — E-value (one-sample Bernoulli mixture)
	•	Goal: e-process for testing p vs p0 with optional stopping validity.
	•	Files: anytime/evalues/bernoulli.py.
	•	Tests: under null, decision rate ≤ α in Monte Carlo; under alternative, power increases.
	•	Done: EValue object emitted; threshold logic implemented.

Task 9 — E-value (two-sample bounded mean difference)
	•	Goal: Two-sample e-process (bounded) for Δ vs 0.
	•	Files: anytime/evalues/twosample.py.
	•	Tests: null stopping Type I; alternative power.
	•	Done: Exposed as public API.

Task 10 — Diagnostics: range + missingness + drift heuristic
	•	Goal: Implement assumption checks and tier downgrades.
	•	Files: anytime/diagnostics/range.py, missingness.py, drift.py.
	•	Tests: out-of-range triggers error/clip; drift scenario triggers warning flag.
	•	Done: Methods attach diagnostics to Interval/EValue meta.

Task 11 — Default recommender
	•	Goal: Choose method based on spec + diagnostics and produce explanation.
	•	Files: anytime/recommend.py.
	•	Tests: bernoulli spec → BernoulliCS; bounded low variance → EB; drift flagged → conservative / diagnostic.
	•	Done: Recommendation is deterministic, logged, and overrideable.

Task 12 — Artifact logging + reproducibility manifest
	•	Goal: JSONL logger + manifest.json writer.
	•	Files: anytime/logging.py.
	•	Tests: manifest contains config + seed; log writes expected fields.
	•	Done: Every CLI/atlas run creates a run directory with artifacts.

Task 13 — Plotting utilities
	•	Goal: Standard plots for CS bands, e-values, stopping time distributions.
	•	Files: anytime/plotting.py.
	•	Tests: plot functions run headless (Agg backend) and save images.
	•	Done: Used by atlas and demo.

Task 14 — CLI: simulate + mean + abtest
	•	Goal: Implement anytime CLI with config parsing and CSV ingestion.
	•	Files: anytime/cli.py, anytime/io/csv.py, configs/*.yaml.
	•	Tests: CLI commands run on tiny sample CSV; schema validation works.
	•	Done: “One command demo” and “one command benchmark” paths are feasible.

Task 15 — Atlas scenarios + runner
	•	Goal: Define 16 scenarios and run sweeps deterministically.
	•	Files: anytime/atlas/scenarios.py, runner.py, metrics.py.
	•	Tests: smoke atlas runs in <N seconds; outputs results file.
	•	Done: Produces metrics for all methods × scenarios.

Task 16 — Report generator
	•	Goal: Turn atlas results into report.html (or md + assets).
	•	Files: anytime/atlas/report.py, templates if needed.
	•	Tests: report builds; includes required plots/tables.
	•	Done: Report is readable and answers skeptical questions.

Task 17 — Interactive demo app (Streamlit) + launcher
	•	Goal: Build local demo with toggles and side-by-side invalid baseline.
	•	Files: demos/app.py, anytime/demo.py.
	•	Tests: python -m anytime.demo launches; main widgets render; synthetic streams run.
	•	Done: Demo is self-contained and persuasive.

Task 18 — Docs + release checklist
	•	Goal: README, guides, cookbook recipes, plus a release checklist.
	•	Files: README.md, docs/guides/*, docs/cookbook/*.
	•	Tests: All snippets run via doctest-like harness (optional) or CI script.
	•	Done: A new user can install, run demo, run atlas, and understand the contract.

⸻

Project Decision Summary
	•	Core guarantee / contract:
Anytime-valid inference for means and mean differences:
\Pr(\forall t:\ \theta \in C_t)\ge 1-\alpha and optional-stopping-safe decisions via e-values:
\Pr_{H_0}(\exists t:\ E_t \ge 1/\alpha)\le \alpha.
	•	Differentiator:
Atlas + defaults + integration polish: unified methods behind one API, systematic regime sweeps with reproducible reports, and a recommender that chooses conservative-but-competitive defaults with explicit assumption tiers.
	•	v1 work units (concrete):
	•	18 implementation tasks
	•	~120 acceptance tests (unit + property + simulation + CLI smoke)
	•	16 benchmark scenarios × 8+ method variants → 128+ experiment cells (more with parameter sweeps)
	•	Risks + mitigations
	1.	Subtle math bugs → mitigation: independent derivation notes per method + Monte Carlo falsification under many stopping rules + golden snapshots.
	2.	Scope creep (too many methods) → mitigation: v1 hard-focus on bounded/Bernoulli means + differences; exclude regression/GLMs/drift-solvers.
	3.	Misuse in unbounded/drifting settings → mitigation: strict validation + tiering + refusal modes + loud docs.
	4.	Performance complaints → mitigation: O(1) updates, vectorized simulation, honest runtime tables in atlas.

⸻
