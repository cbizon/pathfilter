"""Load and parse path data from xlsx files."""
from dataclasses import dataclass
from typing import List, Optional
import pandas as pd
from pathfilter.curie_utils import parse_path_curies


@dataclass
class Path:
    """Represents a single path between two nodes."""

    path_labels: str  # "asthma -> Artenimol -> ATG12 -> Imatinib"
    path_curies: List[str]  # ["MONDO:0004979", "CHEBI:...", "NCBIGene:...", "CHEBI:31690"]
    num_paths: int
    categories: str  # "biolink:Disease --> biolink:SmallMolecule --> biolink:Gene --> biolink:SmallMolecule"
    first_hop_predicates: str  # "{'biolink:treats_or_applied_or_studied_to_treat'}"
    second_hop_predicates: str
    third_hop_predicates: str
    has_gene: bool
    metapaths: str  # List string representation


def load_paths_from_file(file_path: str) -> List[Path]:
    """
    Load all paths from an xlsx file.

    Args:
        file_path: Path to the xlsx file containing paths

    Returns:
        List of Path objects

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file format is invalid
    """
    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Path file not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Error reading path file {file_path}: {e}")

    # Validate required columns
    required_columns = [
        'path', 'num_paths', 'categories', 'first_hop_predicates',
        'second_hop_predicates', 'third_hop_predicates', 'has_gene',
        'metapaths', 'path_curies'
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    paths = []
    for _, row in df.iterrows():
        # Parse path_curies into list
        path_curies_list = parse_path_curies(str(row['path_curies']))

        path = Path(
            path_labels=str(row['path']),
            path_curies=path_curies_list,
            num_paths=int(row['num_paths']),
            categories=str(row['categories']),
            first_hop_predicates=str(row['first_hop_predicates']),
            second_hop_predicates=str(row['second_hop_predicates']),
            third_hop_predicates=str(row['third_hop_predicates']),
            has_gene=bool(row['has_gene']),
            metapaths=str(row['metapaths'])
        )
        paths.append(path)

    return paths


def load_paths_for_query(query, paths_dir: str) -> Optional[List[Path]]:
    """
    Load paths for a specific query.

    This is a convenience function that combines finding the path file
    and loading the paths.

    Args:
        query: Query object with start/end CURIEs
        paths_dir: Directory containing path xlsx files

    Returns:
        List of Path objects, or None if no path file found
    """
    from pathfilter.query_loader import find_path_file_for_query

    path_file = find_path_file_for_query(query, paths_dir)
    if not path_file:
        return None

    return load_paths_from_file(path_file)
