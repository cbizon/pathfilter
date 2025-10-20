#!/usr/bin/env python3
"""Create a table of the best filter for each query based on enrichment."""
import argparse
from pathlib import Path
import pandas as pd
from pathfilter.query_loader import load_all_queries


def count_filters(filter_strategy: str) -> int:
    """
    Count the number of individual filters in a strategy.

    Args:
        filter_strategy: Filter name like "no_dupe_types" or "no_dupe_types+no_expression"

    Returns:
        Number of individual filters (e.g., "no_dupe_types+no_expression" returns 2)
    """
    if filter_strategy == 'none':
        return 0
    if filter_strategy == 'all_four':
        return 4
    return filter_strategy.count('+') + 1


def get_best_filter_per_query(df: pd.DataFrame, query_names: dict) -> pd.DataFrame:
    """
    Find the best filter for each query based on enrichment.

    If the best enrichment is <= 1.0, returns 'none' as the best filter.
    For ties, chooses the filter with the fewest components.

    Args:
        df: Results dataframe
        query_names: Mapping of query IDs to descriptive names

    Returns:
        DataFrame with columns: query_id, name, best_filter, enrichment
    """
    results = []

    # Keep 'none' filter for reference
    df_with_count = df.copy()
    df_with_count['filter_count'] = df_with_count['filter_strategy'].apply(count_filters)

    # Group by query
    for query_id in sorted(df['query'].unique()):
        query_df = df_with_count[df_with_count['query'] == query_id]

        # Get 'none' enrichment (should always be 1.0)
        none_enrichment = query_df[query_df['filter_strategy'] == 'none']['enrichment'].iloc[0]

        # Exclude 'none' to find best filter
        query_df_filtered = query_df[query_df['filter_strategy'] != 'none']

        # Find maximum enrichment among filters
        max_enrichment = query_df_filtered['enrichment'].max()

        # If best enrichment is <= 1.0, use 'none'
        if max_enrichment <= 1.0:
            best_filter = 'none'
            best_enrichment = none_enrichment
        else:
            # Get all filters with max enrichment
            best_filters = query_df_filtered[query_df_filtered['enrichment'] == max_enrichment]

            # If there are ties, choose the simplest (fewest filters)
            if len(best_filters) > 1:
                best_filters = best_filters.sort_values('filter_count')

            best_row = best_filters.iloc[0]
            best_filter = best_row['filter_strategy']
            best_enrichment = best_row['enrichment']

        results.append({
            'query_id': query_id,
            'name': query_names.get(query_id, query_id),
            'best_filter': best_filter,
            'enrichment': best_enrichment
        })

    df_results = pd.DataFrame(results)
    # Sort by enrichment descending
    df_results = df_results.sort_values('enrichment', ascending=False)
    return df_results


def main():
    parser = argparse.ArgumentParser(
        description='Create table of best filters per query'
    )
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
        default='best_filters_table.tsv',
        help='Output TSV file (default: best_filters_table.tsv)'
    )

    args = parser.parse_args()

    # Load data
    print(f"Loading results from {args.results}...")
    df = pd.read_csv(args.results)

    print(f"Loading query definitions from {args.queries}...")
    queries = load_all_queries(args.queries)
    query_names = {
        q.name: f"{q.start_label} → {q.end_label}"
        for q in queries
    }

    # Create best filters table
    print("Finding best filter for each query...")
    best_filters_df = get_best_filter_per_query(df, query_names)

    # Save to TSV
    best_filters_df.to_csv(args.output, index=False, sep='\t')
    print(f"Saved best filters table to {args.output}")

    # Also print to console
    print("\nBest Filters by Query:")
    print("=" * 100)
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.width', None)
    print(best_filters_df.to_string(index=False))
    print("=" * 100)

    # Print some statistics
    print(f"\nTotal queries: {len(best_filters_df)}")
    print(f"Average best enrichment: {best_filters_df['enrichment'].mean():.4f}")
    print(f"Median best enrichment: {best_filters_df['enrichment'].median():.4f}")
    print(f"\nMost common best filters:")
    filter_counts = best_filters_df['best_filter'].value_counts()
    for filter_name, count in filter_counts.head(5).items():
        print(f"  {filter_name}: {count} queries")


if __name__ == '__main__':
    main()
