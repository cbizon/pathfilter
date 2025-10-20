#!/usr/bin/env python3
"""Create scatter plot of metapath frequency vs enrichment."""
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser(
        description='Create scatter plot of metapath frequency vs enrichment'
    )
    parser.add_argument(
        '--input',
        default='metapath_enrichment.tsv',
        help='Input TSV file (default: metapath_enrichment.tsv)'
    )
    parser.add_argument(
        '--output',
        default='metapath_frequency_vs_enrichment.png',
        help='Output PNG file (default: metapath_frequency_vs_enrichment.png)'
    )
    parser.add_argument(
        '--min-frequency',
        type=float,
        default=0.0,
        help='Minimum frequency to plot (default: 0.0)'
    )

    args = parser.parse_args()

    # Read data
    print(f"Reading {args.input}...")
    df = pd.read_csv(args.input, sep='\t')
    print(f"Loaded {len(df)} metapath entries")

    # Filter data
    df_filtered = df.copy()

    # Filter out zero enrichment and zero frequency for log scale
    df_filtered = df_filtered[
        (df_filtered['frequency'] > 0) & (df_filtered['enrichment'] > 0)
    ]
    print(f"Filtered to {len(df_filtered)} entries with frequency > 0 and enrichment > 0")

    if args.min_frequency > 0:
        df_filtered = df_filtered[df_filtered['frequency'] >= args.min_frequency]
        print(f"Further filtered to {len(df_filtered)} entries with frequency >= {args.min_frequency}")

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 10))

    # Get unique queries
    queries = sorted(df_filtered['query_id'].unique())

    # Create color map
    colors = plt.cm.tab20(np.linspace(0, 1, len(queries)))

    # Plot each query
    for idx, query_id in enumerate(queries):
        query_data = df_filtered[df_filtered['query_id'] == query_id]

        ax.scatter(
            query_data['frequency'],
            query_data['enrichment'],
            label=query_id,
            alpha=0.6,
            s=30,
            color=colors[idx],
            edgecolors='none'
        )

    # Add reference line at enrichment = 1.0
    ax.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, linewidth=1,
               label='No enrichment (baseline)')

    # Labels and formatting
    ax.set_xlabel('Frequency (log scale)', fontsize=12)
    ax.set_ylabel('Enrichment (log scale)', fontsize=12)
    ax.set_title('Metapath Frequency vs Enrichment\n' +
                 'Higher enrichment = better at finding expected nodes',
                 fontsize=14, fontweight='bold')

    # Use log-log scale
    ax.set_xscale('log')
    ax.set_yscale('log')

    # Grid
    ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    ax.set_axisbelow(True)

    # Legend
    ax.legend(
        bbox_to_anchor=(1.05, 1),
        loc='upper left',
        fontsize=8,
        ncol=1,
        framealpha=0.9
    )

    # Tight layout
    plt.tight_layout()

    # Save PNG only
    plt.savefig(args.output, dpi=300, bbox_inches='tight')
    print(f"Saved scatter plot to {args.output}")

    # Print statistics
    print("\nStatistics:")
    print(f"Total metapaths plotted: {len(df_filtered)}")
    print(f"Queries: {len(queries)}")
    print(f"Enrichment range: {df_filtered['enrichment'].min():.2f} - {df_filtered['enrichment'].max():.2f}")
    print(f"Frequency range: {df_filtered['frequency'].min():.4f} - {df_filtered['frequency'].max():.4f}")
    print(f"Metapaths with enrichment > 1.0: {(df_filtered['enrichment'] > 1.0).sum()}")


if __name__ == '__main__':
    main()
