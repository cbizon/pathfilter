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
    no_dupe_but_gene,
    no_nonconsecutive_dupe,
    all_paths,
    load_node_characteristics,
    create_min_ic_filter,
    create_max_degree_filter,
    create_max_path_count_filter
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
    "no_dupe_but_gene": no_dupe_but_gene,
    "no_nonconsecutive_dupe": no_nonconsecutive_dupe,
    "all_paths": all_paths,
}


def generate_all_filter_combinations(
    filter_dict: Optional[dict[str, FilterFunction]] = None,
    max_combination_size: Optional[int] = None
) -> dict[str, List[FilterFunction]]:
    """
    Generate all combinations of filters for comprehensive evaluation.

    Node filters (min_ic_*, max_degree_*) are never combined with each other,
    only with path-based filters.

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

    # Separate node filters (IC, degree) from path-based filters
    node_filters = {name: func for name, func in filter_dict.items()
                   if name.startswith("min_ic_") or name.startswith("max_degree_")}
    path_filters = {name: func for name, func in filter_dict.items()
                   if not (name.startswith("min_ic_") or name.startswith("max_degree_"))}

    strategies = {}

    # Baseline: no filtering
    strategies["none"] = [all_paths]

    # Individual filters (both path and IC)
    for name, filter_func in filter_dict.items():
        strategies[name] = [filter_func]

    # All combinations of path filters (size 1 to N)
    path_filter_names = list(path_filters.keys())
    max_size = max_combination_size if max_combination_size is not None else len(path_filter_names)

    # Generate all path filter combinations (including single filters)
    path_combinations = []
    for n in range(1, max_size + 1):
        path_combinations.extend(combinations(path_filter_names, n))

    # For each path filter combination, create:
    # 1. Path filters only (for n >= 2, since n=1 is already in individual filters)
    # 2. Path filters + each node filter
    for combo in path_combinations:
        if len(combo) >= 2:
            # Add path-only combination
            strategy_name = "+".join(combo)
            strategy_filters = [path_filters[name] for name in combo]
            strategies[strategy_name] = strategy_filters

        # Add variants with each node filter (for all combo sizes)
        for node_name, node_func in node_filters.items():
            strategy_name_with_node = "+".join(combo) + "+" + node_name
            combo_filters = [path_filters[name] for name in combo]
            strategies[strategy_name_with_node] = combo_filters + [node_func]

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
  - Path-based: no_dupe_types, no_expression, no_related_to, no_end_pheno,
                no_chemical_start, no_repeat_predicates, no_abab,
                no_dupe_but_gene, no_nonconsecutive_dupe
  - Node-based (requires --node-degrees-file): min_ic_30, min_ic_50, min_ic_70
  - none/all_paths: No filtering

Node-based filters:
  min_ic_30, min_ic_50, min_ic_70: Reject paths with any node having IC below threshold
  (Requires robokop_node_degrees.tsv - run calculate_node_degrees.py first)
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

    parser.add_argument(
        "--node-degrees-file",
        default="node_path_counts_with_degrees.tsv",
        help="Path to node characteristics TSV file with IC, degree, and path count data"
    )

    args = parser.parse_args()

    # Load node characteristics (IC, degree, and path counts) and create filters if file exists
    node_filters_loaded = False
    path_count_data = {}  # Store for future use
    if FilePath(args.node_degrees_file).exists():
        try:
            print(f"Loading node characteristics from {args.node_degrees_file}...")
            ic_data, degree_data, path_count_data = load_node_characteristics(args.node_degrees_file)

            # Create IC filters for thresholds 30, 50, 70
            AVAILABLE_FILTERS["min_ic_30"] = create_min_ic_filter(ic_data, min_ic=30.0)
            AVAILABLE_FILTERS["min_ic_50"] = create_min_ic_filter(ic_data, min_ic=50.0)
            AVAILABLE_FILTERS["min_ic_70"] = create_min_ic_filter(ic_data, min_ic=70.0)

            # Create degree filters for thresholds 1000, 5000, 10000
            AVAILABLE_FILTERS["max_degree_1000"] = create_max_degree_filter(degree_data, max_degree=1000)
            AVAILABLE_FILTERS["max_degree_5000"] = create_max_degree_filter(degree_data, max_degree=5000)
            AVAILABLE_FILTERS["max_degree_10000"] = create_max_degree_filter(degree_data, max_degree=10000)

            node_filters_loaded = True
            print(f"Node filters loaded:")
            print(f"  IC: min_ic_30, min_ic_50, min_ic_70")
            print(f"  Degree: max_degree_1000, max_degree_5000, max_degree_10000")
        except Exception as e:
            print(f"Warning: Could not load node characteristics from {args.node_degrees_file}: {e}")
            print("Continuing without node-based filters")
    else:
        print(f"Warning: Node characteristics file not found: {args.node_degrees_file}")
        print("Continuing without node-based filters. Run rerun_all.sh or these steps:")
        print("  1. uv run python scripts/calculate_node_degrees.py")
        print("  2. uv run python scripts/analyze_node_path_counts.py")
        print("  3. uv run python scripts/join_path_counts_with_degrees.py")

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
            # Calculate number of combinations (accounting for node filter logic)
            # Node filters (IC, degree, path_count) are never combined with each other
            # Path count filters are added per query, so actual combinations will vary
            n_filters = len(individual_filters)
            node_filter_count = sum(1 for name in individual_filters
                                   if name.startswith("min_ic_") or name.startswith("max_degree_"))
            path_filter_count = n_filters - node_filter_count

            # Base combinations with global node filters (IC + degree)
            # With path count filters added per query: +3 more node filters
            # Formula: 2^P * (1 + N) where P=path filters, N=node filters (global + per-query)
            base_combinations = (2 ** path_filter_count) * (1 + node_filter_count)
            with_path_count = (2 ** path_filter_count) * (1 + node_filter_count + 3)  # +3 for p90, p95, p99
            print(f"Evaluating filter combinations: {base_combinations} baseline + 3 path_count filters per query = {with_path_count} per query")
            print(f"  From {n_filters} global filters (6 path + {node_filter_count} node)")
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

        # Create query-specific filters (path count filters)
        query_individual_filters = individual_filters.copy() if individual_filters else None
        query_filter_strategies = filter_strategies

        if path_count_data and query.name in path_count_data:
            # Calculate percentiles for this query
            query_path_counts = list(path_count_data[query.name].values())
            if query_path_counts:
                import numpy as np
                p90 = int(np.percentile(query_path_counts, 90))
                p95 = int(np.percentile(query_path_counts, 95))
                p99 = int(np.percentile(query_path_counts, 99))

                print(f"  Path count percentiles: 90th={p90}, 95th={p95}, 99th={p99}")

                # Create query-specific path count filters
                if query_individual_filters is not None:
                    query_individual_filters[f"max_path_count_p90"] = create_max_path_count_filter(
                        path_count_data[query.name], p90
                    )
                    query_individual_filters[f"max_path_count_p95"] = create_max_path_count_filter(
                        path_count_data[query.name], p95
                    )
                    query_individual_filters[f"max_path_count_p99"] = create_max_path_count_filter(
                        path_count_data[query.name], p99
                    )

        results = evaluate_query(
            query,
            args.paths_dir,
            individual_filters=query_individual_filters,
            filter_strategies=query_filter_strategies
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
