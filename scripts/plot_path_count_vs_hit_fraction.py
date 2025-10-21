#!/usr/bin/env python3
"""
Plot Path_Count vs Hit_Path_Fraction for each query, colored by Is_Expected.

This visualization helps identify whether nodes appearing in more paths
have higher hit path fractions, and whether expected nodes follow different
patterns than other nodes.
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def plot_path_count_vs_hit_fraction(input_file: str, output_file: str):
    """
    Create scatter plots comparing Path_Count to Hit_Path_Fraction.

    Args:
        input_file: Path to node_path_counts.tsv
        output_file: Path to output PNG file
    """
    # Read data
    df = pd.read_csv(input_file, sep='\t')

    # Get unique queries
    queries = sorted(df['Query'].unique())
    n_queries = len(queries)

    # Calculate grid dimensions
    n_cols = 4
    n_rows = int(np.ceil(n_queries / n_cols))

    # Create figure
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, 5 * n_rows))
    if n_queries == 1:
        axes = np.array([axes])
    axes = axes.flatten()

    # Color scheme
    colors = {
        True: '#d62728',   # Red for expected nodes
        False: '#1f77b4'   # Blue for other nodes
    }

    # Plot each query
    for idx, query in enumerate(queries):
        ax = axes[idx]
        query_data = df[df['Query'] == query]

        # Separate expected and other nodes
        for is_expected, color in colors.items():
            mask = query_data['Is_Expected'] == is_expected
            subset = query_data[mask]

            label = 'Expected' if is_expected else 'Other'
            ax.scatter(
                subset['Path_Count'],
                subset['Hit_Path_Fraction'],
                c=color,
                label=label,
                alpha=0.6,
                s=30
            )

        # Formatting
        ax.set_xlabel('Path Count', fontsize=10)
        ax.set_ylabel('Hit Path Fraction', fontsize=10)
        ax.set_title(f'{query}', fontsize=11, fontweight='bold')
        ax.legend(fontsize=8, loc='best')
        ax.grid(True, alpha=0.3)

        # Use log scale for x-axis if path counts vary widely
        if query_data['Path_Count'].max() > 100:
            ax.set_xscale('log')

    # Hide unused subplots
    for idx in range(n_queries, len(axes)):
        axes[idx].axis('off')

    # Overall title
    fig.suptitle(
        'Path Count vs Hit Path Fraction by Query\n(Expected nodes in red, Other nodes in blue)',
        fontsize=14,
        fontweight='bold',
        y=0.995
    )

    plt.tight_layout()

    # Save output
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved plot to: {output_file}")

    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="Plot Path_Count vs Hit_Path_Fraction for each query"
    )
    parser.add_argument(
        '--input',
        default='node_path_counts.tsv',
        help='Path to node_path_counts.tsv (default: node_path_counts.tsv)'
    )
    parser.add_argument(
        '--output',
        default='path_count_vs_hit_fraction.png',
        help='Path to output PNG file (default: path_count_vs_hit_fraction.png)'
    )

    args = parser.parse_args()

    plot_path_count_vs_hit_fraction(args.input, args.output)


if __name__ == '__main__':
    main()
