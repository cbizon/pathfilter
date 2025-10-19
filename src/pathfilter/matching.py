"""Path matching logic for finding expected nodes in paths."""
from typing import Set, List, Dict, Optional
from pathfilter.path_loader import Path
from pathfilter.normalization import normalize_curies


def does_path_contain_expected_node(
    path: Path,
    normalized_expected_nodes: Set[str],
    normalization_cache: Optional[Dict[str, Optional[str]]] = None
) -> bool:
    """
    Check if a path contains any of the expected nodes.

    Uses normalized (preferred) CURIEs for matching. The path's CURIEs are
    normalized and compared against the normalized expected nodes.

    This function is designed to be enhanced in the future for looser matching
    (e.g., fuzzy matching, substring matching).

    Args:
        path: Path object with path_curies
        normalized_expected_nodes: Set of normalized (preferred) CURIEs for expected nodes
        normalization_cache: Optional dict mapping CURIEs to normalized IDs (for efficiency)

    Returns:
        True if the path contains at least one expected node, False otherwise
    """
    # Check if any path CURIE (when normalized) matches any expected node
    for curie in path.path_curies:
        # Use cache if provided, otherwise normalize
        if normalization_cache is not None:
            norm_curie = normalization_cache.get(curie)
        else:
            # Fall back to individual normalization (inefficient but works)
            norm_result = normalize_curies([curie])
            norm_curie = norm_result.get(curie)

        if norm_curie is not None and norm_curie in normalized_expected_nodes:
            return True

    return False


def filter_paths_with_expected_nodes(
    paths: List[Path],
    normalized_expected_nodes: Set[str]
) -> List[Path]:
    """
    Filter paths to only those containing expected nodes.

    Efficiently batch-normalizes all unique CURIEs from paths before filtering.

    Args:
        paths: List of Path objects
        normalized_expected_nodes: Set of normalized expected node CURIEs

    Returns:
        List of Path objects that contain at least one expected node
    """
    # Collect all unique CURIEs from all paths
    all_curies = set()
    for path in paths:
        all_curies.update(path.path_curies)

    # Batch normalize all CURIEs in one API call
    normalization_cache = normalize_curies(list(all_curies))

    # Filter using the cache
    return [
        path for path in paths
        if does_path_contain_expected_node(path, normalized_expected_nodes, normalization_cache)
    ]


def count_paths_with_expected_nodes(
    paths: List[Path],
    normalized_expected_nodes: Set[str]
) -> int:
    """
    Count how many paths contain expected nodes.

    Efficiently batch-normalizes all unique CURIEs from paths before counting.

    Args:
        paths: List of Path objects
        normalized_expected_nodes: Set of normalized expected node CURIEs

    Returns:
        Number of paths containing at least one expected node
    """
    # Collect all unique CURIEs from all paths
    all_curies = set()
    for path in paths:
        all_curies.update(path.path_curies)

    # Batch normalize all CURIEs in one API call
    normalization_cache = normalize_curies(list(all_curies))

    # Count using the cache
    count = 0
    for path in paths:
        if does_path_contain_expected_node(path, normalized_expected_nodes, normalization_cache):
            count += 1
    return count


def get_expected_nodes_found_in_paths(
    paths: List[Path],
    normalized_expected_nodes: Set[str]
) -> Set[str]:
    """
    Get the set of expected nodes that are actually found in the paths.

    Efficiently batch-normalizes all unique CURIEs from paths before searching.

    Args:
        paths: List of Path objects
        normalized_expected_nodes: Set of normalized expected node CURIEs

    Returns:
        Set of normalized expected node CURIEs that appear in at least one path
    """
    # Collect all unique CURIEs from all paths
    all_curies = set()
    for path in paths:
        all_curies.update(path.path_curies)

    # Batch normalize all CURIEs in one API call
    normalization_cache = normalize_curies(list(all_curies))

    # Find which expected nodes are present
    found_nodes = set()
    for path in paths:
        for curie in path.path_curies:
            norm_curie = normalization_cache.get(curie)
            if norm_curie is not None and norm_curie in normalized_expected_nodes:
                found_nodes.add(norm_curie)

    return found_nodes
