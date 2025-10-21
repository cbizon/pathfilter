"""Plot path count vs ROBOKOP degree, colored by expected status."""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import argparse


def plot_degree_vs_pathcount(input_file: str, output_file: str):
    """
    Create scatter plots of path count vs node degree, colored by expected status.

    Args:
        input_file: Path to node_path_counts_with_degrees.tsv
        output_file: Path to save plot
    """
    # Load data
    df = pd.read_csv(input_file, sep='\t')

    # Get unique queries
    queries = sorted(df['Query'].unique())

    # Determine grid layout
    n_queries = len(queries)
    n_cols = 4
    n_rows = int(np.ceil(n_queries / n_cols))

    # Create figure
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, 5*n_rows))
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    axes = axes.flatten()

    # Plot each query
    for idx, query in enumerate(queries):
        ax = axes[idx]
        query_data = df[df['Query'] == query]

        # Split by expected status
        expected = query_data[query_data['Is_Expected'] == True]
        not_expected = query_data[query_data['Is_Expected'] == False]

        # Plot not expected (background)
        if len(not_expected) > 0:
            ax.scatter(
                not_expected['Node_degree'],
                not_expected['Path_Count'],
                alpha=0.4,
                s=20,
                c='gray',
                label=f'Not expected (n={len(not_expected)})',
                edgecolors='none'
            )

        # Plot expected (foreground)
        if len(expected) > 0:
            ax.scatter(
                expected['Node_degree'],
                expected['Path_Count'],
                alpha=0.8,
                s=50,
                c='red',
                label=f'Expected (n={len(expected)})',
                edgecolors='black',
                linewidths=0.5
            )

        # Log scale for both axes (many nodes have degree 0, handle this)
        # Filter out zeros for log scale
        non_zero_degrees = query_data[query_data['Node_degree'] > 0]['Node_degree']
        non_zero_paths = query_data[query_data['Path_Count'] > 0]['Path_Count']

        if len(non_zero_degrees) > 0:
            ax.set_xscale('log')
        if len(non_zero_paths) > 0:
            ax.set_yscale('log')

        ax.set_xlabel('Node Degree (ROBOKOP)', fontsize=9)
        ax.set_ylabel('Path Count', fontsize=9)
        ax.set_title(query, fontsize=10, fontweight='bold')
        ax.legend(fontsize=7, loc='upper left')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.tick_params(labelsize=8)

    # Hide unused subplots
    for idx in range(n_queries, len(axes)):
        axes[idx].set_visible(False)

    plt.suptitle(
        'Path Count vs ROBOKOP Node Degree by Query\n(Expected nodes in red)',
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
        description='Plot path count vs ROBOKOP degree by query'
    )
    parser.add_argument(
        '--input',
        default='node_path_counts_with_degrees.tsv',
        help='Input TSV file with node path counts and degrees'
    )
    parser.add_argument(
        '--output',
        default='degree_vs_pathcount.png',
        help='Output plot file'
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    plot_degree_vs_pathcount(args.input, args.output)
    return 0


if __name__ == '__main__':
    exit(main())
