"""Path filtering functions.

Each filter function takes a Path object and returns True if the path should be kept,
False if it should be filtered out.
"""
from pathfilter.path_loader import Path
from typing import Callable, List


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


# Pre-defined filter sets
DEFAULT_FILTERS = [no_dupe_types, no_expression, no_related_to]
STRICT_FILTERS = [no_dupe_types, no_expression, no_related_to, no_end_pheno]
NO_FILTERS = [all_paths]
