"""Command-line interface for path filter evaluation."""
import argparse
import sys
import csv
from pathlib import Path as FilePath
from typing import List, Optional

from pathfilter.query_loader import load_all_queries, load_query_from_sheet, Query
from pathfilter.path_loader import load_paths_for_query
from pathfilter.normalization import get_normalized_expected_nodes
from pathfilter.filters import (
    FilterFunction,
    no_dupe_types,
    no_expression,
    no_related_to,
    no_end_pheno,
    no_chemical_start,
    all_paths,
    DEFAULT_FILTERS,
    STRICT_FILTERS
)
from pathfilter.evaluation import (
    evaluate_filter_strategy,
    evaluate_multiple_strategies,
    format_metrics_table,
    FilterMetrics
)


# Available filter functions by name
AVAILABLE_FILTERS = {
    "no_dupe_types": no_dupe_types,
    "no_expression": no_expression,
    "no_related_to": no_related_to,
    "no_end_pheno": no_end_pheno,
    "no_chemical_start": no_chemical_start,
    "all_paths": all_paths,
}


def parse_filter_names(filter_spec: str) -> List[FilterFunction]:
    """
    Parse filter specification into list of filter functions.

    Args:
        filter_spec: Comma-separated filter names, or "default" or "strict"

    Returns:
        List of filter functions

    Raises:
        ValueError: If filter name is not recognized
    """
    filter_spec = filter_spec.strip().lower()

    # Handle special cases
    if filter_spec == "default":
        return DEFAULT_FILTERS
    elif filter_spec == "strict":
        return STRICT_FILTERS
    elif filter_spec == "none" or filter_spec == "all_paths":
        return [all_paths]

    # Parse individual filters
    filter_names = [name.strip() for name in filter_spec.split(",")]
    filters = []

    for name in filter_names:
        if name not in AVAILABLE_FILTERS:
            available = ", ".join(AVAILABLE_FILTERS.keys())
            raise ValueError(f"Unknown filter '{name}'. Available: {available}, default, strict")
        filters.append(AVAILABLE_FILTERS[name])

    return filters


def evaluate_query(
    query: Query,
    paths_dir: str,
    filter_strategies: dict[str, List[FilterFunction]]
) -> Optional[List[FilterMetrics]]:
    """
    Evaluate filter strategies on a single query.

    Args:
        query: Query object
        paths_dir: Directory containing path files
        filter_strategies: Dict mapping strategy name to filter list

    Returns:
        List of FilterMetrics, or None if no paths found for query
    """
    # Load paths for this query
    paths = load_paths_for_query(query, paths_dir)
    if not paths:
        print(f"Warning: No paths found for query {query.name}")
        return None

    # Get normalized expected nodes
    normalized_expected = get_normalized_expected_nodes(query)
    if not normalized_expected:
        print(f"Warning: No expected nodes for query {query.name}")
        return None

    # Evaluate all strategies
    results = evaluate_multiple_strategies(paths, normalized_expected, filter_strategies)

    return results


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate path filtering strategies on Pathfinder queries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate all queries with default filters
  %(prog)s

  # Evaluate specific query
  %(prog)s --query PFTQ-1-c

  # Compare multiple filter strategies
  %(prog)s --filters "default,strict,none"

  # Use specific filters
  %(prog)s --filters "no_dupe_types,no_expression"

Available filters:
  - default: no_dupe_types + no_expression + no_related_to
  - strict: default + no_end_pheno
  - Individual: no_dupe_types, no_expression, no_related_to, no_end_pheno, no_chemical_start
  - none/all_paths: No filtering
        """
    )

    parser.add_argument(
        "--query",
        help="Specific query to evaluate (e.g., PFTQ-1-c). If not specified, evaluates all queries."
    )

    parser.add_argument(
        "--filters",
        default="default",
        help="Filter strategies to evaluate (comma-separated). Can be 'default', 'strict', or specific filter names."
    )

    parser.add_argument(
        "--queries-file",
        default="input_data/Pathfinder Test Queries.xlsx.ods",
        help="Path to query definitions file"
    )

    parser.add_argument(
        "--paths-dir",
        default="input_data/paths",
        help="Directory containing path files"
    )

    parser.add_argument(
        "--output",
        help="Output file for results (CSV format). If not specified, prints to stdout."
    )

    args = parser.parse_args()

    # Parse filter strategies
    try:
        # For now, support one strategy specification
        # Could be extended to support multiple: "default,strict,none"
        filter_specs = [s.strip() for s in args.filters.split("|")]

        filter_strategies = {}
        for spec in filter_specs:
            filters = parse_filter_names(spec)
            # Use spec as strategy name
            strategy_name = spec if spec in ["default", "strict", "none"] else spec
            filter_strategies[strategy_name] = filters

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

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
        print("No queries to evaluate", file=sys.stderr)
        return 1

    print(f"Evaluating {len(queries)} queries with {len(filter_strategies)} filter strategies...")
    print()

    # Evaluate each query
    all_results = []
    for query in queries:
        print(f"Processing query: {query.name} ({query.start_label} -> {query.end_label})")

        results = evaluate_query(query, args.paths_dir, filter_strategies)

        if results:
            all_results.extend(results)
            # Print results for this query
            print(format_metrics_table(results))
            print()

    # Summary
    if all_results:
        print(f"\nEvaluated {len(queries)} queries")
        print(f"Total evaluations: {len(all_results)}")

        # Write CSV output if requested
        if args.output:
            write_csv_output(all_results, args.output, queries)
            print(f"Results written to {args.output}")
    else:
        print("No results to display")

    return 0


def write_csv_output(results: List[FilterMetrics], output_file: str, queries: List[Query]):
    """Write evaluation results to CSV file."""
    # Build mapping of filter_name to query (if we tracked it)
    # For now, write all results with available fields

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'filter_strategy',
            'total_paths_before',
            'total_paths_after',
            'expected_paths_before',
            'expected_paths_after',
            'recall',
            'precision_before',
            'precision_after',
            'enrichment',
            'retention_rate',
            'expected_nodes_before',
            'expected_nodes_after',
            'expected_nodes_recall'
        ])

        # Data rows
        for metrics in results:
            writer.writerow([
                metrics.filter_name,
                metrics.total_paths_before,
                metrics.total_paths_after,
                metrics.expected_paths_before,
                metrics.expected_paths_after,
                f"{metrics.recall:.4f}",
                f"{metrics.precision_before:.4f}",
                f"{metrics.precision_after:.4f}",
                f"{metrics.enrichment:.4f}",
                f"{metrics.retention_rate:.4f}",
                metrics.expected_nodes_found_before,
                metrics.expected_nodes_found_after,
                f"{metrics.expected_nodes_recall:.4f}"
            ])


if __name__ == "__main__":
    sys.exit(main())
