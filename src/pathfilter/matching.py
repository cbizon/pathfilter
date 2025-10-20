"""Path matching logic for pre-normalized data.

This module assumes all CURIEs in paths and expected nodes are already normalized.
No API calls are made - matching is done via simple set operations.
"""
from typing import Set, List
from pathfilter.path_loader import Path


def does_path_contain_expected_node(
    path: Path,
    expected_nodes: Set[str]
) -> bool:
    """
    Check if a path contains any of the expected nodes.

    ASSUMES: Both path.path_curies and expected_nodes contain pre-normalized CURIEs.

    This function is designed to be enhanced in the future for looser matching
    (e.g., fuzzy matching, substring matching).

    Args:
        path: Path object with pre-normalized path_curies
        expected_nodes: Set of pre-normalized expected node CURIEs

    Returns:
        True if the path contains at least one expected node, False otherwise
    """
    # Simple set intersection - no normalization needed!
    for curie in path.path_curies:
        if curie in expected_nodes:
            return True
    return False


def filter_paths_with_expected_nodes(
    paths: List[Path],
    expected_nodes: Set[str]
) -> List[Path]:
    """
    Filter paths to only those containing expected nodes.

    ASSUMES: Data is pre-normalized.

    Args:
        paths: List of Path objects with pre-normalized CURIEs
        expected_nodes: Set of pre-normalized expected node CURIEs

    Returns:
        List of Path objects that contain at least one expected node
    """
    return [
        path for path in paths
        if does_path_contain_expected_node(path, expected_nodes)
    ]


def count_paths_with_expected_nodes(
    paths: List[Path],
    expected_nodes: Set[str]
) -> int:
    """
    Count how many paths contain expected nodes.

    ASSUMES: Data is pre-normalized.

    Args:
        paths: List of Path objects with pre-normalized CURIEs
        expected_nodes: Set of pre-normalized expected node CURIEs

    Returns:
        Number of paths containing at least one expected node
    """
    count = 0
    for path in paths:
        if does_path_contain_expected_node(path, expected_nodes):
            count += 1
    return count


def get_expected_nodes_found_in_paths(
    paths: List[Path],
    expected_nodes: Set[str]
) -> Set[str]:
    """
    Get the set of expected nodes that are actually found in the paths.

    ASSUMES: Data is pre-normalized.

    Args:
        paths: List of Path objects with pre-normalized CURIEs
        expected_nodes: Set of pre-normalized expected node CURIEs

    Returns:
        Set of expected node CURIEs that appear in at least one path
    """
    found_nodes = set()
    for path in paths:
        for curie in path.path_curies:
            if curie in expected_nodes:
                found_nodes.add(curie)
    return found_nodes
