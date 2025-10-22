"""Evaluation metrics for path filtering."""
from dataclasses import dataclass
from typing import List, Set, Optional
from pathfilter.path_loader import Path
from pathfilter.filters import FilterFunction, apply_filters
from pathfilter.matching import (
    count_paths_with_expected_nodes,
    get_expected_nodes_found_in_paths
)


@dataclass
class FilterMetrics:
    """Metrics for evaluating a filter strategy on a set of paths."""

    filter_name: str  # Name of the filter strategy
    total_paths_before: int  # Total paths before filtering
    total_paths_after: int  # Total paths after filtering
    expected_paths_before: int  # Paths with expected nodes before filtering
    expected_paths_after: int  # Paths with expected nodes after filtering
    expected_nodes_found_before: int  # Number of unique expected nodes found before
    expected_nodes_found_after: int  # Number of unique expected nodes found after

    @property
    def recall(self) -> float:
        """
        Recall: fraction of expected paths that were kept.

        recall = expected_paths_after / expected_paths_before
        """
        if self.expected_paths_before == 0:
            return 0.0
        return self.expected_paths_after / self.expected_paths_before

    @property
    def precision_before(self) -> float:
        """
        Precision before filtering: fraction of paths with expected nodes.

        precision = expected_paths / total_paths
        """
        if self.total_paths_before == 0:
            return 0.0
        return self.expected_paths_before / self.total_paths_before

    @property
    def precision_after(self) -> float:
        """
        Precision after filtering: fraction of paths with expected nodes.

        precision = expected_paths / total_paths
        """
        if self.total_paths_after == 0:
            return 0.0
        return self.expected_paths_after / self.total_paths_after

    @property
    def enrichment(self) -> float:
        """
        Enrichment: improvement in precision from filtering.

        enrichment = precision_after / precision_before

        Values > 1.0 indicate filtering improved precision.
        """
        if self.precision_before == 0:
            return 0.0
        return self.precision_after / self.precision_before

    @property
    def retention_rate(self) -> float:
        """
        Retention rate: fraction of paths kept after filtering.

        retention = total_paths_after / total_paths_before
        """
        if self.total_paths_before == 0:
            return 0.0
        return self.total_paths_after / self.total_paths_before

    @property
    def expected_nodes_recall(self) -> float:
        """
        Recall for expected nodes: fraction of unique expected nodes still found.

        node_recall = expected_nodes_found_after / expected_nodes_found_before
        """
        if self.expected_nodes_found_before == 0:
            return 0.0
        return self.expected_nodes_found_after / self.expected_nodes_found_before


def evaluate_filter_strategy(
    paths: List[Path],
    expected_nodes: Set[str],
    filters: List[FilterFunction],
    strategy_name: str
) -> FilterMetrics:
    """
    Evaluate a filter strategy on a set of paths.

    ASSUMES: Paths and expected_nodes contain pre-normalized CURIEs.

    Args:
        paths: List of Path objects to evaluate (pre-normalized)
        expected_nodes: Set of expected node CURIEs (pre-normalized)
        filters: List of filter functions to apply
        strategy_name: Name for this filter strategy

    Returns:
        FilterMetrics with evaluation results
    """
    # Metrics before filtering
    total_before = len(paths)
    expected_before = count_paths_with_expected_nodes(paths, expected_nodes)
    nodes_before = len(get_expected_nodes_found_in_paths(paths, expected_nodes))

    # Apply filters
    filtered_paths = apply_filters(paths, filters)

    # Metrics after filtering
    total_after = len(filtered_paths)
    expected_after = count_paths_with_expected_nodes(filtered_paths, expected_nodes)
    nodes_after = len(get_expected_nodes_found_in_paths(filtered_paths, expected_nodes))

    return FilterMetrics(
        filter_name=strategy_name,
        total_paths_before=total_before,
        total_paths_after=total_after,
        expected_paths_before=expected_before,
        expected_paths_after=expected_after,
        expected_nodes_found_before=nodes_before,
        expected_nodes_found_after=nodes_after
    )


def evaluate_multiple_strategies(
    paths: List[Path],
    expected_nodes: Set[str],
    individual_filters: dict[str, FilterFunction],
    max_combination_size: Optional[int] = None
) -> List[FilterMetrics]:
    """
    Evaluate all combinations of filters using optimized caching approach.

    Instead of re-applying filters for every combination, this function:
    1. Applies each filter once, caching which paths pass
    2. Computes combinations using set intersections (fast!)

    This is dramatically faster: O(N*F) instead of O(N*F*C) where:
    - N = number of paths
    - F = number of individual filters
    - C = number of combinations (exponential in F)

    ASSUMES: Paths and expected_nodes contain pre-normalized CURIEs.

    Args:
        paths: List of Path objects to evaluate (pre-normalized)
        expected_nodes: Set of expected node CURIEs (pre-normalized)
        individual_filters: Dict of filter_name -> filter_function
        max_combination_size: Maximum filters in a combination (None = all)

    Returns:
        List of FilterMetrics, one for each combination
    """
    from itertools import combinations as combo_generator

    # Step 1: Apply each filter once and cache passing paths
    filter_cache = {}
    for filter_name, filter_func in individual_filters.items():
        passing_paths = set()
        for i, path in enumerate(paths):
            if filter_func(path):
                passing_paths.add(i)  # Store index, not object
        filter_cache[filter_name] = passing_paths

    # Baseline metrics (no filtering)
    total_before = len(paths)
    expected_before = count_paths_with_expected_nodes(paths, expected_nodes)
    nodes_before = len(get_expected_nodes_found_in_paths(paths, expected_nodes))

    results = []

    # Baseline: no filtering
    results.append(FilterMetrics(
        filter_name="none",
        total_paths_before=total_before,
        total_paths_after=total_before,
        expected_paths_before=expected_before,
        expected_paths_after=expected_before,
        expected_nodes_found_before=nodes_before,
        expected_nodes_found_after=nodes_before
    ))

    # Step 2: Generate all combinations using set intersections
    filter_names = list(individual_filters.keys())
    max_size = max_combination_size if max_combination_size is not None else len(filter_names)

    # Singles, pairs, triples, etc.
    for n in range(1, max_size + 1):
        for combo in combo_generator(filter_names, n):
            # Intersection of all filters in this combination
            passing_indices = filter_cache[combo[0]].copy()
            for filter_name in combo[1:]:
                passing_indices &= filter_cache[filter_name]

            # Build list of filtered paths
            filtered_paths = [paths[i] for i in passing_indices]

            # Calculate metrics
            total_after = len(filtered_paths)
            expected_after = count_paths_with_expected_nodes(filtered_paths, expected_nodes)
            nodes_after = len(get_expected_nodes_found_in_paths(filtered_paths, expected_nodes))

            strategy_name = "+".join(combo)
            results.append(FilterMetrics(
                filter_name=strategy_name,
                total_paths_before=total_before,
                total_paths_after=total_after,
                expected_paths_before=expected_before,
                expected_paths_after=expected_after,
                expected_nodes_found_before=nodes_before,
                expected_nodes_found_after=nodes_after
            ))

    return results


def format_metrics_table(metrics_list: List[FilterMetrics]) -> str:
    """
    Format a list of metrics as a readable table.

    Args:
        metrics_list: List of FilterMetrics to format

    Returns:
        String with formatted table
    """
    # Header
    header = (
        f"{'Strategy':<20} "
        f"{'Paths':<12} "
        f"{'Expected':<12} "
        f"{'Recall':<8} "
        f"{'Precision':<10} "
        f"{'Enrichment':<10} "
        f"{'Nodes':<8}"
    )
    separator = "-" * len(header)

    lines = [header, separator]

    for m in metrics_list:
        line = (
            f"{m.filter_name:<20} "
            f"{m.total_paths_after:>6}/{m.total_paths_before:<5} "
            f"{m.expected_paths_after:>6}/{m.expected_paths_before:<5} "
            f"{m.recall:>7.2%} "
            f"{m.precision_after:>9.2%} "
            f"{m.enrichment:>9.2f}x "
            f"{m.expected_nodes_found_after:>3}/{m.expected_nodes_found_before:<3}"
        )
        lines.append(line)

    return "\n".join(lines)
