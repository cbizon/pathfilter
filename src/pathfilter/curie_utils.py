"""Utilities for parsing and handling CURIEs (Compact URIs)."""
import re
from typing import List


def parse_concatenated_curies(curie_string: str) -> List[str]:
    """
    Parse a string containing one or more concatenated CURIEs.

    CURIEs follow the pattern PREFIX:ID where:
    - PREFIX is alphanumeric with possible dots, underscores, hyphens
    - ID is alphanumeric with possible dots, underscores, hyphens
    - CURIEs are concatenated without delimiters, so we split when we see a new PREFIX

    The key insight: A CURIE ID won't start with an uppercase letter followed by more letters.
    When we see that pattern, it's the start of a new PREFIX.

    Examples:
        >>> parse_concatenated_curies("CHEBI:31690")
        ['CHEBI:31690']

        >>> parse_concatenated_curies("MONDO:0004979MONDO:0004784")
        ['MONDO:0004979', 'MONDO:0004784']

        >>> parse_concatenated_curies("CHEBI:18295PR:000049994")
        ['CHEBI:18295', 'PR:000049994']

        >>> parse_concatenated_curies("NCBIGene:3815NCIT:C39712")
        ['NCBIGene:3815', 'NCIT:C39712']

    Args:
        curie_string: String containing one or more CURIEs

    Returns:
        List of individual CURIE strings
    """
    if not curie_string or curie_string.strip() == '' or str(curie_string) == 'nan':
        return []

    curie_string = str(curie_string).strip()

    # Pattern for a CURIE: PREFIX:ID
    # PREFIX: uppercase letter followed by letters/numbers/dots/underscores/hyphens (non-greedy)
    # ID: anything that's not an uppercase letter starting a new prefix
    # We use a lookahead to stop before the next CURIE starts
    # A new CURIE starts with: uppercase letter + more word chars + colon
    curie_pattern = r'[A-Z][A-Za-z0-9._-]*:[A-Za-z0-9._-]+?(?=[A-Z][A-Za-z]*:|$)'

    matches = re.findall(curie_pattern, curie_string)

    # If no matches with the lookahead approach, try simpler split
    if not matches:
        # Fallback: just return as single CURIE if it looks like one
        if ':' in curie_string:
            return [curie_string]
        return []

    return matches


def parse_path_curies(path_curie_string: str) -> List[str]:
    """
    Parse a path_curies string into individual node CURIEs.

    Path curies are separated by ' --> ' (space-arrow-space).

    Example:
        >>> parse_path_curies("CHEBI:15647 --> NCBIGene:100133941 --> NCBIGene:4907 --> UNII:31YO63LBSN")
        ['CHEBI:15647', 'NCBIGene:100133941', 'NCBIGene:4907', 'UNII:31YO63LBSN']

    Args:
        path_curie_string: String with path CURIEs separated by ' --> '

    Returns:
        List of individual CURIE strings
    """
    if not path_curie_string or str(path_curie_string).strip() == '':
        return []

    # Split on the arrow separator
    curies = path_curie_string.split(' --> ')

    # Strip whitespace from each CURIE
    return [c.strip() for c in curies if c.strip()]
