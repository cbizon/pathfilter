#!/usr/bin/env python3
"""Analyze node degrees for each path in a query.

This diagnostic script shows the degree of each node in every path,
helping understand why degree filters may be overly aggressive.
"""
import argparse
import csv
import sys
from pathlib import Path as FilePath

from pathfilter.query_loader import load_all_queries
from pathfilter.path_loader import load_paths_for_query
from pathfilter.filters import load_node_degrees


def analyze_degrees_per_path(query_name: str, queries_file: str, paths_dir: str,
                             node_degrees_file: str, output_file: str):
    """
    Analyze node degrees for each path in a query.

    Args:
        query_name: Name of query to analyze (e.g., PFTQ-10)
        queries_file: Path to queries file
        paths_dir: Directory containing path files
        node_degrees_file: Path to node degrees TSV
        output_file: Output TSV file path
    """
    # Load query
    all_queries = load_all_queries(queries_file)
    query = None
    for q in all_queries:
        if q.name == query_name:
            query = q
            break

    if not query:
        print(f"Error: Query {query_name} not found", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing query: {query.name} ({query.start_label} -> {query.end_label})")

    # Load paths
    paths = load_paths_for_query(query, paths_dir)
    if not paths:
        print(f"Error: No paths found for query {query_name}", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(paths)} paths")

    # Load node degrees
    if not FilePath(node_degrees_file).exists():
        print(f"Error: Node degrees file not found: {node_degrees_file}", file=sys.stderr)
        sys.exit(1)

    degree_data = load_node_degrees(node_degrees_file)
    print(f"Loaded degrees for {len(degree_data)} nodes")

    # Get expected nodes
    expected_nodes = set()
    for curies_list in query.expected_nodes.values():
        expected_nodes.update(curies_list)

    # Write results
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')

        # Header
        writer.writerow([
            'path_index',
            'has_expected_node',
            'node1_id',
            'node1_degree',
            'node2_id',
            'node2_degree',
            'node3_id',
            'node3_degree',
            'node4_id',
            'node4_degree',
            'max_degree'
        ])

        # Data rows
        for i, path in enumerate(paths):
            # Check if path contains any expected nodes
            has_expected = any(node_id in expected_nodes for node_id in path.path_curies)

            # Get degrees for all 4 nodes
            degrees = []
            for node_id in path.path_curies:
                degree = degree_data.get(node_id, 0)
                degrees.append(degree)

            max_degree = max(degrees)

            writer.writerow([
                i,
                'yes' if has_expected else 'no',
                path.path_curies[0],
                degrees[0],
                path.path_curies[1],
                degrees[1],
                path.path_curies[2],
                degrees[2],
                path.path_curies[3],
                degrees[3],
                max_degree
            ])

    print(f"\nResults written to {output_file}")

    # Print summary statistics
    expected_paths = [p for p in paths if any(n in expected_nodes for n in p.path_curies)]
    print(f"\nSummary:")
    print(f"  Total paths: {len(paths)}")
    print(f"  Paths with expected nodes: {len(expected_paths)}")

    # Count paths that would pass each degree threshold
    all_degrees = []
    expected_degrees = []

    for path in paths:
        degrees = [degree_data.get(node_id, 0) for node_id in path.path_curies]
        max_degree = max(degrees)
        all_degrees.append(max_degree)

        if any(n in expected_nodes for n in path.path_curies):
            expected_degrees.append(max_degree)

    print(f"\nPaths passing degree thresholds:")
    for threshold in [100, 500, 1000, 5000, 10000]:
        all_pass = sum(1 for d in all_degrees if d <= threshold)
        expected_pass = sum(1 for d in expected_degrees if d <= threshold)
        print(f"  max_degree_{threshold}:")
        print(f"    All paths: {all_pass}/{len(paths)} ({100*all_pass/len(paths):.1f}%)")
        if expected_degrees:
            print(f"    Expected paths: {expected_pass}/{len(expected_degrees)} ({100*expected_pass/len(expected_degrees):.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze node degrees for each path in a query"
    )

    parser.add_argument(
        "--query",
        required=True,
        help="Query name to analyze (e.g., PFTQ-10)"
    )

    parser.add_argument(
        "--queries-file",
        default="normalized_input_data/Pathfinder Test Queries.xlsx.ods",
        help="Path to queries file"
    )

    parser.add_argument(
        "--paths-dir",
        default="normalized_input_data/paths",
        help="Directory containing path files"
    )

    parser.add_argument(
        "--node-degrees-file",
        default="robokop_node_degrees.tsv",
        help="Path to node degrees TSV file"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Output TSV file path"
    )

    args = parser.parse_args()

    analyze_degrees_per_path(
        query_name=args.query,
        queries_file=args.queries_file,
        paths_dir=args.paths_dir,
        node_degrees_file=args.node_degrees_file,
        output_file=args.output
    )


if __name__ == "__main__":
    main()
