#!/usr/bin/env python3
"""Aggregate metapath statistics across queries.

For each metapath, calculate max, min, and mean enrichment and frequency
across all queries where it appears.
"""
import argparse
import pandas as pd


def main():
    parser = argparse.ArgumentParser(
        description='Aggregate metapath statistics across queries'
    )
    parser.add_argument(
        '--input',
        default='metapath_enrichment.tsv',
        help='Input TSV file (default: metapath_enrichment.tsv)'
    )
    parser.add_argument(
        '--output',
        default='metapath_aggregated.tsv',
        help='Output TSV file (default: metapath_aggregated.tsv)'
    )
    parser.add_argument(
        '--min-queries',
        type=int,
        default=1,
        help='Minimum number of queries a metapath must appear in (default: 1)'
    )

    args = parser.parse_args()

    # Read data
    print(f"Reading {args.input}...")
    df = pd.read_csv(args.input, sep='\t')
    print(f"Loaded {len(df)} metapath entries")

    # Identify queries with no hits overall (all metapaths have enrichment = 0)
    # These queries should be excluded because enrichment is meaningless there
    queries_with_no_hits = df.groupby('query_id')['enrichment'].max() == 0
    queries_to_exclude = queries_with_no_hits[queries_with_no_hits].index.tolist()

    if queries_to_exclude:
        print(f"Excluding {len(queries_to_exclude)} queries with no hits: {', '.join(queries_to_exclude)}")
        df = df[~df['query_id'].isin(queries_to_exclude)]
        print(f"Filtered to {len(df)} entries from queries with hits")

    # Group by metapath and calculate statistics
    print("Aggregating statistics by metapath...")
    aggregated = df.groupby('metapath').agg({
        'enrichment': ['min', 'max', 'mean'],
        'frequency': ['min', 'max', 'mean'],
        'query_id': 'count'  # Number of queries this metapath appears in
    }).reset_index()

    # Flatten multi-level column names
    aggregated.columns = [
        'metapath',
        'enrichment_min',
        'enrichment_max',
        'enrichment_mean',
        'frequency_min',
        'frequency_max',
        'frequency_mean',
        'num_queries'
    ]

    # Filter by minimum number of queries
    if args.min_queries > 1:
        aggregated = aggregated[aggregated['num_queries'] >= args.min_queries]
        print(f"Filtered to {len(aggregated)} metapaths appearing in >= {args.min_queries} queries")

    # Sort by min enrichment (ascending), then by num_queries (descending)
    aggregated = aggregated.sort_values(
        ['enrichment_min', 'num_queries'],
        ascending=[True, False]
    )

    # Write to output
    print(f"Writing to {args.output}...")
    aggregated.to_csv(args.output, sep='\t', index=False)

    print(f"Done! Aggregated {len(aggregated)} unique metapaths")

    # Print statistics
    print("\nTop 10 metapaths by minimum enrichment:")
    print(aggregated[['metapath', 'enrichment_min', 'enrichment_max', 'enrichment_mean', 'num_queries']].head(10).to_string(index=False))

    print("\nStatistics:")
    print(f"Total unique metapaths: {len(aggregated)}")
    print(f"Metapaths in multiple queries: {(aggregated['num_queries'] > 1).sum()}")
    print(f"Max queries for a metapath: {aggregated['num_queries'].max()}")
    print(f"Metapaths with min enrichment > 1.0: {(aggregated['enrichment_min'] > 1.0).sum()}")


if __name__ == '__main__':
    main()
