import matplotlib
matplotlib.use('Agg')

"""Flask web dashboard for the MATH180 diode leakage current study."""

import os
import subprocess
import sys
import itertools

import numpy
import pandas as pd

if not getattr(sys, 'frozen', False):
    try:
        from flask import Flask, render_template, jsonify, send_file, request
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'flask', '-q'])
        from flask import Flask, render_template, jsonify, send_file, request

    try:
        import statsmodels.formula.api as smf
        import statsmodels.stats.anova as anova_lm
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'statsmodels', '-q'])
        import statsmodels.formula.api as smf
        import statsmodels.stats.anova as anova_lm
else:
    from flask import Flask, render_template, jsonify, send_file, request
    import statsmodels.formula.api as smf
    import statsmodels.stats.anova as anova_lm


def resource_path(relative):
    """Read-only bundled assets (templates, static)."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    return os.path.join(base, relative)


def get_output_dir():
    """Writable output folder next to the executable or project root."""
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        if exe_dir.endswith('.app/Contents/MacOS'):
            exe_dir = os.path.abspath(os.path.join(exe_dir, '..', '..', '..'))
        return os.path.join(exe_dir, 'outputs')
    return os.path.join(os.path.dirname(__file__), 'outputs')


OUTPUT_DIR = get_output_dir()

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

SOURCE_LABELS = {
    'C(doping_label)': 'doping_label',
    'C(temp_label)': 'temp_label',
    'C(doping_label):C(temp_label)': 'interaction',
    'Residual': 'Residual',
}

app = Flask(
    __name__,
    template_folder=resource_path('templates'),
    static_folder=resource_path('static'),
)


def compute_leakage(doping, temp_K, seed):
    A = A_base[doping]
    temp_factor = (temp_K / 300) ** 2 * numpy.exp(-Eg / (k * temp_K) + Eg / (k * 300))
    I0_nA = A * temp_factor * 1e9
    numpy.random.seed(seed)
    noise = numpy.random.normal(0, 0.05 * I0_nA)
    return max(0.001, I0_nA + noise)


def run_factorial_simulation(n_seeds=5):
    results = []
    seeds = list(range(n_seeds))

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
                'leakage_nA': float(leakage_nA),
            })

    return pd.DataFrame(results)


def run_anova(df):
    df = df.copy()
    df['doping_label'] = df['doping_label'].astype('category')
    df['temp_label'] = df['temp_label'].astype('category')

    model = smf.ols('leakage_nA ~ C(doping_label) * C(temp_label)', data=df).fit()
    anova_table = anova_lm.anova_lm(model, typ=2)

    anova_rows = []
    for source, row in anova_table.iterrows():
        p_value = row['PR(>F)']
        anova_rows.append({
            'source': SOURCE_LABELS.get(source, source),
            'ss': float(row['sum_sq']),
            'df': float(row['df']),
            'f_stat': None if pd.isna(row['F']) else float(row['F']),
            'p_value': None if pd.isna(p_value) else float(p_value),
            'significant': bool(p_value < 0.05) if pd.notna(p_value) else False,
        })

    return anova_table, anova_rows


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/run-simulation', methods=['POST'])
def run_simulation():
    payload = request.get_json(silent=True) or {}
    n_seeds = payload.get('n_seeds', 5)

    df = run_factorial_simulation(n_seeds=n_seeds)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results_path = os.path.join(OUTPUT_DIR, 'results.csv')
    df.to_csv(results_path, index=False)

    anova_table, anova_rows = run_anova(df)
    anova_path = os.path.join(OUTPUT_DIR, 'anova_table.csv')
    anova_table.to_csv(anova_path)

    trial_results = df[['doping_label', 'temp_label', 'replicate', 'leakage_nA']].to_dict(orient='records')

    group_means_df = (
        df.groupby(['doping_label', 'temp_label'], observed=True)['leakage_nA']
        .mean()
        .reset_index()
        .rename(columns={'leakage_nA': 'mean_leakage_nA'})
    )
    group_means = group_means_df.to_dict(orient='records')

    best_row = group_means_df.loc[group_means_df['mean_leakage_nA'].idxmax()]
    best_combination = {
        'doping_label': best_row['doping_label'],
        'temp_label': best_row['temp_label'],
    }

    response = {
        'results': trial_results,
        'group_means': group_means,
        'anova_table': anova_rows,
        'summary': {
            'best_combination': best_combination,
            'best_accuracy': float(best_row['mean_leakage_nA']),
            'overall_mean': float(df['leakage_nA'].mean()),
            'total_trials': len(df),
        },
    }

    return jsonify(response)


@app.route('/download-results')
def download_results():
    results_path = os.path.join(OUTPUT_DIR, 'results.csv')
    if not os.path.exists(results_path):
        return jsonify({'error': 'results.csv not found. Run simulation first.'}), 404
    return send_file(results_path, as_attachment=True, download_name='results.csv')


@app.route('/download-anova')
def download_anova():
    anova_path = os.path.join(OUTPUT_DIR, 'anova_table.csv')
    if not os.path.exists(anova_path):
        return jsonify({'error': 'anova_table.csv not found. Run simulation first.'}), 404
    return send_file(anova_path, as_attachment=True, download_name='anova_table.csv')


if __name__ == "__main__":
    app.run(debug=False)
