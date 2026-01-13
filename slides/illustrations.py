"""Generate illustrations for peeking lecture slides."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path
from scipy import stats

from anytime import StreamSpec, ABSpec
from anytime.cs import HoeffdingCS, EmpiricalBernsteinCS, BernoulliCS
from anytime.evalues import TwoSampleMeanMixtureE
from anytime.atlas.runner import naive_peeking_test


# =============================================================================
# ILLUSTRATION 1: False Positive Inflation (Peeking Problem)
# =============================================================================

def generate_peeking_inflation_plot(save_path):
    """Bar chart showing expected vs actual FPR under peeking."""
    fig, ax = plt.subplots(figsize=(10, 6))

    methods = ['Fixed Horizon\n(check once)', 'Peek Every 50', 'Peek Every 20', 'Peek Every 10']
    fpr_expected = [0.05, 0.05, 0.05, 0.05]
    # Simulate false positive rates under peeking
    fpr_actual = [0.05, 0.12, 0.22, 0.38]

    x = np.arange(len(methods))
    width = 0.35

    bars1 = ax.bar(x - width/2, fpr_expected, width, label='Expected (α=0.05)', color='gray', alpha=0.7)
    bars2 = ax.bar(x + width/2, fpr_actual, width, label='Actual with Peeking', color='#e74c3c', alpha=0.9)

    ax.set_ylabel('False Positive Rate', fontsize=12)
    ax.set_title('Peeking Inflates False Positives: 5% → 38%', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(methods, fontsize=11)
    ax.legend(fontsize=11)
    ax.axhline(y=0.05, color='gray', linestyle='--', alpha=0.5)
    ax.set_ylim([0, 0.45])
    ax.grid(True, alpha=0.3, axis='y')

    # Add percentage labels on bars
    for bar in bars2:
        height = bar.get_height()
        ax.annotate(f'{height:.0%}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords='offset points',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
    return fig


# =============================================================================
# ILLUSTRATION 2: Confidence Funnel (Time-Uniform Coverage)
# =============================================================================

def generate_confidence_funnel_plot(save_path):
    """Funnel plot showing confidence bands narrowing over time."""
    np.random.seed(42)
    true_p = 0.60
    n = 500

    spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bernoulli", two_sided=True)
    cs = BernoulliCS(spec)

    times = []
    estimates = []
    los = []
    his = []

    data = [1 if np.random.random() < true_p else 0 for _ in range(n)]

    for t, x in enumerate(data, 1):
        cs.update(x)
        iv = cs.interval()
        if t % 5 == 0:
            times.append(t)
            estimates.append(iv.estimate)
            los.append(iv.lo)
            his.append(iv.hi)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.fill_between(times, los, his, alpha=0.3, color='#3498db', label='95% Confidence Sequence')
    ax.plot(times, estimates, 'k-', linewidth=2, label='Estimate')
    ax.axhline(y=true_p, color='r', linestyle='--', linewidth=2, label='True Value (0.60)')

    # Add annotations
    ax.annotate('Wide at start\n(high uncertainty)', xy=(50, 0.35), fontsize=10,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))
    ax.annotate('Narrows over time\n(more precision)', xy=(400, 0.58), fontsize=10,
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))

    ax.set_xlabel('Time (samples observed)', fontsize=12)
    ax.set_ylabel('Conversion Rate', fontsize=12)
    ax.set_title('Confidence Funnel: Time-Uniform 95% Coverage', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 1])

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
    return fig


# =============================================================================
# ILLUSTRATION 3: Traditional CI vs Confidence Sequence Comparison
# =============================================================================

def generate_traditional_vs_cs_plot(save_path):
    """Side-by-side comparison of traditional CI (fails) vs CS (valid) under peeking."""
    np.random.seed(42)
    true_mean = 0.5
    n_max = 500
    n_sim = 200

    # Track coverage for traditional CI (peeking - INVALID)
    traditional_covered = 0
    for sim in range(n_sim):
        np.random.seed(sim)
        data = np.random.binomial(1, true_mean, n_max)
        traditional_ok = True
        for check_point in [50, 100, 200, 300, 400, 500]:
            sample = data[:check_point]
            ci = stats.t.interval(0.95, len(sample)-1, loc=np.mean(sample), scale=stats.sem(sample))
            if not (ci[0] <= true_mean <= ci[1]):
                traditional_ok = False
        if traditional_ok:
            traditional_covered += 1
    trad_cov = traditional_covered / n_sim

    # Track coverage for CS (peeking - VALID)
    cs_covered = 0
    for sim in range(n_sim):
        np.random.seed(sim)
        data = np.random.binomial(1, true_mean, n_max)
        spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bernoulli", two_sided=True)
        cs = BernoulliCS(spec)
        cs_ok = True
        for x in data:
            cs.update(x)
            iv = cs.interval()
            if not (iv.lo <= true_mean <= iv.hi):
                cs_ok = False
        if cs_ok:
            cs_covered += 1
    cs_cov = cs_covered / n_sim

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Left: Traditional CI
    color1 = '#e74c3c' if trad_cov < 0.90 else '#27ae60'
    ax1.bar(['Traditional CI\n(peeking INVALID)'], [trad_cov], color=color1, alpha=0.8, width=0.5)
    ax1.axhline(y=0.95, color='gray', linestyle='--', label='Target (95%)', linewidth=2)
    ax1.set_ylabel('Coverage Rate', fontsize=12)
    ax1.set_title(f'Traditional CI: {trad_cov:.1%} coverage', fontsize=13, fontweight='bold')
    ax1.set_ylim([0, 1])
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3, axis='y')

    # Right: Confidence Sequence
    ax2.bar(['Confidence Sequence\n(peeking VALID)'], [cs_cov], color='#27ae60', alpha=0.8, width=0.5)
    ax2.axhline(y=0.95, color='gray', linestyle='--', label='Target (95%)', linewidth=2)
    ax2.set_ylabel('Coverage Rate', fontsize=12)
    ax2.set_title(f'Confidence Sequence: {cs_cov:.1%} coverage', fontsize=13, fontweight='bold')
    ax2.set_ylim([0, 1])
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3, axis='y')

    plt.suptitle('Why Traditional Methods Fail with Peeking', fontsize=15, fontweight='bold')
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
    return fig


# =============================================================================
# ILLUSTRATION 4: Method Comparison (Hoeffding vs Empirical Bernstein vs Bernoulli)
# =============================================================================

def generate_method_comparison_plot(save_path):
    """Overlapping funnel plots showing interval width trade-offs."""
    np.random.seed(42)
    true_p = 0.60
    n = 500
    data = [1 if np.random.random() < true_p else 0 for _ in range(n)]

    spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bernoulli", two_sided=True)

    methods_data = []
    for cs_class, color in [
        (HoeffdingCS, '#3498db'),
        (EmpiricalBernsteinCS, '#e74c3c'),
        (BernoulliCS, '#27ae60')
    ]:
        cs = cs_class(spec)
        widths = []
        times = []

        for t, x in enumerate(data, 1):
            cs.update(x)
            if t % 5 == 0:
                iv = cs.interval()
                widths.append(iv.hi - iv.lo)
                times.append(t)

        methods_data.append((times, widths, color))

    fig, ax = plt.subplots(figsize=(12, 6))

    labels = ['Hoeffding\n(most conservative)', 'Empirical Bernstein\n(variance-adaptive)', 'Bernoulli\n(tightest for binary)']
    for (times, widths, color), label in zip(methods_data, labels):
        ax.plot(times, widths, label=label, color=color, linewidth=2.5, alpha=0.8)

    ax.set_xlabel('Sample Size', fontsize=12)
    ax.set_ylabel('Interval Width', fontsize=12)
    ax.set_title('Method Comparison: Interval Width vs Sample Size', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11, loc='upper right')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
    return fig


# =============================================================================
# ILLUSTRATION 5: E-Value Growth
# =============================================================================

def generate_evalue_growth_plot(save_path):
    """E-value trajectory crossing the decision threshold."""
    np.random.seed(42)
    rate_a, rate_b = 0.50, 0.60
    n = 500

    spec = ABSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=False)
    evalue = TwoSampleMeanMixtureE(spec, delta0=0.0, side="ge")

    evalues = []
    times = []

    for t in range(1, n + 1):
        if t % 2 == 1:
            arm, val = "A", 1 if np.random.random() < rate_a else 0
        else:
            arm, val = "B", 1 if np.random.random() < rate_b else 0
        evalue.update((arm, val))

        if t % 10 == 0:
            ev = evalue.evalue()
            evalues.append(max(ev.e, 0.01))  # Avoid log(0)
            times.append(t)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(times, evalues, 'g-', linewidth=2.5, label='E-value', alpha=0.8)
    ax.axhline(y=20, color='r', linestyle='--', linewidth=2, label='Decision Threshold (1/α = 20)')

    # Shade decision region
    ax.fill_between(times, 0, evalues, where=np.array(evalues) >= 20,
                    alpha=0.3, color='green', label='Decision Region')

    ax.set_xlabel('Total Observations (A + B)', fontsize=12)
    ax.set_ylabel('E-value (log scale)', fontsize=12)
    ax.set_title('E-Value Growth: Stop When Evidence Threshold is Crossed', fontsize=14, fontweight='bold')
    ax.set_yscale('log')
    ax.legend(fontsize=11, loc='upper left')
    ax.grid(True, alpha=0.3, which='both')
    ax.set_ylim([0.01, 1000])

    # Annotate stopping point
    stop_idx = next((i for i, e in enumerate(evalues) if e >= 20), None)
    if stop_idx:
        ax.annotate(f'Stop at t={times[stop_idx]}!\nSufficient evidence',
                    xy=(times[stop_idx], evalues[stop_idx]),
                    xytext=(times[stop_idx] + 50, evalues[stop_idx] * 0.3),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2),
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8),
                    fontsize=10, fontweight='bold')

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
    return fig


# =============================================================================
# ILLUSTRATION 6: Early Stopping Benefits
# =============================================================================

def generate_early_stopping_distribution_plot(save_path):
    """Histogram of stopping times showing early stopping benefits."""
    np.random.seed(42)
    true_lift = 0.10
    n_max = 1000
    n_sim = 100

    spec = ABSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=False)

    stop_times = []
    for sim in range(n_sim):
        np.random.seed(sim)
        evalue = TwoSampleMeanMixtureE(spec, delta0=0.0, side="ge")

        rate_a = 0.50
        rate_b = 0.50 + true_lift

        stopped = False
        for t in range(1, n_max + 1):
            if t % 2 == 1:
                arm, val = "A", 1 if np.random.random() < rate_a else 0
            else:
                arm, val = "B", 1 if np.random.random() < rate_b else 0
            evalue.update((arm, val))

            if t % 20 == 0 and evalue.evalue().decision:
                stop_times.append(t)
                stopped = True
                break

        if not stopped:
            stop_times.append(n_max)

    traditional_n = 1000
    median_stop = np.median(stop_times)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Left: Traditional
    ax1.bar([0], [traditional_n], width=0.5, color='gray', alpha=0.7)
    ax1.set_xlim(-0.5, 0.5)
    ax1.set_ylabel('Sample Size', fontsize=12)
    ax1.set_title('Traditional: Always N=1000', fontsize=13, fontweight='bold')
    ax1.set_xticks([])
    ax1.text(0, traditional_n / 2, f'N={traditional_n}\n100% of tests',
             ha='center', va='center', fontsize=12, fontweight='bold')

    # Right: Anytime
    ax2.hist(stop_times, bins=30, color='#27ae60', alpha=0.7, edgecolor='black')
    ax2.axvline(x=traditional_n, color='r', linestyle='--', linewidth=2, label='Traditional fixed N')
    ax2.axvline(x=median_stop, color='green', linestyle='-', linewidth=3,
                label=f'Median stop: {median_stop:.0f}')
    ax2.set_xlabel('Stopping Time (samples)', fontsize=12)
    ax2.set_ylabel('Frequency', fontsize=12)
    savings_pct = 100 * (1 - median_stop / traditional_n)
    ax2.set_title(f'Anytime: Median {median_stop:.0f} samples\n({savings_pct:.0f}% savings)',
                  fontsize=13, fontweight='bold')
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3, axis='y')

    plt.suptitle(f'Early Stopping: {savings_pct:.0f}% Average Sample Size Reduction',
                 fontsize=15, fontweight='bold')
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
    return fig


# =============================================================================
# ILLUSTRATION 7: Guarantee Tiers
# =============================================================================

def generate_guarantee_tiers_plot(save_path):
    """Tiered pyramid showing GOLD/SILVER/BRONZE guarantee tiers."""
    from matplotlib.patches import FancyBboxPatch

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Draw tiered pyramid
    tiers = [
        ('GOLD\nAll assumptions met\nTrust results blindly', 8, 9, '#FFD700', (5.5, 8.5)),
        ('SILVER\nMinor issues\nValid but conservative', 6, 7, '#C0C0C0', (4, 7.5)),
        ('BRONZE\nMajor issues\nDiagnostic only\nInvestigate assumptions', 4, 5, '#CD7F32', (2.5, 6.5))
    ]

    for tier_name, y_bottom, y_top, color, pos in tiers:
        box = FancyBboxPatch((pos[0], y_bottom), pos[1] - pos[0], y_top - y_bottom,
                             boxstyle="round,pad=0.1", edgecolor='black', facecolor=color, alpha=0.7, linewidth=2)
        ax.add_patch(box)

        lines = tier_name.split('\n')
        for i, line in enumerate(lines):
            fontweight = 'bold' if i == 0 else 'normal'
            ax.text((pos[0] + pos[1]) / 2, y_bottom + (y_top - y_bottom) / 2 + (1 - i) * 0.35, line,
                    ha='center', va='center', fontsize=11, fontweight=fontweight, color='black')

    # Add title
    ax.text(5, 9.7, 'Guarantee Tiers: Automatic Assumption Checking',
            ha='center', fontsize=15, fontweight='bold')

    # Add decision flowchart
    ax.text(8.5, 7, 'Decision Flow:', fontsize=12, fontweight='bold')
    ax.text(8.5, 6.4, '1. Check tier', fontsize=10)
    ax.text(8.5, 5.9, '2. If GOLD → Trust', fontsize=10, color='#27ae60', fontweight='bold')
    ax.text(8.5, 5.4, '3. If SILVER → Use caution', fontsize=10, color='#f39c12')
    ax.text(8.5, 4.9, '4. If BRONZE → Investigate', fontsize=10, color='#e74c3c')

    # Add example scenarios
    ax.text(1, 3.2, 'Example Scenarios:', fontsize=12, fontweight='bold')
    ax.text(0.3, 2.6, '✓ GOLD: Binary data, bounds correct', fontsize=10, color='#27ae60')
    ax.text(0.3, 2.1, '✓ SILVER: Some outliers clipped', fontsize=10, color='#f39c12')
    ax.text(0.3, 1.6, '✓ BRONZE: Many missing values', fontsize=10, color='#e74c3c')

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
    return fig


# =============================================================================
# ILLUSTRATION 8: A/B Test Dashboard
# =============================================================================

def generate_ab_test_dashboard_plot(save_path):
    """Mock A/B test dashboard showing lift evolution over time."""
    np.random.seed(42)
    n_days = 14
    visitors_per_day = 100

    rate_a, rate_b = 0.10, 0.13

    days = []
    lifts = []
    los = []
    his = []

    cumulative_a = cumulative_b = 0
    total_a = total_b = 0

    for day in range(1, n_days + 1):
        for _ in range(visitors_per_day):
            conv_a = 1 if np.random.random() < rate_a else 0
            cumulative_a += conv_a
            total_a += 1

            conv_b = 1 if np.random.random() < rate_b else 0
            cumulative_b += conv_b
            total_b += 1

        rate_a_est = cumulative_a / total_a
        rate_b_est = cumulative_b / total_b
        lift_est = rate_b_est - rate_a_est

        se = np.sqrt(rate_a_est * (1 - rate_a_est) / total_a + rate_b_est * (1 - rate_b_est) / total_b)
        margin = 1.96 * se

        days.append(day)
        lifts.append(lift_est)
        los.append(max(0, lift_est - margin))
        his.append(lift_est + margin)

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.fill_between(days, los, his, alpha=0.3, color='#3498db', label='95% CI for Lift')
    ax.plot(days, lifts, 'k-', linewidth=2.5, marker='o', label='Estimated Lift')
    ax.axhline(y=0, color='gray', linestyle='--', linewidth=1.5, label='No Difference')

    ax.set_xlabel('Experiment Day', fontsize=12)
    ax.set_ylabel('Lift (B - A)', fontsize=12)
    ax.set_title('A/B Test Dashboard: Conversion Rate Lift Over Time\nNew vs Old Checkout Flow',
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=11, loc='upper left')
    ax.grid(True, alpha=0.3)

    # Add business context
    text_str = (f"Total samples: A={total_a}, B={total_b}\n"
                f"True effect: +3 percentage points\n"
                f"Final lift: {lifts[-1]:.1%}\n"
                f"Decision: CI excludes 0 → Significant!")
    ax.text(0.98, 0.02, text_str, transform=ax.transAxes, fontsize=9,
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8),
            verticalalignment='bottom', horizontalalignment='right')

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
    return fig


# =============================================================================
# Batch Generation
# =============================================================================

def generate_all(output_dir='slides/images/'):
    """Generate all illustrations and save as PNGs."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    print(f"Generating illustrations to {output_path}/")

    generate_peeking_inflation_plot(output_path / 'peeking_inflation.png')
    print("  ✓ peeking_inflation.png")

    generate_confidence_funnel_plot(output_path / 'confidence_funnel.png')
    print("  ✓ confidence_funnel.png")

    generate_traditional_vs_cs_plot(output_path / 'traditional_vs_cs.png')
    print("  ✓ traditional_vs_cs.png")

    generate_method_comparison_plot(output_path / 'method_comparison.png')
    print("  ✓ method_comparison.png")

    generate_evalue_growth_plot(output_path / 'evalue_growth.png')
    print("  ✓ evalue_growth.png")

    generate_early_stopping_distribution_plot(output_path / 'early_stopping_distribution.png')
    print("  ✓ early_stopping_distribution.png")

    generate_guarantee_tiers_plot(output_path / 'guarantee_tiers.png')
    print("  ✓ guarantee_tiers.png")

    generate_ab_test_dashboard_plot(output_path / 'ab_test_dashboard.png')
    print("  ✓ ab_test_dashboard.png")

    print(f"\nAll 8 illustrations saved to {output_path}/")


if __name__ == '__main__':
    generate_all()
