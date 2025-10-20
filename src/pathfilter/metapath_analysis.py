"""Metapath enrichment analysis for path evaluation.

This module analyzes how different structural patterns (metapaths) in knowledge graph
paths correlate with finding expected nodes.
"""
import ast
from dataclasses import dataclass
from typing import List, Set, Dict, Tuple
from collections import defaultdict
from pathfilter.path_loader import Path
from pathfilter.matching import does_path_contain_expected_node


@dataclass
class MetapathStats:
    """Statistics for a single metapath in a query."""
    metapath: str
    total_paths: int
    hit_paths: int
    precision: float
    enrichment: float
    frequency: float


def parse_metapaths_from_string(metapaths_str: str) -> List[str]:
    """
    Parse metapaths from the string representation in xlsx files.

    The metapaths column contains a string representation of a Python list.
    Examples:
        "['metapath1']"
        "['metapath1', 'metapath2']"

    Args:
        metapaths_str: String representation of metapath list from xlsx

    Returns:
        List of metapath strings
    """
    try:
        # Use ast.literal_eval to safely parse the string representation
        metapaths = ast.literal_eval(metapaths_str)
        if isinstance(metapaths, list):
            return metapaths
        else:
            # If it's not a list, wrap it
            return [str(metapaths)]
    except (ValueError, SyntaxError):
        # If parsing fails, return empty list
        return []


def expand_paths_with_metapaths(paths: List[Path]) -> List[Tuple[Path, str]]:
    """
    Expand paths to (path, metapath) tuples.

    Each path may have multiple metapaths. This function expands them so each
    (path, metapath) combination is represented separately.

    Args:
        paths: List of Path objects

    Returns:
        List of (Path, metapath_string) tuples
    """
    expanded = []
    for path in paths:
        metapaths = parse_metapaths_from_string(path.metapaths)
        for metapath in metapaths:
            expanded.append((path, metapath))
    return expanded


def calculate_metapath_enrichment(
    paths: List[Path],
    expected_nodes: Set[str],
    query_id: str
) -> List[MetapathStats]:
    """
    Calculate enrichment statistics for each metapath in the query.

    Args:
        paths: List of Path objects from the query
        expected_nodes: Set of pre-normalized expected node CURIEs
        query_id: Query identifier (for reference)

    Returns:
        List of MetapathStats objects, one per unique metapath
    """
    # Expand paths to (path, metapath) tuples
    path_metapath_pairs = expand_paths_with_metapaths(paths)

    # Calculate overall query statistics (baseline)
    total_paths_in_query = len(paths)
    total_hits_in_query = sum(
        1 for path in paths
        if does_path_contain_expected_node(path, expected_nodes)
    )
    overall_precision = (
        total_hits_in_query / total_paths_in_query
        if total_paths_in_query > 0
        else 0.0
    )

    # Group by metapath and count
    metapath_total: Dict[str, int] = defaultdict(int)
    metapath_hits: Dict[str, int] = defaultdict(int)

    for path, metapath in path_metapath_pairs:
        metapath_total[metapath] += 1
        if does_path_contain_expected_node(path, expected_nodes):
            metapath_hits[metapath] += 1

    # Calculate statistics for each metapath
    stats = []
    for metapath in sorted(metapath_total.keys()):
        total = metapath_total[metapath]
        hits = metapath_hits[metapath]

        precision = hits / total if total > 0 else 0.0
        enrichment = precision / overall_precision if overall_precision > 0 else 0.0
        frequency = total / total_paths_in_query if total_paths_in_query > 0 else 0.0

        stats.append(MetapathStats(
            metapath=metapath,
            total_paths=total,
            hit_paths=hits,
            precision=precision,
            enrichment=enrichment,
            frequency=frequency
        ))

    return stats


def analyze_all_queries_metapaths(
    query_data: Dict[str, Tuple[List[Path], Set[str]]]
) -> List[Dict[str, any]]:
    """
    Analyze metapath enrichment for all queries.

    Args:
        query_data: Dict mapping query_id to (paths, expected_nodes) tuple

    Returns:
        List of dicts with columns: query_id, metapath, total_paths, hit_paths,
        precision, enrichment, frequency
    """
    results = []

    for query_id, (paths, expected_nodes) in query_data.items():
        stats_list = calculate_metapath_enrichment(paths, expected_nodes, query_id)

        for stats in stats_list:
            results.append({
                'query_id': query_id,
                'metapath': stats.metapath,
                'total_paths': stats.total_paths,
                'hit_paths': stats.hit_paths,
                'precision': stats.precision,
                'enrichment': stats.enrichment,
                'frequency': stats.frequency
            })

    return results
