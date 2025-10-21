"""Utilities for parsing and handling CURIEs (Compact URIs)."""
import re
from typing import List


def is_valid_curie(curie: str) -> bool:
    """
    Validate that a string is a properly formatted CURIE.

    A valid CURIE must:
    - Contain exactly one colon
    - Have a non-empty prefix (before colon)
    - Have a non-empty ID (after colon)
    - Prefix starts with uppercase letter
    - Only contain alphanumeric, dots, underscores, hyphens

    Args:
        curie: String to validate

    Returns:
        True if valid CURIE, False otherwise
    """
    if not curie or not isinstance(curie, str):
        return False

    # Must contain exactly one colon
    if curie.count(':') != 1:
        return False

    prefix, id_part = curie.split(':')

    # Prefix must be non-empty and start with uppercase
    if not prefix or not prefix[0].isupper():
        return False

    # ID part must be non-empty
    if not id_part:
        return False

    # Both parts should only contain valid CURIE characters
    valid_pattern = r'^[A-Za-z0-9._-]+$'
    if not re.match(valid_pattern, prefix) or not re.match(valid_pattern, id_part):
        return False

    return True


def parse_concatenated_curies(curie_string: str) -> List[str]:
    """
    Parse a string containing one or more concatenated CURIEs.

    CURIEs follow the pattern PREFIX:ID where:
    - PREFIX is alphanumeric with possible dots, underscores, hyphens
    - ID is alphanumeric with possible dots, underscores, hyphens
    - CURIEs are concatenated without delimiters, so we split when we see a new PREFIX
    - Annotations (text after " -> ") are stripped before parsing

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

        >>> parse_concatenated_curies("NCBIGene:2739 -> human geneAraPort:AT3G14420")
        ['NCBIGene:2739', 'AraPort:AT3G14420']

    Args:
        curie_string: String containing one or more CURIEs (possibly with annotations)

    Returns:
        List of individual CURIE strings (validated)
    """
    if not curie_string or curie_string.strip() == '' or str(curie_string) == 'nan':
        return []

    curie_string = str(curie_string).strip()

    # Strip annotations: remove any text after " -> " markers
    # This handles cases like "NCBIGene:2739 -> human geneAraPort:AT3G14420 -> Arabidopsis gene"
    if ' -> ' in curie_string:
        # Pattern: CURIE -> text CURIE -> text...
        # After splitting on " -> ", parts contain: [CURIE, text+CURIE, text+CURIE, text]
        # We need to extract ALL CURIEs from all parts using regex
        parts = curie_string.split(' -> ')

        # Extract all CURIEs from each part
        all_curies = []
        # Match CURIEs that are preceded by start, whitespace, lowercase letter, or digit
        # Lowercase letter handles "geneAraPort:123" -> extracts "AraPort:123"
        # Use lookbehind for lowercase but don't include it in match
        curie_pattern = r'(?:^|(?<=[\s\da-z]))([A-Z][A-Za-z0-9._-]*:[A-Za-z0-9._-]+)'
        for part in parts:
            # Find all CURIEs in this part
            matches = re.finditer(curie_pattern, part)
            # Extract the capturing group (group 1)
            curies_in_part = [m.group(1) for m in matches]

            # Filter out false positives like "RNFT2NCBIGene:123"
            # A valid CURIE prefix shouldn't contain multiple runs of uppercase+digits
            # If the prefix looks like it has concatenated words (e.g., "RNFT2NCBIGene"),
            # it's probably "text" + "RealPrefix", so we should extract just the real prefix part
            filtered_curies = []
            for curie in curies_in_part:
                # If this looks like it might be concatenated annotation + CURIE,
                # try to extract just the CURIE part
                # Pattern: look for a common CURIE prefix at the end
                # Common prefixes: NCBIGene, MONDO, CHEBI, UMLS, GO, PR, UniProtKB, ENSEMBL, etc.
                # Check if the curie prefix contains a known prefix
                known_prefixes = ['NCBIGene', 'MONDO', 'CHEBI', 'UMLS', 'GO', 'PR', 'UniProtKB', 'ENSEMBL', 'NCIT', 'AraPort']
                prefix = curie.split(':')[0]

                # If the prefix ends with a known prefix, extract just that part
                matched_known = False
                for known in known_prefixes:
                    if prefix.endswith(known) and len(prefix) > len(known):
                        # Extract just the known prefix part
                        real_curie = known + ':' + curie.split(':')[1]
                        filtered_curies.append(real_curie)
                        matched_known = True
                        break

                if not matched_known:
                    # No known prefix found at end, keep as-is if it passes validation
                    filtered_curies.append(curie)

            all_curies.extend(filtered_curies)

        # If we found CURIEs by stripping annotations, validate and return them
        if all_curies:
            validated = [c for c in all_curies if is_valid_curie(c)]
            return validated

    # Pattern for a CURIE: PREFIX:ID
    # PREFIX: uppercase letter followed by letters/numbers/dots/underscores/hyphens (non-greedy)
    # ID: anything that's not an uppercase letter starting a new prefix
    # We use a lookahead to stop before the next CURIE starts
    # A new CURIE starts with: uppercase letter + more word chars + colon
    curie_pattern = r'[A-Z][A-Za-z0-9._-]*:[A-Za-z0-9._-]+?(?=[A-Z][A-Za-z]*:|$)'

    matches = re.findall(curie_pattern, curie_string)

    # Validate all matches
    validated_matches = [m for m in matches if is_valid_curie(m)]

    return validated_matches


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
