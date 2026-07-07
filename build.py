"""Build standalone executable with PyInstaller."""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SEP = ';' if sys.platform == 'win32' else ':'

cmd = [
    sys.executable, '-m', 'PyInstaller',
    '--noconfirm',
    '--clean',
    'launch.py',
    '--onefile',
    '--windowed',
    '--name', 'Diode Leakage Study',
    f'--add-data=templates{SEP}templates',
    f'--add-data=static{SEP}static',
    f'--add-data=outputs{SEP}outputs',
    '--hidden-import=statsmodels.formula.api',
    '--hidden-import=statsmodels.stats.anova',
    '--collect-submodules=statsmodels',
    '--collect-submodules=scipy',
    '--hidden-import=scipy._external.array_api_compat.numpy.fft',
    '--hidden-import=flask',
    '--hidden-import=pandas',
    '--hidden-import=numpy',
    '--hidden-import=scipy',
    '--collect-all=scipy',
]

subprocess.run(cmd, cwd=ROOT, check=True)
print('Build complete. Executable is in dist/ folder.')
