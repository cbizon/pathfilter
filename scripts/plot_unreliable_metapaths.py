#!/usr/bin/env python3
"""Plot enrichment vs frequency for metapaths with complete misses (num_queries=max, enrichment_min=0)."""
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser(
        description='Plot enrichment vs frequency for metapaths with complete misses'
    )
    parser.add_argument(
        '--aggregated',
        default='metapath_aggregated.tsv',
        help='Aggregated TSV file (default: metapath_aggregated.tsv)'
    )
    parser.add_argument(
        '--enrichment',
        default='metapath_enrichment.tsv',
        help='Enrichment TSV file (default: metapath_enrichment.tsv)'
    )
    parser.add_argument(
        '--output',
        default='complete_misses.png',
        help='Output PNG file (default: complete_misses.png)'
    )
    parser.add_argument(
        '--num-queries',
        type=int,
        default=7,
        help='Filter for metapaths with this many queries (default: 7, the max after excluding queries with no hits)'
    )

    args = parser.parse_args()

    # Read aggregated data to find unreliable metapaths
    print(f"Reading {args.aggregated}...")
    df_agg = pd.read_csv(args.aggregated, sep='\t')

    # Find metapaths with num_queries=8 and enrichment_min=0
    unreliable = df_agg[
        (df_agg['num_queries'] == args.num_queries) &
        (df_agg['enrichment_min'] == 0)
    ]
    print(f"Found {len(unreliable)} metapaths with num_queries={args.num_queries} and enrichment_min=0")

    if len(unreliable) == 0:
        print("No metapaths found matching criteria")
        return

    # Get the list of metapaths
    metapaths = unreliable['metapath'].tolist()

    # Read unaggregated enrichment data
    print(f"Reading {args.enrichment}...")
    df_enrich = pd.read_csv(args.enrichment, sep='\t')

    # Filter to only these metapaths
    df_plot = df_enrich[df_enrich['metapath'].isin(metapaths)]

    # Create subplots
    n_metapaths = len(metapaths)
    n_cols = 3
    n_rows = (n_metapaths + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 5 * n_rows))
    fig.suptitle(f'Metapaths with Complete Misses: Enrichment vs Frequency\n' +
                 f'(num_queries={args.num_queries}, enrichment_min=0 - fail in at least one query)',
                 fontsize=16, fontweight='bold')

    # Flatten axes
    if n_metapaths == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    # Plot each metapath
    for idx, metapath in enumerate(metapaths):
        ax = axes[idx]

        # Get data for this metapath
        metapath_data = df_plot[df_plot['metapath'] == metapath]

        # Scatter plot
        ax.scatter(
            metapath_data['frequency'],
            metapath_data['enrichment'],
            alpha=0.7,
            s=100,
            c=range(len(metapath_data)),
            cmap='tab10',
            edgecolors='black',
            linewidth=1
        )

        # Add query labels
        for _, row in metapath_data.iterrows():
            ax.annotate(
                row['query_id'],
                (row['frequency'], row['enrichment']),
                fontsize=7,
                ha='right',
                va='bottom'
            )

        # Add reference line at enrichment = 1.0
        ax.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, linewidth=1)

        # Labels
        ax.set_xlabel('Frequency', fontsize=9)
        ax.set_ylabel('Enrichment', fontsize=9)

        # Title - abbreviated metapath
        title = metapath.replace('biolink:', '').replace('---', ' ')
        if len(title) > 100:
            title = title[:97] + '...'
        ax.set_title(title, fontsize=8, fontweight='bold')

        # Grid
        ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
        ax.set_axisbelow(True)

    # Hide unused subplots
    for idx in range(n_metapaths, len(axes)):
        axes[idx].set_visible(False)

    # Tight layout
    plt.tight_layout(rect=[0, 0, 1, 0.97])

    # Save
    plt.savefig(args.output, dpi=300, bbox_inches='tight')
    print(f"Saved plot to {args.output}")

    # Print details
    print("\nMetapath details:")
    for metapath in metapaths:
        metapath_data = df_plot[df_plot['metapath'] == metapath]
        print(f"\n{metapath[:100]}...")
        print(f"  Queries: {', '.join(metapath_data['query_id'].tolist())}")
        print(f"  Enrichment range: {metapath_data['enrichment'].min():.2f} - {metapath_data['enrichment'].max():.2f}")
        print(f"  Frequency range: {metapath_data['frequency'].min():.4f} - {metapath_data['frequency'].max():.4f}")


if __name__ == '__main__':
    main()
