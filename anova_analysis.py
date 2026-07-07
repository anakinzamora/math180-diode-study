"""Two-way ANOVA analysis for the MATH180 diode leakage current study."""

import os
import subprocess
import sys

import pandas as pd

try:
    import statsmodels.formula.api as smf
    import statsmodels.stats.anova as anova_lm
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'statsmodels', '-q'])
    import statsmodels.formula.api as smf
    import statsmodels.stats.anova as anova_lm

SOURCE_LABELS = {
    'C(doping_label)': 'doping_label',
    'C(temp_label)': 'temp_label',
    'C(doping_label):C(temp_label)': 'interaction',
    'Residual': 'Residual',
}


def main():
    base_dir = os.path.dirname(__file__)
    results_path = os.path.join(base_dir, 'outputs', 'results.csv')
    output_path = os.path.join(base_dir, 'outputs', 'anova_table.csv')

    df = pd.read_csv(results_path)
    df['doping_label'] = df['doping_label'].astype('category')
    df['temp_label'] = df['temp_label'].astype('category')

    model = smf.ols('leakage_nA ~ C(doping_label) * C(temp_label)', data=df).fit()
    anova_table = anova_lm.anova_lm(model, typ=2)

    anova_display = anova_table.rename(columns={
        'sum_sq': 'SS',
        'df': 'df',
        'F': 'F-statistic',
        'PR(>F)': 'PR(>F)',
    })

    print("=== TWO-WAY ANOVA RESULTS ===")
    print(anova_display.to_string())

    print("\n=== SIGNIFICANCE DECISIONS (α = 0.05) ===")
    for source, row in anova_table.iterrows():
        label = SOURCE_LABELS.get(source, source)
        p_value = row['PR(>F)']
        if label == 'Residual' or pd.isna(p_value):
            continue
        if p_value < 0.05:
            decision = "SIGNIFICANT — Reject H₀"
        else:
            decision = "NOT SIGNIFICANT — Fail to reject H₀"
        print(f"{label}: p = {p_value:.6f} → {decision}")

    print("\n=== GROUP MEANS (leakage_nA) ===")
    group_means = df.groupby(['doping_label', 'temp_label'], observed=True)['leakage_nA'].mean()
    print(group_means.to_string())

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    anova_table.to_csv(output_path)
    print("\nANOVA complete. Saved to outputs/anova_table.csv")


if __name__ == '__main__':
    main()
