"""Load and parse Pathfinder query definitions from normalized JSON."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path
import json


@dataclass
class Query:
    """Represents a Pathfinder test query with expected results."""

    name: str  # e.g., "PFTQ-1-c"
    start_label: str  # e.g., "imatinib"
    start_curies: List[str]  # e.g., ["CHEBI:31690"]
    end_label: str  # e.g., "asthma"
    end_curies: List[str]  # e.g., ["MONDO:0004979", "MONDO:0004784"]
    expected_nodes: Dict[str, List[str]] = field(default_factory=dict)  # label -> list of CURIEs
    path_file: Optional[str] = None  # path to corresponding xlsx file


def load_all_queries(queries_file: str) -> List[Query]:
    """
    Load all query definitions from normalized JSON file.

    The JSON file is created by scripts/normalize_input_data.py which parses
    the ODS file and normalizes all CURIEs.

    Args:
        queries_file: Path to queries_normalized.json or the ODS file
                      (will auto-detect JSON in same directory)

    Returns:
        List of Query objects with normalized CURIEs
    """
    queries_path = Path(queries_file)

    # If given an ODS file path, look for JSON in same directory
    if queries_path.suffix == '.ods':
        json_path = queries_path.parent / "queries_normalized.json"
        if not json_path.exists():
            raise FileNotFoundError(
                f"Normalized queries file not found: {json_path}\n"
                f"Run: uv run python scripts/normalize_input_data.py"
            )
        queries_path = json_path

    # Load from JSON
    with open(queries_path, 'r') as f:
        queries_data = json.load(f)

    # Convert to Query objects
    queries = []
    for query_dict in queries_data:
        query = Query(
            name=query_dict['name'],
            start_label=query_dict['start_label'],
            start_curies=query_dict['start_curies'],
            end_label=query_dict['end_label'],
            end_curies=query_dict['end_curies'],
            expected_nodes=query_dict['expected_nodes']
        )
        queries.append(query)

    return queries


def find_path_file_for_query(query: Query, paths_dir: str) -> Optional[str]:
    """
    Find the path file corresponding to a query.

    Path files are named {START_CURIE}_to_{END_CURIE}.xlsx where colons are replaced with underscores.

    Args:
        query: Query object
        paths_dir: Directory containing path xlsx files

    Returns:
        Path to the matching xlsx file, or None if not found
    """
    paths_path = Path(paths_dir)

    # Try all combinations of start and end CURIEs
    for start_curie in query.start_curies:
        for end_curie in query.end_curies:
            # Replace colons with underscores for filename
            start_part = start_curie.replace(':', '_')
            end_part = end_curie.replace(':', '_')

            # Try different filename patterns
            patterns = [
                f"{start_part}_to_{end_part}.xlsx",
                f"{start_part}_to_{end_part}_paths.xlsx",
            ]

            for pattern in patterns:
                file_path = paths_path / pattern
                if file_path.exists():
                    return str(file_path)

    return None
