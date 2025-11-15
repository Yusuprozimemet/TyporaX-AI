# tools/dna_plot.py
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from scipy.stats import norm
import numpy as np


def generate_dna_plots(report, user_dir):
    # Create high-quality figure with better settings
    plt.style.use('default')  # Ensure clean style
    fig = plt.figure(figsize=(20, 12))  # Larger figure for better quality
    gs = fig.add_gridspec(3, 3, hspace=0.4, wspace=0.4)

    # 1. Population Distribution
    ax1 = fig.add_subplot(gs[0, :2])
    z = report['pgs_results']['z_score']
    x = np.linspace(-3, 3, 500)
    pop_pdf = norm.pdf(x, 0, 1)
    ax1.plot(x, pop_pdf, color="#2c3e50", lw=3)
    ax1.axvline(z, color="#e74c3c", lw=2.5, ls="--")
    ax1.fill_between(x, pop_pdf, where=(x <= z), alpha=0.25, color="#e74c3c")
    ax1.set(title="Your Genetic Score vs Population",
            xlabel="Z-score", ylabel="Density")
    ax1.grid(alpha=0.3)

    # 2. Percentile Bar
    ax2 = fig.add_subplot(gs[0, 2])
    pct = report['pgs_results']['percentile']
    color = "#27ae60" if pct > 60 else "#e74c3c" if pct < 40 else "#3498db"
    ax2.barh(["Score"], [pct], color=color, height=0.5)
    ax2.set_xlim(0, 100)
    ax2.axvline(50, color='gray', ls='--')
    ax2.set_title("Percentile")
    ax2.text(pct + 3, 0, f"{pct:.1f}%", va='center', fontweight='bold')

    # 3. SNP Contributions
    ax3 = fig.add_subplot(gs[1, :])
    contrib_data = []
    for rsid, c in report['snp_contributions'].items():
        if c['contrib'] is not None:
            contrib_data.append({
                'SNP': f"{rsid}\n({c['gene']})",
                'Contribution': c['contrib'],
                'Evidence': c['evidence']
            })
    df_bar = pd.DataFrame(contrib_data).sort_values('Contribution')
    colors = {'Strong': '#27ae60', 'Moderate': '#f39c12', 'Weak': '#95a5a6'}
    bar_colors = [colors.get(e, '#95a5a6') for e in df_bar['Evidence']]
    ax3.barh(df_bar['SNP'], df_bar['Contribution'], color=bar_colors)
    ax3.axvline(0, color='black', lw=1)
    ax3.set_title("SNP Contributions")
    ax3.grid(axis='x', alpha=0.3)

    # 4. Scenario Table (as plot)
    ax4 = fig.add_subplot(gs[2, :])
    ax4.axis('off')
    df_scen = pd.DataFrame(report['scenarios'])
    table = ax4.table(cellText=df_scen.values,
                      colLabels=df_scen.columns, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.8)
    ax4.set_title("Time to B2 Scenarios", fontweight='bold', pad=20)

    try:
        plt.tight_layout()
    except UserWarning:
        pass  # Ignore tight_layout warnings
    path = f"{user_dir}/dna_report.png"

    # Save with maximum quality settings for PDF embedding
    plt.savefig(
        path,
        dpi=600,  # Very high DPI for crisp PDF embedding
        bbox_inches='tight',
        facecolor='white',
        edgecolor='none',
        format='png',
        transparent=False,
        pad_inches=0.2,  # Small padding
        metadata={'Title': 'DNA Analysis Report', 'Creator': 'GeneLingua v7'}
    )
    plt.close()

    # Verify the file was created correctly and check size
    import os
    if os.path.exists(path):
        file_size = os.path.getsize(path) / (1024 * 1024)  # Size in MB
        print(f"DNA plot saved successfully: {path} ({file_size:.1f} MB)")
        return path
    else:
        print(f"Failed to save DNA plot: {path}")
        return None
