"""Command-line interface for path filter evaluation."""
import argparse
import sys
import csv
from pathlib import Path as FilePath
from typing import List, Optional

from pathfilter.query_loader import load_all_queries, Query
from pathfilter.path_loader import load_paths_for_query
from pathfilter.filters import (
    FilterFunction,
    no_dupe_types,
    no_expression,
    no_related_to,
    no_end_pheno,
    no_chemical_start,
    no_repeat_predicates,
    no_abab,
    all_paths
)
from itertools import combinations
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
    "no_repeat_predicates": no_repeat_predicates,
    "no_abab": no_abab,
    "all_paths": all_paths,
}


def generate_all_filter_combinations(
    filter_dict: Optional[dict[str, FilterFunction]] = None,
    max_combination_size: Optional[int] = None
) -> dict[str, List[FilterFunction]]:
    """
    Generate all combinations of filters for comprehensive evaluation.

    Args:
        filter_dict: Dict of filter_name -> filter_function. If None, uses all
                     available filters except all_paths and no_chemical_start
        max_combination_size: Maximum number of filters in a combination. If None,
                              generates all combinations up to total number of filters

    Returns:
        Dict mapping strategy name to filter list
    """
    # Default: use all available filters except baseline and no_chemical_start
    if filter_dict is None:
        filter_dict = {
            name: func for name, func in AVAILABLE_FILTERS.items()
            if name not in ["all_paths", "no_chemical_start"]
        }

    strategies = {}

    # Baseline: no filtering
    strategies["none"] = [all_paths]

    # Individual filters
    for name, filter_func in filter_dict.items():
        strategies[name] = [filter_func]

    # All combinations of 2..N filters
    filter_names = list(filter_dict.keys())
    max_size = max_combination_size if max_combination_size is not None else len(filter_names)

    for n in range(2, max_size + 1):
        for combo in combinations(filter_names, n):
            strategy_name = "+".join(combo)
            strategy_filters = [filter_dict[name] for name in combo]
            strategies[strategy_name] = strategy_filters

    return strategies


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
    individual_filters: Optional[dict[str, FilterFunction]] = None,
    filter_strategies: Optional[dict[str, List[FilterFunction]]] = None
) -> Optional[List[FilterMetrics]]:
    """
    Evaluate filter strategies on a single query.

    ASSUMES: Query and paths contain pre-normalized CURIEs.

    Args:
        query: Query object (with pre-normalized expected nodes)
        paths_dir: Directory containing path files (pre-normalized)
        individual_filters: Dict of filter_name -> filter_function (for optimized evaluation)
        filter_strategies: Dict of strategy_name -> filter_list (for custom combinations)

    Returns:
        List of FilterMetrics, or None if no paths found for query
    """
    # Load paths for this query
    paths = load_paths_for_query(query, paths_dir)
    if not paths:
        print(f"Warning: No paths found for query {query.name}")
        return None

    # Get expected nodes (already normalized in the input data)
    expected_nodes = set()
    for curies_list in query.expected_nodes.values():
        expected_nodes.update(curies_list)

    if not expected_nodes:
        print(f"Warning: No expected nodes for query {query.name}")
        return None

    # Evaluate using optimized or custom path
    if individual_filters is not None:
        # Optimized: evaluate all combinations using caching
        results = evaluate_multiple_strategies(paths, expected_nodes, individual_filters)
    elif filter_strategies is not None:
        # Custom: evaluate each strategy separately
        results = []
        for strategy_name, filters in filter_strategies.items():
            metrics = evaluate_filter_strategy(paths, expected_nodes, filters, strategy_name)
            results.append(metrics)
    else:
        raise ValueError("Must provide either individual_filters or filter_strategies")

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
        default="all_combinations",
        help="Filter strategies to evaluate. Use 'all_combinations' to test all combinations, or specify filter names."
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
        help="Output file for results (CSV format). If not specified, prints to stdout."
    )

    args = parser.parse_args()

    # Parse filter strategies
    individual_filters = None
    filter_strategies = None

    try:
        if args.filters == "all_combinations":
            # Build individual filters dict for optimized evaluation
            individual_filters = {
                name: func for name, func in AVAILABLE_FILTERS.items()
                if name not in ["all_paths", "no_chemical_start"]
            }
            # Calculate number of combinations for reporting
            n_filters = len(individual_filters)
            n_combinations = sum(1 for r in range(1, n_filters + 1)
                               for _ in combinations(individual_filters.keys(), r)) + 1  # +1 for "none"
            print(f"Evaluating {n_combinations} filter combinations from {n_filters} individual filters")
        else:
            # Parse user-specified filters
            filter_specs = [s.strip() for s in args.filters.split("|")]
            filter_strategies = {}
            for spec in filter_specs:
                filters = parse_filter_names(spec)
                strategy_name = spec
                filter_strategies[strategy_name] = filters

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Load queries
    try:
        if args.query:
            # Load all queries and filter to the requested one
            all_queries = load_all_queries(args.queries_file)
            queries = [q for q in all_queries if q.name == args.query]
            if not queries:
                print(f"Error: Query {args.query} not found", file=sys.stderr)
                return 1
            if not queries[0].expected_nodes:
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

    # Report evaluation scope
    if individual_filters:
        print(f"Evaluating {len(queries)} queries...")
    else:
        print(f"Evaluating {len(queries)} queries with {len(filter_strategies)} filter strategies...")
    print()

    # Evaluate each query
    all_results = []  # List of (query_name, FilterMetrics) tuples
    for query in queries:
        print(f"Processing query: {query.name} ({query.start_label} -> {query.end_label})")

        results = evaluate_query(
            query,
            args.paths_dir,
            individual_filters=individual_filters,
            filter_strategies=filter_strategies
        )

        if results:
            # Store with query name
            for metrics in results:
                all_results.append((query.name, metrics))

            # Print results for this query (optional, can be verbose)
            n_strategies = len(results)
            if n_strategies <= 5:  # Only print table if not too many strategies
                print(format_metrics_table(results))
            else:
                print(f"  Evaluated {n_strategies} filter strategies")
            print()

    # Summary
    if all_results:
        print(f"\nEvaluated {len(queries)} queries")
        print(f"Total evaluations: {len(all_results)}")
        if individual_filters:
            n_strategies_per_query = len(all_results) // len(queries) if queries else 0
            print(f"Filter combinations tested: {n_strategies_per_query}")
        else:
            print(f"Filter combinations tested: {len(filter_strategies)}")

        # Write CSV output if requested
        if args.output:
            write_csv_output(all_results, args.output)
            print(f"Results written to {args.output}")
    else:
        print("No results to display")

    return 0


def write_csv_output(results: List[tuple[str, FilterMetrics]], output_file: str):
    """Write evaluation results to TSV file.

    Args:
        results: List of tuples (query_name, metrics)
        output_file: Path to output TSV file
    """
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')

        # Header
        writer.writerow([
            'query',
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
        for query_name, metrics in results:
            writer.writerow([
                query_name,
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
