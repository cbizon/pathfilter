#!/usr/bin/env python3
"""Analyze metapath enrichment across queries.

This script calculates enrichment statistics for each metapath pattern in the
knowledge graph paths, helping identify which structural patterns correlate
with finding expected nodes.
"""
import argparse
import sys
import csv
from pathlib import Path as FilePath
from typing import List, Dict, Set, Tuple

from pathfilter.query_loader import load_all_queries, load_query_from_sheet, Query
from pathfilter.path_loader import load_paths_for_query, Path
from pathfilter.metapath_analysis import calculate_metapath_enrichment, MetapathStats


def analyze_query_metapaths(
    query: Query,
    paths_dir: str
) -> List[Dict[str, any]]:
    """
    Analyze metapath enrichment for a single query.

    Args:
        query: Query object with expected nodes
        paths_dir: Directory containing path files

    Returns:
        List of result dicts with metapath statistics
    """
    # Load paths for this query
    paths = load_paths_for_query(query, paths_dir)

    if not paths:
        print(f"Warning: No paths found for query {query.name}")
        return []

    # Get expected nodes (already normalized in the input data)
    expected_nodes = set()
    for curies_list in query.expected_nodes.values():
        expected_nodes.update(curies_list)

    if not expected_nodes:
        print(f"Warning: No expected nodes for query {query.name}")
        return []

    # Calculate metapath enrichment
    metapath_stats = calculate_metapath_enrichment(paths, expected_nodes, query.name)

    # Convert to dict format for output
    results = []
    for stats in metapath_stats:
        results.append({
            'query_id': query.name,
            'metapath': stats.metapath,
            'total_paths': stats.total_paths,
            'hit_paths': stats.hit_paths,
            'precision': stats.precision,
            'enrichment': stats.enrichment,
            'frequency': stats.frequency
        })

    return results


def write_tsv_output(results: List[Dict[str, any]], output_file: str):
    """
    Write metapath enrichment results to TSV file.

    Args:
        results: List of result dictionaries
        output_file: Path to output TSV file
    """
    if not results:
        print("No results to write")
        return

    with open(output_file, 'w', newline='') as f:
        fieldnames = [
            'query_id', 'metapath', 'total_paths', 'hit_paths',
            'precision', 'enrichment', 'frequency'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(results)


def main():
    """Main entry point for metapath enrichment analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze metapath enrichment for Pathfinder queries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze all queries
  %(prog)s --output metapath_enrichment.tsv

  # Analyze specific query
  %(prog)s --query PFTQ-4 --output metapath_enrichment.tsv

  # Use custom data directories
  %(prog)s --queries-file normalized_input_data/Pathfinder\\ Test\\ Queries.xlsx.ods \\
           --paths-dir normalized_input_data/paths \\
           --output results.tsv

Output columns:
  query_id   - Query identifier (e.g., PFTQ-4)
  metapath   - Structural pattern (e.g., biolink:Gene ---affects--> biolink:Disease)
  total_paths - Number of paths using this metapath
  hit_paths  - Number of hit paths (containing expected nodes) with this metapath
  precision  - Fraction of paths with this metapath that are hits
  enrichment - How much better than query baseline (>1.0 = better, <1.0 = worse)
  frequency  - How common this metapath is in the query (0.0-1.0)
        """
    )

    parser.add_argument(
        "--query",
        help="Specific query to analyze (e.g., PFTQ-1-c). If not specified, analyzes all queries."
    )

    parser.add_argument(
        "--queries-file",
        default="normalized_input_data/Pathfinder Test Queries.xlsx.ods",
        help="Path to query definitions file (should be pre-normalized)"
    )

    parser.add_argument(
        "--paths-dir",
        default="normalized_input_data/paths",
        help="Directory containing path files (should be pre-normalized)"
    )

    parser.add_argument(
        "--output",
        default="metapath_enrichment.tsv",
        help="Output TSV file for results (default: metapath_enrichment.tsv)"
    )

    parser.add_argument(
        "--min-frequency",
        type=float,
        default=0.0,
        help="Minimum frequency threshold (0.0-1.0). Only output metapaths with frequency >= this value."
    )

    parser.add_argument(
        "--min-paths",
        type=int,
        default=1,
        help="Minimum number of paths. Only output metapaths with total_paths >= this value."
    )

    args = parser.parse_args()

    # Load queries
    try:
        if args.query:
            # Load specific query
            query = load_query_from_sheet(args.queries_file, args.query)
            queries = [query] if query.expected_nodes else []
            if not queries:
                print(f"Error: Query {args.query} has no expected nodes", file=sys.stderr)
                return 1
        else:
            # Load all queries
            queries = load_all_queries(args.queries_file)

    except Exception as e:
        print(f"Error loading queries: {e}", file=sys.stderr)
        return 1

    if not queries:
        print("No queries to analyze", file=sys.stderr)
        return 1

    print(f"Analyzing metapath enrichment for {len(queries)} queries...")
    print()

    # Analyze each query
    all_results = []
    queries_with_no_hits = []

    for query in queries:
        print(f"Processing query: {query.name} ({query.start_label} → {query.end_label})")

        results = analyze_query_metapaths(query, args.paths_dir)

        if results:
            # Check if this query has any hits at all (any enrichment > 0)
            has_hits = any(r['enrichment'] > 0 for r in results)

            if not has_hits:
                print(f"  WARNING: Query has no hits in any metapath - EXCLUDING from output")
                queries_with_no_hits.append(query.name)
                print()
                continue

            # Apply filters if specified
            filtered_results = [
                r for r in results
                if r['frequency'] >= args.min_frequency and r['total_paths'] >= args.min_paths
            ]

            all_results.extend(filtered_results)
            print(f"  Found {len(results)} unique metapaths ({len(filtered_results)} after filtering)")
        else:
            print(f"  No metapaths found")

        print()

    # Summary
    if all_results:
        queries_included = len(queries) - len(queries_with_no_hits)
        print(f"\nAnalyzed {len(queries)} queries ({queries_included} with hits, {len(queries_with_no_hits)} excluded)")
        if queries_with_no_hits:
            print(f"Excluded queries with no hits: {', '.join(queries_with_no_hits)}")
        print(f"Total metapath entries: {len(all_results)}")

        # Write TSV output
        write_tsv_output(all_results, args.output)
        print(f"Results written to {args.output}")
    else:
        print("No results to output")

    return 0


if __name__ == '__main__':
    sys.exit(main())
