"""Node normalization using the Node Normalizer API."""
import requests
from typing import List, Dict, Optional, Set
from functools import lru_cache


# Node Normalizer API endpoint
NODE_NORMALIZER_URL = "https://nodenormalization-sri.renci.org/get_normalized_nodes"


def normalize_curies(curies: List[str]) -> Dict[str, Optional[str]]:
    """
    Normalize a list of CURIEs to their preferred identifiers.

    Uses the Node Normalizer API with both conflation options set to True.
    Returns a mapping from input CURIE to its preferred (clique leader) identifier.

    Args:
        curies: List of CURIEs to normalize

    Returns:
        Dictionary mapping input CURIE to preferred CURIE.
        If a CURIE cannot be normalized, it maps to None.

    Example:
        >>> normalize_curies(["MESH:D014867", "CHEBI:15377"])
        {
            "MESH:D014867": "CHEBI:15377",
            "CHEBI:15377": "CHEBI:15377"
        }
    """
    if not curies:
        return {}

    # Prepare request payload
    payload = {
        "curies": curies,
        "conflate": True,
        "drug_chemical_conflate": True
    }

    try:
        response = requests.post(NODE_NORMALIZER_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        # Let it fail - don't hide the error
        raise RuntimeError(f"Node normalization API request failed: {e}")

    # Extract preferred identifiers
    result = {}
    for curie in curies:
        if curie in data and data[curie] is not None:
            preferred_id = data[curie].get("id", {}).get("identifier")
            result[curie] = preferred_id
        else:
            result[curie] = None

    return result


@lru_cache(maxsize=10000)
def normalize_curie(curie: str) -> Optional[str]:
    """
    Normalize a single CURIE to its preferred identifier.

    This function is cached to avoid repeated API calls for the same CURIE.

    Args:
        curie: CURIE to normalize

    Returns:
        Preferred CURIE identifier, or None if normalization fails
    """
    result = normalize_curies([curie])
    return result.get(curie)


def normalize_curie_set(curies: Set[str]) -> Dict[str, Optional[str]]:
    """
    Normalize a set of CURIEs efficiently.

    Batches the API call for better performance.

    Args:
        curies: Set of CURIEs to normalize

    Returns:
        Dictionary mapping input CURIE to preferred CURIE
    """
    return normalize_curies(list(curies))


def get_normalized_expected_nodes(query) -> Set[str]:
    """
    Get all normalized (preferred) CURIEs for a query's expected nodes.

    Args:
        query: Query object with expected_nodes dict

    Returns:
        Set of preferred CURIEs for all expected nodes
    """
    # Collect all expected node CURIEs
    all_curies = []
    for curies_list in query.expected_nodes.values():
        all_curies.extend(curies_list)

    # Normalize them
    normalized = normalize_curies(all_curies)

    # Return set of preferred identifiers (excluding None)
    return {preferred for preferred in normalized.values() if preferred is not None}


def normalize_path_curies(path_curies: List[str]) -> List[Optional[str]]:
    """
    Normalize a path's CURIEs to their preferred identifiers.

    Maintains the order of the path.

    Args:
        path_curies: List of CURIEs in path order

    Returns:
        List of preferred CURIEs in same order (None if normalization fails)
    """
    normalized = normalize_curies(path_curies)
    return [normalized.get(curie) for curie in path_curies]
