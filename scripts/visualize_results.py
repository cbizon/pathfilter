#!/usr/bin/env python3
"""Visualize filter evaluation results with subplots for each query."""
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathfilter.query_loader import load_all_queries


def load_results(results_file: str) -> pd.DataFrame:
    """Load the evaluation results CSV/TSV."""
    # Use pandas auto-detect for separator
    return pd.read_csv(results_file, sep=None, engine='python')


def get_query_names(query_file: str) -> dict:
    """
    Get mapping of query IDs to descriptive names.

    Returns:
        Dict mapping query ID (e.g., 'PFTQ-23-c') to formatted name
        (e.g., 'PFTQ-23-c: Sorafenib → liver carcinoma')
    """
    queries = load_all_queries(query_file)
    return {
        q.name: f"{q.name}: {q.start_label} → {q.end_label}"
        for q in queries
    }


def filter_frontier_strategies(df: pd.DataFrame, query_id: str) -> pd.DataFrame:
    """
    Filter to show only frontier strategies: singles + record-setting combinations.

    Strategy:
    1. Always show all individual filters (singles)
    2. For combinations, only show if they set a new best or worst enrichment record

    This reduces visualization from 256 to ~20-30 bars while showing what matters.

    Args:
        df: Results dataframe
        query_id: Query to filter for

    Returns:
        Filtered dataframe with only frontier strategies
    """
    # Get data for this query (excluding 'none')
    query_df = df[(df['query'] == query_id) & (df['filter_strategy'] != 'none')].copy()

    # Add combo size (number of + signs + 1)
    query_df['combo_size'] = query_df['filter_strategy'].apply(lambda x: x.count('+') + 1)

    # Separate singles from combinations
    singles = query_df[query_df['combo_size'] == 1]
    combos = query_df[query_df['combo_size'] > 1]

    if combos.empty:
        return singles

    # Track best and worst enrichment seen so far
    best_enrichment = singles['enrichment'].max()
    worst_enrichment = singles['enrichment'].min()

    frontier_combos = []

    # Process each combination size in order
    for size in sorted(combos['combo_size'].unique()):
        size_combos = combos[combos['combo_size'] == size]

        # Find best and worst at this size
        best_at_size = size_combos.loc[size_combos['enrichment'].idxmax()]
        worst_at_size = size_combos.loc[size_combos['enrichment'].idxmin()]

        # Add if they set new records
        if best_at_size['enrichment'] > best_enrichment:
            frontier_combos.append(best_at_size)
            best_enrichment = best_at_size['enrichment']

        if worst_at_size['enrichment'] < worst_enrichment and worst_at_size.name != best_at_size.name:
            frontier_combos.append(worst_at_size)
            worst_enrichment = worst_at_size['enrichment']

    # Combine singles with frontier combos
    if frontier_combos:
        frontier_df = pd.concat([singles, pd.DataFrame(frontier_combos)], ignore_index=True)
    else:
        frontier_df = singles

    # Sort by combo size then enrichment for nice display
    frontier_df = frontier_df.sort_values(['combo_size', 'enrichment'], ascending=[True, False])

    return frontier_df


def plot_enrichment_by_query(df: pd.DataFrame, query_names: dict, output_file: str):
    """
    Create a figure with subplots for each query showing enrichment vs filters.
    Uses horizontal bar charts showing only frontier filters (singles + record setters).

    Args:
        df: Results dataframe
        query_names: Mapping of query IDs to descriptive names
        output_file: Path to save the figure
    """
    # Get unique queries
    queries = sorted(df['query'].unique())
    n_queries = len(queries)

    # Filter each query to frontier strategies and collect all
    frontier_data = []
    for query_id in queries:
        query_frontier = filter_frontier_strategies(df, query_id)
        frontier_data.append(query_frontier)

    # Determine max number of filters to show (for consistent subplot sizing)
    max_filters = max(len(qf) for qf in frontier_data)

    # Single column layout with horizontal bars
    # Height based on max filters to display
    subplot_height = max(4, max_filters * 0.3)
    fig, axes = plt.subplots(n_queries, 1, figsize=(12, subplot_height * n_queries))
    fig.suptitle('Filter Enrichment by Query (Frontier Strategies)', fontsize=16, y=0.999)

    # Handle single query case
    if n_queries == 1:
        axes = [axes]

    # Plot each query
    for idx, (query_id, query_frontier) in enumerate(zip(queries, frontier_data)):
        ax = axes[idx]

        # Get filter names and enrichment values
        filters = query_frontier['filter_strategy'].tolist()
        enrichments = query_frontier['enrichment'].tolist()
        combo_sizes = query_frontier['combo_size'].tolist()

        n_filters = len(filters)

        # Create horizontal bar chart
        y_pos = np.arange(n_filters)
        bars = ax.barh(y_pos, enrichments, color='steelblue', alpha=0.7)

        # Color bars based on enrichment value and combo size
        for i, (bar, enrichment, combo_size) in enumerate(zip(bars, enrichments, combo_sizes)):
            if enrichment > 1.5:
                bar.set_color('darkgreen')
                bar.set_alpha(0.8)
            elif enrichment >= 1.0:
                bar.set_color('steelblue')
                bar.set_alpha(0.7)
            else:  # enrichment < 1.0
                bar.set_color('coral')
                bar.set_alpha(0.7)

            # Slightly darken combinations to distinguish from singles
            if combo_size > 1:
                bar.set_alpha(bar.get_alpha() + 0.1)

        # Add vertical line at x=1 (no enrichment)
        ax.axvline(x=1.0, color='red', linestyle='--', alpha=0.5, linewidth=1)

        # Formatting
        ax.set_yticks(y_pos)
        # Add combo size indicator to labels
        labeled_filters = [f"[{cs}] {filt}" for filt, cs in zip(filters, combo_sizes)]
        ax.set_yticklabels(labeled_filters, fontsize=8)
        ax.set_xlabel('Enrichment', fontsize=10)
        ax.set_xlim(0, max(enrichments) * 1.1 if enrichments else 2.0)

        # Title with query name and filter count
        title = query_names.get(query_id, query_id)
        ax.set_title(f"{title} ({n_filters} frontier strategies)", fontsize=11, fontweight='bold', pad=10)

        # Add grid for readability
        ax.grid(axis='x', alpha=0.3, linestyle=':', linewidth=0.5)
        ax.set_axisbelow(True)

        # Invert y-axis so first filter is at top
        ax.invert_yaxis()

    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.995])

    # Save figure
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved frontier enrichment visualization to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Visualize filter evaluation results')
    parser.add_argument(
        '--results',
        default='all_filter_results.tsv',
        help='Path to results file (default: all_filter_results.tsv)'
    )
    parser.add_argument(
        '--queries',
        default='normalized_input_data/Pathfinder Test Queries.xlsx.ods',
        help='Path to query definitions file'
    )
    parser.add_argument(
        '--output',
        default='filter_enrichment_by_query.png',
        help='Output file for visualization (default: filter_enrichment_by_query.png)'
    )

    args = parser.parse_args()

    # Load data
    print(f"Loading results from {args.results}...")
    df = load_results(args.results)

    print(f"Loading query definitions from {args.queries}...")
    query_names = get_query_names(args.queries)

    # Create visualization
    print("Creating visualization...")
    plot_enrichment_by_query(df, query_names, args.output)

    print("Done!")


if __name__ == '__main__':
    main()
