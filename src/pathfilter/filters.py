"""Path filtering functions.

Each filter function takes a Path object and returns True if the path should be kept,
False if it should be filtered out.
"""
from pathfilter.path_loader import Path
from typing import Callable, Dict, List


# Type alias for filter functions
FilterFunction = Callable[[Path], bool]


def no_dupe_types(path: Path) -> bool:
    """
    Filter out paths that have duplicate node types (after normalization).

    Chemical types (ChemicalEntity, SmallMolecule, MolecularMixture, etc.) are
    considered equivalent. Protein and Gene are considered equivalent.

    A valid path should have 4 unique types.

    Args:
        path: Path object to check

    Returns:
        True if path has 4 unique types, False otherwise
    """
    types = path.categories.split(" --> ")
    normalized_types = []

    for tp in types:
        if tp in ["biolink:ChemicalEntity", "biolink:SmallMolecule",
                  "biolink:MolecularMixture", "biolink:ComplexMolecularMixture"]:
            normalized_types.append("biolink:ChemicalEntity")
        elif tp in ["biolink:Protein"]:
            normalized_types.append("biolink:Gene")
        else:
            normalized_types.append(tp)

    n_unique = len(set(normalized_types))
    return n_unique == 4


def no_expression(path: Path) -> bool:
    """
    Filter out paths that use 'expressed_in' predicates.

    Args:
        path: Path object to check

    Returns:
        True if path does not contain expressed_in, False otherwise
    """
    # Check all predicate fields
    predicates = [
        path.first_hop_predicates,
        path.second_hop_predicates,
        path.third_hop_predicates
    ]

    for pred in predicates:
        if "expressed_in" in pred:
            return False

    return True


def no_related_to(path: Path) -> bool:
    """
    Filter out paths that use generic 'related_to' predicates.

    Args:
        path: Path object to check

    Returns:
        True if path does not contain related_to, False otherwise
    """
    # Check all predicate fields
    predicates = [
        path.categories,
        path.first_hop_predicates,
        path.second_hop_predicates,
        path.third_hop_predicates
    ]

    for pred in predicates:
        if "{'biolink:related_to'}" in pred:
            return False

    return True


def no_end_pheno(path: Path) -> bool:
    """
    Filter out paths that end with PhenotypicFeature -> SmallMolecule.

    Args:
        path: Path object to check

    Returns:
        True if path does not end with this pattern, False otherwise
    """
    return not path.categories.endswith("biolink:PhenotypicFeature --> biolink:SmallMolecule")


def no_chemical_start(path: Path) -> bool:
    """
    Filter out paths that start with Disease -> Chemical.

    Args:
        path: Path object to check

    Returns:
        True if path does not start with Disease->Chemical, False otherwise
    """
    starts = [
        "biolink:Disease --> biolink:SmallMolecule",
        "biolink:Disease --> biolink:ChemicalEntity",
        "biolink:Disease --> biolink:MolecularMixture"
    ]

    for start in starts:
        if path.categories.startswith(start):
            return False

    return True


def no_repeat_predicates(path: Path) -> bool:
    """
    Filter out paths that have the same predicate appearing multiple times.

    Args:
        path: Path object to check

    Returns:
        True if all predicates are unique, False if any predicate repeats
    """
    # Collect all predicates from the three hops
    all_predicates = []

    for pred_str in [path.first_hop_predicates, path.second_hop_predicates, path.third_hop_predicates]:
        # pred_str is a string representation of a set like "{'biolink:affects'}"
        # Extract the predicate(s) from the set notation
        # Handle both single predicates and multiple predicates per hop
        if pred_str and pred_str != "set()":
            # Remove set notation and quotes, split on commas
            cleaned = pred_str.strip("{}").replace("'", "").replace('"', '')
            predicates = [p.strip() for p in cleaned.split(',')]
            all_predicates.extend(predicates)

    # Check for duplicates
    return len(all_predicates) == len(set(all_predicates))


def no_abab(path: Path) -> bool:
    """
    Filter out paths with ABAB alternating type patterns.

    An ABAB pattern is when node types alternate back and forth, like:
    Disease -> Gene -> Disease -> Gene

    Type equivalences (treated as same class):
    - Disease and PhenotypicFeature
    - SmallMolecule, ChemicalEntity, and MolecularMixture
    - Gene and Protein

    Args:
        path: Path object to check

    Returns:
        True if path does not have ABAB pattern, False if it does
    """
    types = path.categories.split(" --> ")

    # Must have exactly 4 nodes for ABAB pattern
    if len(types) != 4:
        return True

    # Normalize types according to equivalence classes
    def normalize_type(tp: str) -> str:
        # Disease/PhenotypicFeature equivalence
        if tp in ["biolink:Disease", "biolink:PhenotypicFeature"]:
            return "CLASS_DISEASE"
        # Chemical equivalence
        elif tp in ["biolink:SmallMolecule", "biolink:ChemicalEntity",
                    "biolink:MolecularMixture", "biolink:ComplexMolecularMixture"]:
            return "CLASS_CHEMICAL"
        # Gene/Protein equivalence
        elif tp in ["biolink:Gene", "biolink:Protein"]:
            return "CLASS_GENE"
        else:
            return tp

    normalized = [normalize_type(tp) for tp in types]

    # Check for ABAB pattern: positions 0==2 and 1==3, but 0!=1
    is_abab = (normalized[0] == normalized[2] and
               normalized[1] == normalized[3] and
               normalized[0] != normalized[1])

    # Return True to keep (not ABAB), False to filter (is ABAB)
    return not is_abab


def no_dupe_but_gene(path: Path) -> bool:
    """
    Filter out paths that have duplicate node types, except Gene/Protein duplicates are allowed.

    Chemical types (ChemicalEntity, SmallMolecule, MolecularMixture, etc.) are
    considered equivalent. Protein and Gene are considered equivalent.

    Gene/Protein types are allowed to repeat. All other types must be unique.

    Args:
        path: Path object to check

    Returns:
        True if path has no duplicate non-Gene types, False otherwise
    """
    types = path.categories.split(" --> ")
    normalized_types = []

    for tp in types:
        if tp in ["biolink:ChemicalEntity", "biolink:SmallMolecule",
                  "biolink:MolecularMixture", "biolink:ComplexMolecularMixture"]:
            normalized_types.append("biolink:ChemicalEntity")
        elif tp in ["biolink:Protein"]:
            normalized_types.append("biolink:Gene")
        else:
            normalized_types.append(tp)

    # Filter out Gene types, check if remaining types are unique
    non_gene_types = [t for t in normalized_types if t != "biolink:Gene"]
    n_unique_non_gene = len(set(non_gene_types))

    # All non-gene types must be unique
    return n_unique_non_gene == len(non_gene_types)


def no_nonconsecutive_dupe(path: Path) -> bool:
    """
    Filter out paths where the same node type appears at non-consecutive positions.

    Consecutive duplicates (A→A→B) are allowed, but non-consecutive duplicates
    (A→B→A) are filtered out.

    Chemical types (ChemicalEntity, SmallMolecule, MolecularMixture, etc.) are
    considered equivalent. Protein and Gene are considered equivalent.

    Args:
        path: Path object to check

    Returns:
        True if no type appears at non-consecutive positions, False otherwise
    """
    types = path.categories.split(" --> ")
    normalized_types = []

    for tp in types:
        if tp in ["biolink:ChemicalEntity", "biolink:SmallMolecule",
                  "biolink:MolecularMixture", "biolink:ComplexMolecularMixture"]:
            normalized_types.append("biolink:ChemicalEntity")
        elif tp in ["biolink:Protein"]:
            normalized_types.append("biolink:Gene")
        else:
            normalized_types.append(tp)

    # For each type, check if all occurrences are consecutive
    type_positions = {}  # type -> [positions]
    for i, tp in enumerate(normalized_types):
        if tp not in type_positions:
            type_positions[tp] = []
        type_positions[tp].append(i)

    # Check if all positions for each type are consecutive
    for tp, positions in type_positions.items():
        if len(positions) > 1:
            # Check if positions are consecutive (e.g., [0,1,2] or [1,2])
            for i in range(len(positions) - 1):
                if positions[i+1] - positions[i] != 1:
                    # Non-consecutive positions found
                    return False

    return True


def all_paths(path: Path) -> bool:
    """
    Accept all paths (no filtering).

    Args:
        path: Path object

    Returns:
        Always True
    """
    return True


def apply_filters(paths: List[Path], filters: List[FilterFunction]) -> List[Path]:
    """
    Apply a list of filter functions to paths.

    A path is kept only if ALL filters return True.

    Args:
        paths: List of Path objects
        filters: List of filter functions

    Returns:
        Filtered list of Path objects
    """
    filtered = []

    for path in paths:
        # Path must pass all filters
        passes_all = all(filter_func(path) for filter_func in filters)
        if passes_all:
            filtered.append(path)

    return filtered


# Node characteristic-based filters

def load_node_characteristics(node_degrees_file: str) -> tuple[Dict[str, float], Dict[str, int], Dict[str, Dict[str, int]]]:
    """
    Load information content, node degree, and path count data from TSV file.

    Args:
        node_degrees_file: Path to node characteristics TSV file (e.g., node_path_counts_with_degrees.tsv)

    Returns:
        Tuple of (ic_data, degree_data, path_count_data) where:
        - ic_data: Dictionary mapping node_id to information_content (missing = 100.0)
        - degree_data: Dictionary mapping node_id to node_degree (missing = 0)
        - path_count_data: Dictionary mapping query -> {node_id: path_count} (query-specific)
    """
    import pandas as pd

    ic_data = {}
    degree_data = {}
    path_count_data = {}  # {query: {node_id: count}}
    df = pd.read_csv(node_degrees_file, sep='\t')

    for _, row in df.iterrows():
        node_id = row['CURIE']
        query = row['Query']

        # Information content (global)
        if node_id not in ic_data:
            ic_value = row['Information_content']
            if pd.isna(ic_value) or ic_value == '':
                ic_data[node_id] = 100.0  # Very specific, passes all filters
            else:
                ic_data[node_id] = float(ic_value)

        # Node degree (global)
        if node_id not in degree_data:
            degree_value = row['Node_degree']
            if pd.isna(degree_value) or degree_value == '':
                degree_data[node_id] = 0  # No connections, passes all max_degree filters
            else:
                degree_data[node_id] = int(degree_value)

        # Path count (per query)
        if query not in path_count_data:
            path_count_data[query] = {}

        path_count_value = row['Path_Count']
        if pd.isna(path_count_value) or path_count_value == '':
            path_count_data[query][node_id] = 0
        else:
            path_count_data[query][node_id] = int(path_count_value)

    return ic_data, degree_data, path_count_data


def create_min_ic_filter(ic_data: Dict[str, float], min_ic: float) -> FilterFunction:
    """
    Create a filter that rejects paths containing any INTERMEDIATE node with IC below threshold.

    Only checks intermediate nodes (positions 1 and 2), not start/end nodes.
    Start and end nodes are query-specific, so their IC doesn't help filter.

    Factory function that creates a filter with the IC data in a closure.

    Args:
        ic_data: Dictionary mapping node_id to information_content
        min_ic: Minimum information content threshold

    Returns:
        Filter function that rejects paths with any intermediate node IC < min_ic
    """
    def min_ic_filter(path: Path) -> bool:
        """
        Filter out paths where ANY INTERMEDIATE node has information content below threshold.

        Only checks path.path_curies[1] and path.path_curies[2] (intermediate nodes).
        Nodes not in ic_data are treated as having IC=100.0 (pass all thresholds).

        Args:
            path: Path object to check

        Returns:
            True if all intermediate nodes have IC >= min_ic, False otherwise
        """
        # Only check intermediate nodes (positions 1 and 2)
        for node_id in path.path_curies[1:3]:
            # Default to 100.0 if node not found (assume specific/rare)
            ic_value = ic_data.get(node_id, 100.0)
            if ic_value < min_ic:
                return False
        return True

    # Set a descriptive name for the filter function
    min_ic_filter.__name__ = f"min_ic_{int(min_ic)}"
    return min_ic_filter


def create_max_path_count_filter(path_count_data: Dict[str, int], max_path_count: int) -> FilterFunction:
    """
    Create a filter that rejects paths containing any INTERMEDIATE node with path_count above threshold.

    Only checks intermediate nodes (positions 1 and 2), not start/end nodes.
    Path counts are query-specific, so this filter is created per query.

    Factory function that creates a filter with the path count data in a closure.

    Args:
        path_count_data: Dictionary mapping node_id to path_count for a specific query
        max_path_count: Maximum path count threshold

    Returns:
        Filter function that rejects paths with any intermediate node path_count > max_path_count
    """
    def max_path_count_filter(path: Path) -> bool:
        """
        Filter out paths where ANY INTERMEDIATE node has path_count above threshold.

        Only checks path.path_curies[1] and path.path_curies[2] (intermediate nodes).
        Nodes not in path_count_data are treated as having path_count=0 (pass all thresholds).

        Args:
            path: Path object to check

        Returns:
            True if all intermediate nodes have path_count <= max_path_count, False otherwise
        """
        # Only check intermediate nodes (positions 1 and 2)
        for node_id in path.path_curies[1:3]:
            # Default to 0 if node not found (assume no paths)
            path_count_value = path_count_data.get(node_id, 0)
            if path_count_value > max_path_count:
                return False
        return True

    # Set a descriptive name for the filter function
    max_path_count_filter.__name__ = f"max_path_count_{max_path_count}"
    return max_path_count_filter


def create_max_degree_filter(degree_data: Dict[str, int], max_degree: int) -> FilterFunction:
    """
    Create a filter that rejects paths containing any INTERMEDIATE node with degree above threshold.

    Only checks intermediate nodes (positions 1 and 2), not start/end nodes.
    Start and end nodes are query-specific, so their degree doesn't help filter.

    Factory function that creates a filter with the degree data in a closure.

    Args:
        degree_data: Dictionary mapping node_id to node_degree
        max_degree: Maximum node degree threshold

    Returns:
        Filter function that rejects paths with any intermediate node degree > max_degree
    """
    def max_degree_filter(path: Path) -> bool:
        """
        Filter out paths where ANY INTERMEDIATE node has degree above threshold.

        Only checks path.path_curies[1] and path.path_curies[2] (intermediate nodes).
        Nodes not in degree_data are treated as having degree=0 (pass all thresholds).

        Args:
            path: Path object to check

        Returns:
            True if all intermediate nodes have degree <= max_degree, False otherwise
        """
        # Only check intermediate nodes (positions 1 and 2)
        for node_id in path.path_curies[1:3]:
            # Default to 0 if node not found (assume no connections)
            degree_value = degree_data.get(node_id, 0)
            if degree_value > max_degree:
                return False
        return True

    # Set a descriptive name for the filter function
    max_degree_filter.__name__ = f"max_degree_{max_degree}"
    return max_degree_filter


# Pre-defined filter sets
DEFAULT_FILTERS = [no_dupe_types, no_expression, no_related_to]
STRICT_FILTERS = [no_dupe_types, no_expression, no_related_to, no_end_pheno]
NO_FILTERS = [all_paths]
