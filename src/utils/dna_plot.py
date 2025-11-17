# tools/dna_plot.py
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from scipy.stats import norm
import numpy as np
from matplotlib.patches import Patch


def generate_dna_plots(report, user_dir):
    """Generate comprehensive DNA analysis plots matching test.ipynb"""
    # Create high-quality figure with 5 subplots
    plt.style.use('default')
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

    # 1. Population Distribution
    ax1 = fig.add_subplot(gs[0, :2])
    z_score = report['pgs_results']['z_score']
    percentile = report['pgs_results']['percentile']
    x = np.linspace(-3, 3, 500)
    pop_pdf = norm.pdf(x, 0, 1)
    ax1.plot(x, pop_pdf, color="#2c3e50", lw=3,
             label="Population Distribution")
    ax1.axvline(z_score, color="#e74c3c", lw=2.5, ls="--",
                label=f"Your Score (z={z_score:+.2f})")
    ax1.fill_between(x, pop_pdf, where=(x <= z_score),
                     alpha=0.25, color="#e74c3c")
    ax1.set(title="Your Genetic Score vs Population",
            xlabel="Z-score", ylabel="Probability Density")
    ax1.legend(fontsize=10)
    ax1.grid(alpha=0.3)

    # 2. Percentile Bar
    ax2 = fig.add_subplot(gs[0, 2])
    pct = percentile
    color = "#27ae60" if pct > 60 else "#e74c3c" if pct < 40 else "#3498db"
    ax2.barh(["Your\nScore"], [pct], color=color,
             height=0.5, edgecolor='black', linewidth=1.5)
    ax2.set_xlim(0, 100)
    ax2.axvline(50, color='gray', ls='--', alpha=0.5, lw=2)
    ax2.set_title(f"Percentile Rank", fontweight='bold')
    ax2.set_xlabel("Percentile")
    for i in [25, 50, 75]:
        ax2.axvline(i, color='gray', ls=':', alpha=0.3)
    ax2.text(pct + 3, 0, f"{pct:.1f}%", va='center',
             fontsize=13, fontweight='bold')

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
    colors_map = {'Strong': '#27ae60',
                  'Moderate': '#f39c12', 'Weak': '#95a5a6'}
    bar_colors = [colors_map.get(e, '#95a5a6') for e in df_bar['Evidence']]

    bars = ax3.barh(df_bar['SNP'], df_bar['Contribution'],
                    color=bar_colors, edgecolor='black', linewidth=0.8)
    ax3.axvline(0, color='black', lw=1)
    ax3.set_title("Individual SNP Contributions to Your PGS",
                  fontweight='bold', fontsize=12)
    ax3.set_xlabel("Weighted Contribution (Beta × Dosage)")
    ax3.grid(axis='x', alpha=0.3)

    # Legend for evidence strength
    legend_elements = [Patch(facecolor='#27ae60', label='Strong Evidence'),
                       Patch(facecolor='#f39c12', label='Moderate Evidence'),
                       Patch(facecolor='#95a5a6', label='Weak Evidence')]
    ax3.legend(handles=legend_elements, loc='lower right', fontsize=9)

    # 4. Evidence Strength Pie
    ax4 = fig.add_subplot(gs[2, 0])
    evidence_dist = report.get('evidence_distribution', {})
    if evidence_dist:
        labels = list(evidence_dist.keys())
        values = list(evidence_dist.values())
        colors_pie = [colors_map.get(e, '#95a5a6') for e in labels]
        ax4.pie(values, labels=labels, autopct='%1.0f%%',
                colors=colors_pie, startangle=90,
                textprops={'fontsize': 10, 'fontweight': 'bold'})
        ax4.set_title("Evidence Quality Distribution", fontweight='bold')

    # 5. Phenotype Categories
    ax5 = fig.add_subplot(gs[2, 1:])
    category_scores = report.get('category_scores', {})
    if category_scores:
        cats = list(category_scores.keys())
        scores = list(category_scores.values())
        colors_cat = ['#3498db', '#9b59b6', '#e67e22', '#1abc9c', '#e74c3c']
        bars_cat = ax5.barh(cats, scores, color=colors_cat[:len(cats)],
                            edgecolor='black', linewidth=1)
        ax5.axvline(0, color='black', lw=1)
        ax5.set_title("Contributions by Cognitive Domain", fontweight='bold')
        ax5.set_xlabel("Cumulative Contribution")
        ax5.grid(axis='x', alpha=0.3)

    try:
        plt.tight_layout()
    except UserWarning:
        pass  # Ignore tight_layout warnings

    path = f"{user_dir}/dna_report.png"

    # Save with maximum quality settings for PDF embedding
    plt.savefig(
        path,
        dpi=300,  # High DPI for crisp display
        bbox_inches='tight',
        facecolor='white',
        edgecolor='none',
        format='png',
        transparent=False,
        pad_inches=0.2,
        metadata={'Title': 'DNA Analysis Report', 'Creator': 'GeneLingua v7'}
    )
    plt.close()

    # Verify the file was created correctly
    import os
    if os.path.exists(path):
        file_size = os.path.getsize(path) / (1024 * 1024)  # Size in MB
        print(f"DNA plot saved successfully: {path} ({file_size:.1f} MB)")
        return path
    else:
        print(f"Failed to save DNA plot: {path}")
        return None
