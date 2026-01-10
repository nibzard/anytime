#!/usr/bin/env python3
"""
14_medical_trials.py - Clinical Trial Analysis

INTERMEDIATE

This example shows how to use anytime-valid inference for clinical trials
and medical research. Perfect for:
- Vaccine efficacy trials
- Treatment comparison studies
- Adverse event monitoring
- Interim analysis with early stopping

SCENARIO:
You're a statistician working on a Phase III clinical trial comparing
a new treatment to standard of care. You need to conduct interim analyses
to check for efficacy or safety concerns without inflating Type I error.

REAL-WORLD CONTEXT:
- Clinical trials are expensive and time-consuming
- Early stopping for efficacy can save lives and money
- Early stopping for harm (futility) protects patients
- Traditional statistics require strict pre-specified analyses
- Anytime-valid methods enable flexible monitoring

WHAT YOU'LL LEARN:
- Sequential monitoring of clinical trial endpoints
- Group sequential design principles
- Efficacy and futility monitoring
- Ethical considerations in early stopping

TIME: 15 minutes

DISCLAIMER: This is a simplified educational example. Real clinical trials
require rigorous protocol design, regulatory approval, and qualified
statisticians. Always consult with biostatisticians and regulatory experts.
"""

from anytime import StreamSpec, ABSpec
from anytime.cs import EmpiricalBernsteinCS, HoeffdingCS
from anytime.evalues import TwoSampleMeanMixtureE
from anytime.twosample import TwoSampleHoeffdingCS, TwoSampleEmpiricalBernsteinCS
import random
from dataclasses import dataclass
from typing import Optional

@dataclass
class TrialConfig:
    """Configuration for a clinical trial."""
    treatment_response_rate: float  # True response rate for treatment
    control_response_rate: float    # True response rate for control
    n_planned: int                  # Planned sample size
    alpha: float = 0.05             # Significance level
    min_effect: float = 0.05        # Minimum clinically meaningful effect

def simulate_trial_participants(config: TrialConfig, random_seed: int = 42):
    """
    Simulate participants in a clinical trial.

    In a real trial, this would be:
    - Sequential enrollment of eligible patients
    - Randomized assignment (treatment vs control)
    - Outcome measurement (response, survival, etc.)
    - Careful tracking of adverse events

    SCENARIO: Oncology trial
    - Primary endpoint: Treatment response (binary: responded or not)
    - Treatment (A): New immunotherapy
    - Control (B): Standard chemotherapy
    """
    random.seed(random_seed)

    participants = []
    for i in range(config.n_planned):
        # Random assignment (1:1)
        arm = 'A' if random.random() < 0.5 else 'B'

        # Response probability depends on arm
        if arm == 'A':  # Treatment
            prob_response = config.treatment_response_rate
        else:  # Control
            prob_response = config.control_response_rate

        # Did patient respond?
        response = 1 if random.random() < prob_response else 0

        participants.append({
            'patient_id': f"P{i:04d}",
            'arm': arm,
            'response': response,
            'enrollment_day': i // 10  # 10 patients enrolled per day
        })

    return participants

def demo_vaccine_efficacy_trial():
    """
    Analyze a vaccine efficacy trial with sequential monitoring.
    """
    print("\n" + "=" * 80)
    print("💉 CLINICAL TRIAL: Vaccine Efficacy with Sequential Monitoring")
    print("=" * 80)

    print("""
SCENARIO:
  Phase III trial for a new vaccine.

  Trial Design:
    - Treatment group: Receives new vaccine
    - Control group: Receives placebo
    - Primary endpoint: Infection (binary: infected or not)
    - Null hypothesis: Vaccine efficacy = 0%

  Vaccine Efficacy (VE) formula:
    VE = 1 - (infection_rate_treatment / infection_rate_control)

    If treatment infection rate = 2% and control = 4%:
    VE = 1 - (0.02 / 0.04) = 50%

  True parameters:
    - Control infection rate: 4%
    - Treatment infection rate: 2%
    - True vaccine efficacy: 50%
    """)

    # Setup trial configuration
    config = TrialConfig(
        treatment_response_rate=0.98,  # 98% stay healthy (2% infected)
        control_response_rate=0.96,    # 96% stay healthy (4% infected)
        n_planned=2000,
        alpha=0.05,
        min_effect=0.30  # 30% VE is clinically meaningful
    )

    # Setup two-sample confidence sequence
    # Note: We're tracking HEALTHY (response = 1), not infections
    # Using two_sided=True (required by TwoSampleHoeffdingCS)
    spec = ABSpec(
        alpha=0.05,
        support=(0.0, 1.0),
        kind="bounded",
        two_sided=True,  # Two-sided: we can detect treatment > control
        name="vaccine_efficacy"
    )

    cs = TwoSampleEmpiricalBernsteinCS(spec)

    print("\n📊 Simulating trial enrollment...")
    print("   (In real trials: enrollment over months/years)")

    # Generate trial data
    participants = simulate_trial_participants(config)

    # Track statistics
    treatment_healthy = 0
    treatment_total = 0
    control_healthy = 0
    control_total = 0

    print("\n" + "-" * 100)
    print(f"{'Patients':>10} | {'Tx Healthy':>12} | {'Ctrl Healthy':>12} | {'VE':>8} | {'95% CI':>20} | {'Status':>15}")
    print("-" * 100)

    efficacy_detected = None

    for i, patient in enumerate(participants, start=1):
        arm = patient['arm']
        healthy = patient['response']  # 1 = healthy (not infected)

        if arm == 'A':  # Treatment
            treatment_healthy += healthy
            treatment_total += 1
        else:  # Control (B)
            control_healthy += healthy
            control_total += 1

        # Update confidence sequence
        cs.update((arm, healthy))

        # Interim analysis every 200 patients
        if i % 200 == 0:
            iv = cs.interval()

            # Calculate vaccine efficacy
            tx_rate = treatment_healthy / treatment_total if treatment_total > 0 else 0
            ctrl_rate = control_healthy / control_total if control_total > 0 else 0

            infection_tx = 1 - tx_rate
            infection_ctrl = 1 - ctrl_rate
            ve = 1 - (infection_tx / infection_ctrl) if infection_ctrl > 0 else 0

            # Check if confidence interval for difference excludes 0
            # (iv.lo > 0 means treatment is significantly better)
            status = "✅ SIGNIFICANT" if iv.lo > 0 else "Continue"

            if iv.lo > 0 and efficacy_detected is None:
                efficacy_detected = i

            print(f"{i:10d} | {tx_rate:12.3f} | {ctrl_rate:12.3f} | {ve:7.1%} | "
                  f"({iv.lo:.3f}, {iv.hi:.3f}) | {status:>15}")

    # Final results
    iv = cs.interval()
    final_tx_rate = treatment_healthy / treatment_total
    final_ctrl_rate = control_healthy / control_total

    final_infection_tx = 1 - final_tx_rate
    final_infection_ctrl = 1 - final_ctrl_rate
    final_ve = 1 - (final_infection_tx / final_infection_ctrl)

    print("\n" + "=" * 100)
    print("📈 FINAL TRIAL RESULTS")
    print("=" * 100)

    print(f"\nSample sizes:")
    print(f"  Treatment: {treatment_total} patients, {treatment_healthy} healthy ({final_tx_rate:.1%} healthy)")
    print(f"  Control:   {control_total} patients, {control_healthy} healthy ({final_ctrl_rate:.1%} healthy)")

    print(f"\nInfection rates:")
    print(f"  Treatment: {final_infection_tx:.3f}")
    print(f"  Control:   {final_infection_ctrl:.3f}")

    print(f"\nVaccine Efficacy: {final_ve:.1%}")
    print(f"  (VE = 1 - treatment_infection / control_infection)")

    print(f"\n95% CI for difference in healthy rates:")
    print(f"  ({iv.lo:.3f}, {iv.hi:.3f})")

    if iv.lo > 0:
        print(f"\n  ✅ Conclusion: Vaccine is EFFECTIVE")
        print(f"     The difference is statistically significant.")
        print(f"     We're 95% confident treatment > control by at least {iv.lo:.3f}")
    else:
        print(f"\n  ⚠️  Conclusion: Cannot confirm efficacy yet")

    print(f"\n  Total patients: {iv.t}")
    print(f"  Guarantee tier: {iv.tier.value}")

    if efficacy_detected:
        print(f"\n  💡 Efficacy detected at patient #{efficacy_detected}")
        print(f"     Could stop early - save {len(participants) - efficacy_detected} patients!")
        print(f"     (Ethical benefit: offer effective treatment to control group)")

def demo_interim_analysis_design():
    """
    Demonstrate proper interim analysis design for clinical trials.
    """
    print("\n" + "=" * 80)
    print("📋 INTERIM ANALYSIS DESIGN: Group Sequential Principles")
    print("=" * 80)

    print("""
CLINICAL TRIAL MONITORING:

Why monitor trials sequentially?
  ✓ Stop early for efficacy → Offer effective treatment to control group
  ✓ Stop early for futility → Save resources, redirect patients
  ✓ Stop early for harm → Protect patients from unsafe treatments

TYPES OF EARLY STOPPING:

1. EFFICACY BOUNDARY
   - Stop if treatment is clearly better
   - Ethical: Offer effective treatment to everyone
   - Example: VE confidence interval excludes 0%

2. FUTILITY BOUNDARY
   - Stop if treatment is unlikely to show benefit
   - Efficient: Save resources for promising treatments
   - Example: Conditional power < 10%

3. SAFETY BOUNDARY
   - Stop if treatment shows harm
   - Ethical: Protect patients from adverse events
   - Example: Adverse event rate significantly higher in treatment

TRADITIONAL APPROACH vs ANYTIME-VALID:

Traditional (Group Sequential):
  • Requires pre-specified analysis schedule
  • Complex alpha-spending functions (O'Brien-Fleming, Pocock)
  • Fixed number of looks

Anytime-Valid:
  • Flexible monitoring at any time
  • Simple constant thresholds
  • No penalty for frequency of looks

EXAMPLE DESIGN:
    """)

    # Create a simple monitoring table
    print("""
    Trial Size: N = 2000 patients
    Interim Analyses: Every 200 patients (10 looks total)

    ┌────────────┬──────────────────┬─────────────────────┐
    │ Analysis   │ Efficacy Boundary│ Futility Boundary   │
    │ (N)        │ (Stop if VE CI   │ (Stop if conditional │
    │            │  excludes 0)     │  power < 10%)        │
    ├────────────┼──────────────────┼─────────────────────┤
    │ 200        │   VE > 70%       │   VE < 10%          │
    │ 400        │   VE > 50%       │   VE < 15%          │
    │ 600        │   VE > 40%       │   VE < 18%          │
    │ 800        │   VE > 35%       │   VE < 20%          │
    │ 1000       │   VE > 30%       │   VE < 22%          │
    │ ...        │   ...            │   ...               │
    │ 2000       │   VE > 25%       │   (final analysis)   │
    └────────────┴──────────────────┴─────────────────────┘

    With anytime-valid methods, you can check ANY time without penalty!
    """)

def demo_safety_monitoring():
    """
    Demonstrate adverse event monitoring.
    """
    print("\n" + "=" * 80)
    print("⚠️  SAFETY MONITORING: Adverse Event Tracking")
    print("=" * 80)

    print("""
SCENARIO:
  Monitoring for adverse events (AEs) in a clinical trial.

  Common adverse events:
    - Fever, fatigue, headache (mild)
    - Allergic reactions (moderate)
    - Organ damage, anaphylaxis (severe)

  Safety monitoring goals:
    ✓ Detect elevated AE rates in treatment group
    ✓ Stop trial if safety concerns emerge
    ✓ Maintain statistical validity with repeated checks

EXAMPLE: Monitoring severe AEs
    """)

    # Setup for monitoring adverse events
    spec = ABSpec(
        alpha=0.05,
        support=(0.0, 1.0),
        kind="bounded",
        two_sided=True,  # Two-sided: detect higher OR lower rates
        name="adverse_events"
    )

    cs = TwoSampleHoeffdingCS(spec)

    # Simulate adverse events
    random.seed(123)
    n_patients = 500

    treatment_ae_rate = 0.03  # 3% severe AEs in treatment
    control_ae_rate = 0.01    # 1% severe AEs in control

    treatment_aes = 0
    control_aes = 0
    treatment_n = 0
    control_n = 0

    print("\n" + "-" * 80)
    print(f"{'Patients':>10} | {'Tx AE Rate':>14} | {'Ctrl AE Rate':>14} | {'95% CI':>20} | {'Status':>15}")
    print("-" * 80)

    safety_concern_detected = None

    for i in range(n_patients):
        arm = 'A' if random.random() < 0.5 else 'B'  # A=Treatment, B=Control

        if arm == 'A':  # Treatment
            has_ae = 1 if random.random() < treatment_ae_rate else 0
            treatment_aes += has_ae
            treatment_n += 1
        else:  # Control
            has_ae = 1 if random.random() < control_ae_rate else 0
            control_aes += has_ae
            control_n += 1

        cs.update((arm, has_ae))

        # Check every 50 patients
        if (i + 1) % 50 == 0:
            iv = cs.interval()
            tx_rate = treatment_aes / treatment_n if treatment_n > 0 else 0
            ctrl_rate = control_aes / control_n if control_n > 0 else 0

            # Check if treatment AEs are significantly HARMFUL (higher)
            is_harmful = iv.lo > 0  # Treatment - Control > 0

            status = "⚠️  SAFETY ALERT" if is_harmful else "No concern"

            if is_harmful and safety_concern_detected is None:
                safety_concern_detected = i + 1

            print(f"{i+1:10d} | {tx_rate:14.3f} | {ctrl_rate:14.3f} | "
                  f"({iv.lo:.4f}, {iv.hi:.4f}) | {status:>15}")

    print("\n💡 With small AE rates, need larger sample to detect safety concerns")
    print("   This is why safety monitoring requires ongoing vigilance!")

def main():
    print("=" * 80)
    print("💉 Clinical Trial Analysis with Anytime-Valid Inference")
    print("=" * 80)

    print("""
This example demonstrates how anytime-valid inference can be used in
clinical trials for sequential monitoring, interim analysis, and early
stopping decisions.

DISCLAIMER: This is for educational purposes. Real clinical trials require:
  • Qualified biostatisticians
  • Regulatory approval (FDA, EMA, etc.)
  • Rigorous protocol design
  • Independent Data Monitoring Committees (DMCs)

EXAMPLES COVERED:
  1. Vaccine efficacy trial with sequential monitoring
  2. Interim analysis design principles
  3. Safety monitoring for adverse events

REAL-WORLD APPLICATIONS:
  • Phase I/II/III clinical trials
  • Vaccine efficacy studies
  • Medical device testing
  • Comparative effectiveness research
  • Pharmacovigilance and post-market surveillance

ETHICAL CONSIDERATIONS:
  • Early stopping for efficacy: Make effective treatments available sooner
  • Early stopping for futility: Save resources, redirect patients
  • Early stopping for harm: Protect patients from unsafe treatments

DATASETS IN PRODUCTION:
  • Electronic Health Records (EHR)
  • Clinical trial databases (REDCap, ClinicalTrials.gov)
  • Disease registries
  • Pharmacovigilance databases (FAERS, VigiBase)
    """)

    # Run demonstrations
    demo_vaccine_efficacy_trial()
    demo_interim_analysis_design()
    demo_safety_monitoring()

    # Final summary
    print("\n" + "=" * 80)
    print("✅ SUMMARY")
    print("=" * 80)

    print("""
WHAT YOU LEARNED:
  ✓ Sequential monitoring of clinical trial endpoints
  ✓ Vaccine efficacy calculation with confidence intervals
  ✓ Interim analysis design principles (efficacy, futility, safety)
  ✓ Adverse event monitoring patterns

KEY INSIGHTS:
  • Anytime-valid methods simplify interim analysis design
  • No complex alpha-spending functions needed
  • Flexible monitoring without statistical penalty
  • Early stopping has ethical implications

IMPORTANT NOTES:
  ⚠️  Real clinical trials require expert statisticians
  ⚠️  Regulatory guidelines must be followed (ICH E9, FDA guidance)
  ⚠️  Independent Data Monitoring Committees (DMCs) review interim results
  ⚠️  This example is simplified for educational purposes

REFERENCES FOR FURTHER READING:
  • ICH E9 Statistical Principles for Clinical Trials
  • FDA Adaptive Design Clinical Trial Guidance
  • "Group Sequential Methods" (Jennison & Turnbull)
  • "Confidence Sequences and Mean-Testing" (Waudby-Smith & Ramdas, 2023)

NEXT STEPS:
  • Example 12: Currency and financial monitoring
  • Example 13: Retail and e-commerce analytics
  • Example 15: Multi-armed bandit optimization

SOURCES:
  • [Top 10 Healthcare Data Sets and Sources](https://kms-technology.com/blog/healthcare-data-sets/)
  • [ClinicalTrials.gov](https://clinicaltrials.gov/)
  • [FDA Adaptive Design Guidance](https://www.fda.gov/media/78595/download)
    """)

if __name__ == "__main__":
    main()
