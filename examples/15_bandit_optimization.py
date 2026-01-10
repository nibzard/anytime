#!/usr/bin/env python3
"""
15_bandit_optimization.py - Multi-Armed Bandit with Anytime-Valid Inference

ADVANCED

This example shows how to use anytime-valid inference for multi-armed bandit
problems - a classic optimization challenge where you balance exploration
(learning which option is best) vs exploitation (using the best option).

Perfect for:
- Website optimization (headline testing)
- Ad placement optimization
- Recommendation systems
- Clinical trial allocation
- Resource allocation problems

SCENARIO:
You're running a website with 4 different headlines. You want to quickly
find the best headline while minimizing lost clicks from showing bad ones.

REAL-WORLD CONTEXT:
- Traditional A/B testing wastes traffic on losing variants
- Bandit algorithms adaptively shift traffic to winners
- Anytime-valid inference provides guarantees during exploration
- You can stop anytime with valid confidence intervals

WHAT YOU'LL LEARN:
- Bandit problem framing (exploration vs exploitation)
- Adaptive allocation with confidence sequences
- Regret minimization strategies
- Production bandit patterns

TIME: 20 minutes
"""

from anytime import StreamSpec, ABSpec
from anytime.cs import EmpiricalBernsteinCS
import random
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class BanditArm:
    """Represents one option (arm) in a bandit problem."""
    name: str
    true_rate: float  # Actual success rate (unknown in practice)
    cs: EmpiricalBernsteinCS  # Confidence sequence for this arm

class MultiArmedBandit:
    """
    Multi-armed bandit with anytime-valid confidence sequences.

    STRATEGY:
    - Track confidence sequences for each arm
    - Periodically estimate which arm is best
    - Shift traffic toward promising arms
    - Maintain statistical guarantees throughout
    """

    def __init__(self, arms: List[str], alpha: float = 0.05):
        """Initialize bandit with given arms."""
        spec = StreamSpec(
            alpha=alpha,
            support=(0.0, 1.0),
            kind="bounded",
            two_sided=True
        )

        self.arms = {name: BanditArm(name, 0.0, EmpiricalBernsteinCS(spec))
                     for name in arms}
        self.total_samples = 0

    def select_arm_epsilon_greedy(self, epsilon: float = 0.1) -> str:
        """
        Epsilon-greedy selection: explore with prob epsilon, exploit otherwise.

        EXPLORE: Random arm (gather data)
        EXPLOIT: Arm with highest observed rate
        """
        if random.random() < epsilon:
            # Explore: pick random arm
            return random.choice(list(self.arms.keys()))
        else:
            # Exploit: pick best arm (highest observed rate)
            best_arm = None
            best_rate = -1

            for name, arm in self.arms.items():
                if arm.cs.interval().t > 0:  # Has data
                    rate = arm.cs.interval().estimate
                    if rate > best_rate:
                        best_rate = rate
                        best_arm = name

            return best_arm if best_arm else random.choice(list(self.arms.keys()))

    def select_arm_ucb(self) -> str:
        """
        Upper Confidence Bound (UCB) selection.

        Pick arm with highest UCB = estimate + confidence_width
        Optimistic about uncertainty: explores uncertain arms
        """
        best_arm = None
        best_ucb = -1

        for name, arm in self.arms.items():
            iv = arm.cs.interval()

            if iv.t == 0:
                # No data yet, give it maximum priority
                ucb = 1.0
            else:
                # UCB = estimate + upper bound width
                ucb = iv.estimate + (iv.hi - iv.estimate)

            if ucb > best_ucb:
                best_ucb = ucb
                best_arm = name

        return best_arm

    def select_arm_thompson_sampling(self) -> str:
        """
        Thompson Sampling: Bayesian-style selection.

        Sample from each arm's distribution, pick highest sample.
        Naturally balances exploration and exploitation.
        """
        best_arm = None
        best_sample = -1

        for name, arm in self.arms.items():
            iv = arm.cs.interval()

            if iv.t == 0:
                sample = random.random()  # Uniform prior
            else:
                # Approximate beta distribution from CI
                # Simple approximation: sample from normal centered at estimate
                import math
                std = (iv.hi - iv.lo) / 4  # Rough approximation
                sample = random.gauss(iv.estimate, std)
                sample = max(0, min(1, sample))  # Clamp to [0,1]

            if sample > best_sample:
                best_sample = sample
                best_arm = name

        return best_arm

    def update(self, arm: str, reward: float):
        """Update the confidence sequence for the selected arm."""
        self.arms[arm].cs.update(reward)
        self.total_samples += 1

    def get_arm_stats(self) -> Dict[str, Dict]:
        """Get current statistics for all arms."""
        stats = {}
        for name, arm in self.arms.items():
            iv = arm.cs.interval()
            stats[name] = {
                'samples': iv.t,
                'rate': iv.estimate,
                'ci_lower': iv.lo,
                'ci_upper': iv.hi,
                'ci_width': iv.hi - iv.lo
            }
        return stats

def demo_headline_optimization():
    """
    Optimize website headlines using multi-armed bandit.
    """
    print("\n" + "=" * 80)
    print("🎰 MULTI-ARMED BANDIT: Headline Optimization")
    print("=" * 80)

    print("""
SCENARIO:
  Testing 4 different headlines for a website.

  Headlines:
    A: "Sign Up Now"              (True rate: 8%)
    B: "Join 10,000+ Users"       (True rate: 12%) ← Best!
    C: "Get Started Free"         (True rate: 10%)
    D: "Start Your Journey"       (True rate: 6%)

  Goal: Find the best headline quickly while maximizing clicks.

BANDIT STRATEGIES:
  1. EPSILON-GREEDY: Explore 10% randomly, exploit 90%
  2. UCB (Upper Confidence Bound): Optimistic about uncertainty
  3. THOMPSON SAMPLING: Sample from posterior, pick best
    """)

    # Setup bandit
    arms = ['A', 'B', 'C', 'D']
    true_rates = {'A': 0.08, 'B': 0.12, 'C': 0.10, 'D': 0.06}

    print("\n" + "-" * 100)
    print(f"{'Samples':>10} | {'A':>8} | {'B':>8} | {'C':>8} | {'D':>8} | {'Best':>8} | {'Strategy':>20}")
    print("-" * 100)

    # Test different strategies
    strategies = [
        ("Epsilon-Greedy (ε=0.1)", lambda b: b.select_arm_epsilon_greedy(0.1)),
        ("UCB", lambda b: b.select_arm_ucb()),
        ("Thompson Sampling", lambda b: b.select_arm_thompson_sampling())
    ]

    results = {}

    for strategy_name, strategy_func in strategies:
        bandit = MultiArmedBandit(arms)
        arm_counts = {arm: 0 for arm in arms}
        total_rewards = 0

        # Run for 1000 visitors
        for _ in range(1000):
            # Select arm using strategy
            selected_arm = strategy_func(bandit)
            arm_counts[selected_arm] += 1

            # Simulate click/no-click
            clicked = 1 if random.random() < true_rates[selected_arm] else 0
            total_rewards += clicked

            # Update bandit
            bandit.update(selected_arm, clicked)

        results[strategy_name] = {
            'arm_counts': arm_counts,
            'total_rewards': total_rewards,
            'final_stats': bandit.get_arm_stats()
        }

    # Display results
    for i in range(0, 1000, 200):
        print(f"{i:>10} |", end="")
        for strategy_name, strategy_func in strategies:
            break
        print()

    print(f"\n{'Strategy':>25} | {'A':>8} | {'B':>8} | {'C':>8} | {'D':>8} | {'Rewards':>10} | {'Rate':>8}")
    print("-" * 100)

    for strategy_name, data in results.items():
        print(f"{strategy_name:>25} |", end="")
        for arm in arms:
            count = data['arm_counts'][arm]
            pct = count / 1000 * 100
            print(f"{pct:7.1f}% |", end="")

        rewards = data['total_rewards']
        rate = rewards / 1000 * 100
        print(f"{rewards:>10} | {rate:7.2f}%")

    print("\n💡 Bandit strategies learn to favor the best headline (B) over time!")

def demo_regret_comparison():
    """
    Compare strategies by regret (lost rewards vs optimal).
    """
    print("\n" + "=" * 80)
    print("📊 REGRET ANALYSIS: How Much Do We Lose?")
    print("=" * 80)

    print("""
REGRET = Difference between actual rewards and optimal rewards.

  Lower regret = Better strategy
  Optimal strategy would always pick arm B (12% rate)

We measure cumulative regret over time.
    """)

    arms = ['A', 'B', 'C', 'D']
    true_rates = {'A': 0.08, 'B': 0.12, 'C': 0.10, 'D': 0.06}
    optimal_rate = max(true_rates.values())  # B has 12%

    strategies = [
        ("Random (baseline)", lambda: random.choice(arms)),
        ("Epsilon-Greedy", lambda: random.choice(arms) if random.random() < 0.1 else 'B'),  # Simplified
        ("UCB", lambda: random.choice(arms)),  # Placeholder
    ]

    # For simplicity, just show random vs perfect
    print("\n" + "-" * 80)
    print(f"{'Samples':>10} | {'Random Regret':>18} | {'Perfect Regret':>18} | {'Gap':>10}")
    print("-" * 80)

    random_seed = 42
    random.seed(random_seed)

    random_regret = 0
    perfect_regret = 0

    for t in [100, 500, 1000, 2000, 5000]:
        # Random strategy
        for _ in range(t):
            arm = random.choice(arms)
            reward = 1 if random.random() < true_rates[arm] else 0
            optimal_reward = 1 if random.random() < optimal_rate else 0
            random_regret += (optimal_reward - reward)

        # Reset and do perfect
        random.seed(random_seed)
        perfect_regret = 0
        for _ in range(t):
            arm = 'B'  # Always pick best
            reward = 1 if random.random() < true_rates[arm] else 0
            optimal_reward = 1 if random.random() < optimal_rate else 0
            perfect_regret += (optimal_reward - reward)

        gap = random_regret - perfect_regret

        print(f"{t:10d} | {random_regret:18.1f} | {perfect_regret:18.1f} | {gap:10.1f}")

    print("\n💡 Perfect strategy (always knowing B is best) has minimal regret!")
    print("   Bandit algorithms aim to approach this by learning quickly.")

def demo_adaptive_allocation():
    """
    Demonstrate adaptive traffic allocation over time.
    """
    print("\n" + "=" * 80)
    print("🔄 ADAPTIVE ALLOCATION: How Traffic Shifts Over Time")
    print("=" * 80)

    print("""
Watch how a smart bandit algorithm shifts traffic toward winning arms
as it learns which headlines perform best.
    """)

    arms = ['A', 'B', 'C', 'D']
    true_rates = {'A': 0.08, 'B': 0.12, 'C': 0.10, 'D': 0.06}

    bandit = MultiArmedBandit(arms)
    allocation_history = []

    # Track allocation every 100 samples
    for t in range(2000):
        # UCB strategy
        arm = bandit.select_arm_ucb()

        # Get reward
        clicked = 1 if random.random() < true_rates[arm] else 0
        bandit.update(arm, clicked)

        # Record allocation every 100
        if (t + 1) % 100 == 0:
            stats = bandit.get_arm_stats()
            allocation = {arm: stats[arm]['samples'] for arm in arms}
            allocation_history.append((t + 1, allocation))

    print("\n" + "-" * 90)
    print(f"{'Time':>8} | {'A %':>8} | {'B %':>8} | {'C %':>8} | {'D %':>8} | {'Leader':>10}")
    print("-" * 90)

    for time, alloc in allocation_history:
        total = sum(alloc.values())
        a_pct = alloc['A'] / total * 100
        b_pct = alloc['B'] / total * 100
        c_pct = alloc['C'] / total * 100
        d_pct = alloc['D'] / total * 100

        # Find leader
        leader = max(alloc.keys(), key=lambda x: alloc[x])

        print(f"{time:8d} | {a_pct:7.1f}% | {b_pct:7.1f}% | {c_pct:7.1f}% | {d_pct:7.1f}% | {leader:>10}")

    print("\n💡 Traffic shifts toward B (the true winner) as confidence increases!")

def main():
    print("=" * 80)
    print("🎰 Multi-Armed Bandit Optimization with Anytime-Valid Inference")
    print("=" * 80)

    print("""
This example demonstrates multi-armed bandit optimization using
anytime-valid confidence sequences. Bandit problems balance
exploration (learning) vs exploitation (using what works).

THE BANDIT PROBLEM:

  You have K options (arms), each with unknown success rates.
  You want to:
    1. Learn which arm is best (exploration)
    2. Maximize rewards by pulling good arms (exploitation)

  Classic dilemma:
    • Explore → Learn more but waste pulls on bad arms
    • Exploit → Use known good arms but miss better ones

ANYTIME-VALID INFERENCE HELPS:

  ✓ Confidence sequences track uncertainty for each arm
  ✓ Valid even with adaptive/sequential decisions
  ✓ Can stop anytime with valid confidence intervals
  ✓ Regret bounds quantify learning efficiency

EXAMPLES COVERED:
  1. Headline optimization with multiple strategies
  2. Regret analysis (lost rewards vs optimal)
  3. Adaptive allocation over time

BANDIT STRATEGIES:
  • EPSILON-GREEDY: Explore randomly ε fraction of the time
  • UCB: Pick arm with highest upper confidence bound
  • THOMPSON SAMPLING: Sample from posterior, pick highest

REAL-WORLD APPLICATIONS:
  • Website optimization (headlines, layouts, CTAs)
  • Ad placement and creative testing
  • Recommendation system exploration
  • Clinical trial adaptive allocation
  • Resource allocation and routing
  • Price optimization

DATASETS IN PRODUCTION:
  • Your website analytics (Google Analytics, Mixpanel)
  • Ad platform performance data
  • Recommendation system logs
  • Clinical trial databases
    """)

    # Run demonstrations
    demo_headline_optimization()
    demo_regret_comparison()
    demo_adaptive_allocation()

    # Final summary
    print("\n" + "=" * 80)
    print("✅ SUMMARY")
    print("=" * 80)

    print("""
WHAT YOU LEARNED:
  ✓ Multi-armed bandit problem framing
  ✓ Epsilon-greedy, UCB, and Thompson sampling strategies
  ✓ Regret as a performance metric
  ✓ Adaptive allocation patterns

KEY INSIGHTS:
  • Bandits balance exploration vs exploitation
  • Anytime-valid CI enables adaptive decisions
  • Regret quantifies cost of learning
  • UCB naturally explores uncertain arms

PRODUCTION TIPS:
  ✓ Start with epsilon-greedy (simple, works well)
  ✓ Track arm statistics and confidence intervals
  ✓ Monitor regret over time
  ✓ Consider Thompson sampling for complex problems
  ✓ Use anytime-valid CI for guarantees

NEXT STEPS:
  • Example 12: Currency monitoring
  • Example 13: Retail analytics
  • Example 14: Medical trials
  • Example 16: Time series forecasting

REFERENCES:
  • "Bandit Algorithms" (Lattimore & Szepesvari)
  • "Multi-Armed Bandit Decision Making" (Scott, 2010)
  • "Confidence Sequences for Bandits" (Waudby-Smith & Ramdas, 2023)
    """)

if __name__ == "__main__":
    main()
