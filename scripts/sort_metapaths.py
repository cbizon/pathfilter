#!/usr/bin/env python3
"""Sort metapath enrichment results by enrichment within each query."""
import argparse
import pandas as pd


def main():
    parser = argparse.ArgumentParser(
        description='Sort metapath enrichment results by enrichment within each query'
    )
    parser.add_argument(
        '--input',
        default='metapath_enrichment.tsv',
        help='Input TSV file (default: metapath_enrichment.tsv)'
    )
    parser.add_argument(
        '--output',
        default='metapath_enrichment_sorted.tsv',
        help='Output TSV file (default: metapath_enrichment_sorted.tsv)'
    )
    parser.add_argument(
        '--ascending',
        action='store_true',
        help='Sort enrichment ascending instead of descending'
    )

    args = parser.parse_args()

    # Read the TSV file
    print(f"Reading {args.input}...")
    df = pd.read_csv(args.input, sep='\t')
    print(f"Loaded {len(df)} rows")

    # Sort by query_id (ascending) and enrichment (descending by default)
    print("Sorting by query_id and enrichment...")
    df_sorted = df.sort_values(
        by=['query_id', 'enrichment'],
        ascending=[True, args.ascending]
    )

    # Write to output file
    print(f"Writing to {args.output}...")
    df_sorted.to_csv(args.output, sep='\t', index=False)

    print(f"Done! Sorted {len(df_sorted)} rows")
    print(f"\nTop entries per query:")
    for query_id in df_sorted['query_id'].unique()[:5]:  # Show first 5 queries
        query_data = df_sorted[df_sorted['query_id'] == query_id]
        top_entry = query_data.iloc[0]
        print(f"  {query_id}: enrichment={top_entry['enrichment']:.2f}, "
              f"precision={top_entry['precision']:.3f}, "
              f"frequency={top_entry['frequency']:.4f}")


if __name__ == '__main__':
    main()
