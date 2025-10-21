"""Plot node degree vs information content for ROBOKOP nodes."""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import argparse


def plot_degree_vs_info_content(input_file: str, output_file: str):
    """
    Create scatter plot of node degree vs information content.

    Args:
        input_file: Path to TSV file with node degrees and information content
        output_file: Path to save plot
    """
    # Load data
    print(f"Loading data from {input_file}...")
    df = pd.read_csv(input_file, sep='\t')

    # Filter to nodes with information content
    df_with_ic = df[df['Information_content'].notna() & (df['Information_content'] != '')]
    df_with_ic = df_with_ic.copy()
    df_with_ic['Information_content'] = pd.to_numeric(df_with_ic['Information_content'], errors='coerce')
    df_with_ic = df_with_ic.dropna(subset=['Information_content'])

    print(f"Total nodes: {len(df):,}")
    print(f"Nodes with information content: {len(df_with_ic):,} ({len(df_with_ic)/len(df)*100:.1f}%)")
    print(f"Information content range: {df_with_ic['Information_content'].min():.1f} - {df_with_ic['Information_content'].max():.1f}")
    print(f"Degree range: {df_with_ic['Node_degree'].min()} - {df_with_ic['Node_degree'].max()}")

    # Calculate log(degree) / information_content for nodes with degree >= 1
    df_deg_gte1 = df_with_ic[df_with_ic['Node_degree'] >= 1].copy()
    df_deg_gte1['log_degree_over_IC'] = np.log10(df_deg_gte1['Node_degree']) / df_deg_gte1['Information_content']

    print(f"Nodes with degree >= 1: {len(df_deg_gte1):,}")
    print(f"log(degree) / IC range: {df_deg_gte1['log_degree_over_IC'].min():.2f} - {df_deg_gte1['log_degree_over_IC'].max():.2f}")

    # Create figure with 2 subplots
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # 1. Scatter plot: Degree vs Information Content
    ax = axes[0]
    ax.scatter(
        df_with_ic['Node_degree'],
        df_with_ic['Information_content'],
        alpha=0.3,
        s=1,
        c='steelblue',
        edgecolors='none'
    )
    ax.set_xscale('log')
    ax.set_xlabel('Node Degree (log scale)', fontsize=12)
    ax.set_ylabel('Information Content', fontsize=12)
    ax.set_title('Node Degree vs Information Content', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')

    # 2. Distribution of log(degree) / IC
    ax = axes[1]
    # Filter out inf and nan values
    ratio_clean = df_deg_gte1['log_degree_over_IC'].replace([np.inf, -np.inf], np.nan).dropna()

    ax.hist(ratio_clean, bins=100, color='steelblue', alpha=0.7, edgecolor='black')
    ax.set_xlabel('log₁₀(degree) / Information Content', fontsize=12)
    ax.set_ylabel('Count (log scale)', fontsize=12)
    ax.set_yscale('log')
    ax.set_title('Distribution of log₁₀(degree) / IC', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    # Add statistics
    mean_ratio = ratio_clean.mean()
    median_ratio = ratio_clean.median()
    ax.axvline(mean_ratio, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_ratio:.3f}')
    ax.axvline(median_ratio, color='orange', linestyle='--', linewidth=2, label=f'Median: {median_ratio:.3f}')
    ax.legend(fontsize=10)

    plt.suptitle(
        f'ROBOKOP Node Degree vs Information Content\n{len(df_with_ic):,} nodes with information content',
        fontsize=14,
        fontweight='bold',
        y=0.995
    )
    plt.tight_layout()

    # Save
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Saved plot to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Plot node degree vs information content'
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Input TSV file with node degrees and information content'
    )
    parser.add_argument(
        '--output',
        default='degree_vs_info_content.png',
        help='Output plot file'
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    plot_degree_vs_info_content(args.input, args.output)
    return 0


if __name__ == '__main__':
    exit(main())
