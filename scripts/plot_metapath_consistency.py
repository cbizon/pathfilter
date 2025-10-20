#!/usr/bin/env python3
"""Plot metapath minimum enrichment vs number of queries."""
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser(
        description='Plot metapath minimum enrichment vs number of queries'
    )
    parser.add_argument(
        '--input',
        default='metapath_aggregated.tsv',
        help='Input TSV file (default: metapath_aggregated.tsv)'
    )
    parser.add_argument(
        '--output',
        default='metapath_consistency.png',
        help='Output PNG file (default: metapath_consistency.png)'
    )
    parser.add_argument(
        '--min-enrichment',
        type=float,
        default=0.0,
        help='Minimum enrichment_min to plot (default: 0.0)'
    )

    args = parser.parse_args()

    # Read data
    print(f"Reading {args.input}...")
    df = pd.read_csv(args.input, sep='\t')
    print(f"Loaded {len(df)} unique metapaths")

    # Filter
    df_filtered = df[df['enrichment_min'] >= args.min_enrichment].copy()
    print(f"Filtered to {len(df_filtered)} metapaths with enrichment_min >= {args.min_enrichment}")

    # Filter for log scale (enrichment_min > 0)
    df_filtered = df_filtered[df_filtered['enrichment_min'] > 0]
    print(f"Further filtered to {len(df_filtered)} metapaths with enrichment_min > 0 (for log scale)")

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))

    # Create scatter plot with color gradient based on enrichment_mean
    scatter = ax.scatter(
        df_filtered['num_queries'],
        df_filtered['enrichment_min'],
        c=df_filtered['enrichment_mean'],
        cmap='viridis',
        alpha=0.6,
        s=50,
        edgecolors='black',
        linewidth=0.5,
        norm=plt.matplotlib.colors.LogNorm()
    )

    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax, label='Mean Enrichment (log scale)')

    # Add reference line at enrichment = 1.0
    ax.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, linewidth=1.5,
               label='No enrichment (baseline)')

    # Labels and formatting
    ax.set_xlabel('Number of Queries', fontsize=12)
    ax.set_ylabel('Minimum Enrichment (log scale)', fontsize=12)
    ax.set_title('Metapath Consistency: Minimum Enrichment vs Query Coverage\n' +
                 'Upper right = metapaths that work well across many queries',
                 fontsize=14, fontweight='bold')

    # Log scale for y-axis
    ax.set_yscale('log')

    # Grid
    ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    ax.set_axisbelow(True)

    # Legend
    ax.legend(loc='upper right', fontsize=10)

    # Tight layout
    plt.tight_layout()

    # Save
    plt.savefig(args.output, dpi=300, bbox_inches='tight')
    print(f"Saved plot to {args.output}")

    # Print statistics
    print("\nStatistics:")
    print(f"Total metapaths plotted: {len(df_filtered)}")
    print(f"Enrichment_min range: {df_filtered['enrichment_min'].min():.2f} - {df_filtered['enrichment_min'].max():.2f}")
    print(f"Num_queries range: {df_filtered['num_queries'].min()} - {df_filtered['num_queries'].max()}")
    print(f"Metapaths in multiple queries: {(df_filtered['num_queries'] > 1).sum()}")
    print(f"Metapaths with min enrichment > 1.0: {(df_filtered['enrichment_min'] > 1.0).sum()}")
    print(f"Metapaths in multiple queries with min enrichment > 1.0: {((df_filtered['num_queries'] > 1) & (df_filtered['enrichment_min'] > 1.0)).sum()}")


if __name__ == '__main__':
    main()
