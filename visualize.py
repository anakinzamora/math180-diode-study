import matplotlib
matplotlib.use('Agg')

"""Visualization module for the MATH180 diode leakage current study."""

import os
import subprocess
import sys

import pandas as pd

try:
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'matplotlib', '-q'])
    import matplotlib.pyplot as plt
    import numpy as np

DOPING_ORDER = ['Low', 'Medium', 'High']
TEMP_ORDER = ['27C', '50C', '75C']
TEMP_COLORS = ['#4682b4', '#ff7f50', '#3cb371']


def main():
    base_dir = os.path.dirname(__file__)
    output_dir = os.path.join(base_dir, 'outputs')
    results_path = os.path.join(output_dir, 'results.csv')

    df = pd.read_csv(results_path)
    df['doping_label'] = pd.Categorical(df['doping_label'], categories=DOPING_ORDER, ordered=True)
    df['temp_label'] = pd.Categorical(df['temp_label'], categories=TEMP_ORDER, ordered=True)

    summary = (
        df.groupby(['doping_label', 'temp_label'], observed=True)['leakage_nA']
        .agg(['mean', 'std', 'count'])
        .reset_index()
    )
    summary.columns = ['Doping Level', 'Temperature', 'Mean Leakage (nA)', 'Std Dev (nA)', 'N']
    summary_path = os.path.join(output_dir, 'summary_table.csv')
    summary.to_csv(summary_path, index=False)

    plt.style.use('seaborn-v0_8-whitegrid')

    fig1, ax1 = plt.subplots(figsize=(10, 6), dpi=300)
    x = np.arange(len(DOPING_ORDER))
    bar_width = 0.25

    for i, temp in enumerate(TEMP_ORDER):
        temp_data = summary[summary['Temperature'] == temp]
        means = [temp_data[temp_data['Doping Level'] == d]['Mean Leakage (nA)'].values[0]
                 for d in DOPING_ORDER]
        stds = [temp_data[temp_data['Doping Level'] == d]['Std Dev (nA)'].values[0]
                for d in DOPING_ORDER]
        offset = (i - 1) * bar_width
        ax1.bar(
            x + offset, means, bar_width,
            yerr=stds, capsize=4,
            label=temp, color=TEMP_COLORS[i],
            edgecolor='black', linewidth=0.5,
        )

    ax1.set_xticks(x)
    ax1.set_xticklabels(DOPING_ORDER)
    ax1.set_title('Mean Leakage Current by Doping Concentration and Temperature')
    ax1.set_xlabel('Doping Concentration Level')
    ax1.set_ylabel('Mean Leakage Current (nA)')
    ax1.legend(title='Junction Temperature')
    fig1.tight_layout()
    fig1.savefig(os.path.join(output_dir, 'bar_chart.png'))
    plt.close(fig1)

    fig2, ax2 = plt.subplots(figsize=(10, 6), dpi=300)

    for doping in DOPING_ORDER:
        doping_data = summary[summary['Doping Level'] == doping]
        means = [doping_data[doping_data['Temperature'] == t]['Mean Leakage (nA)'].values[0]
                 for t in TEMP_ORDER]
        ax2.plot(TEMP_ORDER, means, marker='o', linewidth=2, label=doping)

    ax2.set_title('Interaction Plot: Doping Concentration × Junction Temperature')
    ax2.set_xlabel('Junction Temperature')
    ax2.set_ylabel('Mean Leakage Current (nA)')
    ax2.legend(title='Doping Concentration')
    fig2.tight_layout()
    fig2.savefig(os.path.join(output_dir, 'interaction_plot.png'))
    plt.close(fig2)

    print("Charts saved: outputs/bar_chart.png and outputs/interaction_plot.png")


if __name__ == '__main__':
    main()
