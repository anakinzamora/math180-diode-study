"""
MATH180 Engineering Data Analysis — Diode Leakage Current Study
=================================================================

Research Title:
    Effect of Doping Concentration and Junction Temperature on Leakage Current
    in a Simulated Semiconductor Diode: A Two-Factor Factorial Design Approach

Factors:
    Factor A — Doping Concentration:
        Low    : 1×10¹⁵ cm⁻³
        Medium : 1×10¹⁷ cm⁻³
        High   : 1×10¹⁹ cm⁻³

    Factor B — Junction Temperature:
        27°C (300 K)
        50°C (323 K)
        75°C (348 K)

Dependent Variable:
    Leakage current I₀ (reverse saturation current) in nanoamperes (nA)

Core Physics Equation:
    I₀ = A · T² · e^(−Eg / kT)

    where:
        A  = scaling constant proportional to doping concentration
        T  = absolute temperature in Kelvin
        Eg = 1.12 eV  (silicon bandgap energy)
        k  = 8.617×10⁻⁵ eV/K  (Boltzmann constant)

Study Design:
    3×3 two-factor factorial design
    5 replicates per cell
    45 trials total

Statistical Test:
    Two-way ANOVA at α = 0.05
"""

import numpy
import pandas
import scipy
import itertools
import random
import os

Eg = 1.12       # silicon bandgap energy (eV)
k = 8.617e-5    # Boltzmann constant (eV/K)
ni_300 = 1.5e10  # intrinsic carrier concentration at 300K (cm⁻³)

doping_levels = {
    'Low':    1e15,   # cm⁻³
    'Medium': 1e17,   # cm⁻³
    'High':   1e19,   # cm⁻³
}

A_base = {
    1e15: 1e-12,   # Low   — picoamperes range
    1e17: 1e-10,   # Medium
    1e19: 1e-8,    # High
}

temperature_levels = {
    '27C': 300,   # Kelvin
    '50C': 323,   # Kelvin
    '75C': 348,   # Kelvin
}


def compute_leakage(doping, temp_K, seed):
    A = A_base[doping]
    temp_factor = (temp_K / 300) ** 2 * numpy.exp(-Eg / (k * temp_K) + Eg / (k * 300))
    I0_nA = A * temp_factor * 1e9
    numpy.random.seed(seed)
    noise = numpy.random.normal(0, 0.05 * I0_nA)
    return max(0.001, I0_nA + noise)


def run_experiment():
    results = []
    seeds = [0, 1, 2, 3, 4]

    for (doping_label, doping_value), (temp_label, temp_K_value) in itertools.product(
        doping_levels.items(), temperature_levels.items()
    ):
        for seed in seeds:
            leakage_nA = compute_leakage(doping_value, temp_K_value, seed)
            results.append({
                'doping_label': doping_label,
                'doping_value': doping_value,
                'temp_label': temp_label,
                'temp_K': temp_K_value,
                'replicate': seed + 1,
                'leakage_nA': leakage_nA,
            })

    df = pandas.DataFrame(results)

    output_dir = os.path.join(os.path.dirname(__file__), 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'results.csv')
    df.to_csv(output_path, index=False)

    summary = df.groupby(['doping_label', 'temp_label'])['leakage_nA'].agg(['mean', 'std'])
    print(summary)
    print("45 trials complete. Saved to outputs/results.csv")


if __name__ == "__main__":
    run_experiment()
