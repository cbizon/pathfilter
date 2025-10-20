#!/usr/bin/env python3
"""Visualize filter evaluation results with subplots for each query."""
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathfilter.query_loader import load_all_queries


def load_results(results_file: str) -> pd.DataFrame:
    """Load the evaluation results CSV."""
    return pd.read_csv(results_file)


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


def plot_enrichment_by_query(df: pd.DataFrame, query_names: dict, output_file: str):
    """
    Create a figure with subplots for each query showing enrichment vs filters.

    Args:
        df: Results dataframe
        query_names: Mapping of query IDs to descriptive names
        output_file: Path to save the figure
    """
    # Get unique queries and filters
    queries = sorted(df['query'].unique())

    # Get all unique filters (excluding 'none') in a consistent order
    all_filters = df[df['filter_strategy'] != 'none']['filter_strategy'].unique()
    # Sort filters by complexity (number of + signs) then alphabetically
    all_filters = sorted(all_filters, key=lambda x: (x.count('+'), x))

    # Calculate grid dimensions
    n_queries = len(queries)
    n_cols = 4
    n_rows = (n_queries + n_cols - 1) // n_cols

    # Create figure with subplots
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, 5 * n_rows))
    fig.suptitle('Filter Enrichment by Query', fontsize=16, y=0.995)

    # Flatten axes array for easier iteration
    if n_queries == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    # Plot each query
    for idx, query_id in enumerate(queries):
        ax = axes[idx]

        # Get data for this query (excluding 'none' filter)
        query_df = df[(df['query'] == query_id) & (df['filter_strategy'] != 'none')]

        # Create a dataframe with all filters (fill missing with NaN)
        plot_data = pd.DataFrame({'filter_strategy': all_filters})
        plot_data = plot_data.merge(
            query_df[['filter_strategy', 'enrichment']],
            on='filter_strategy',
            how='left'
        )

        # Create bar chart
        x_pos = np.arange(len(all_filters))
        bars = ax.bar(x_pos, plot_data['enrichment'], color='steelblue', alpha=0.7)

        # Color bars based on enrichment value
        for i, (bar, enrichment) in enumerate(zip(bars, plot_data['enrichment'])):
            if pd.notna(enrichment):
                if enrichment > 1.5:
                    bar.set_color('darkgreen')
                    bar.set_alpha(0.8)
                elif enrichment >= 1.0:
                    bar.set_color('steelblue')
                    bar.set_alpha(0.7)
                else:  # enrichment < 1.0
                    bar.set_color('coral')
                    bar.set_alpha(0.7)

        # Add horizontal line at y=1 (no enrichment)
        ax.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, linewidth=1)

        # Formatting
        ax.set_xticks(x_pos)
        ax.set_xticklabels(all_filters, rotation=45, ha='right', fontsize=8)
        ax.set_ylabel('Enrichment', fontsize=10)
        ax.set_ylim(0, max(plot_data['enrichment'].max() * 1.1, 2.0) if not plot_data['enrichment'].isna().all() else 2.0)

        # Title with query name
        title = query_names.get(query_id, query_id)
        ax.set_title(title, fontsize=10, fontweight='bold')

        # Add grid for readability
        ax.grid(axis='y', alpha=0.3, linestyle=':', linewidth=0.5)
        ax.set_axisbelow(True)

    # Hide unused subplots
    for idx in range(n_queries, len(axes)):
        axes[idx].set_visible(False)

    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.995])

    # Save figure
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved enrichment visualization to {output_file}")

    # Also save as PDF for better quality
    pdf_file = output_file.replace('.png', '.pdf')
    plt.savefig(pdf_file, bbox_inches='tight')
    print(f"Saved PDF version to {pdf_file}")


def main():
    parser = argparse.ArgumentParser(description='Visualize filter evaluation results')
    parser.add_argument(
        '--results',
        default='all_filter_results.csv',
        help='Path to results CSV file (default: all_filter_results.csv)'
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
