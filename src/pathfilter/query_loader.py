"""Load and parse Pathfinder query definitions from Excel files."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path
import pandas as pd
from pathfilter.curie_utils import parse_concatenated_curies


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


def load_query_from_sheet(excel_file: str, sheet_name: str) -> Query:
    """
    Load a single query definition from a sheet in the Pathfinder Test Queries file.

    Args:
        excel_file: Path to the Pathfinder Test Queries .ods file
        sheet_name: Name of the sheet to load (e.g., "PFTQ-1-c")

    Returns:
        Query object with parsed information

    Raises:
        ValueError: If the sheet format is invalid or required fields are missing
    """
    df = pd.read_excel(excel_file, sheet_name=sheet_name, engine='odf')

    # Extract start node
    start_row = df[df.iloc[:, 0] == 'Start node']
    if len(start_row) == 0:
        raise ValueError(f"No 'Start node' row found in sheet {sheet_name}")

    start_label = str(start_row.iloc[0, 1]).strip()
    start_curies_str = str(start_row.iloc[0, 2]) if len(start_row.iloc[0]) > 2 else ""
    start_curies = parse_concatenated_curies(start_curies_str)

    # Extract end node
    end_row = df[df.iloc[:, 0] == 'End node']
    if len(end_row) == 0:
        raise ValueError(f"No 'End node' row found in sheet {sheet_name}")

    end_label = str(end_row.iloc[0, 1]).strip()
    end_curies_str = str(end_row.iloc[0, 2]) if len(end_row.iloc[0]) > 2 else ""
    end_curies = parse_concatenated_curies(end_curies_str)

    # Extract expected nodes (only rows with CURIEs in column C)
    expected_nodes = {}
    expected_rows = df[df.iloc[:, 0] == 'Expected Node']
    for idx, row in expected_rows.iterrows():
        label = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        curies_str = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else ""
        curies = parse_concatenated_curies(curies_str)

        # Only include if we have CURIEs
        if curies:
            expected_nodes[label] = curies

    return Query(
        name=sheet_name,
        start_label=start_label,
        start_curies=start_curies,
        end_label=end_label,
        end_curies=end_curies,
        expected_nodes=expected_nodes
    )


def get_all_query_sheets(excel_file: str) -> List[str]:
    """
    Get list of all query sheets from the Pathfinder Test Queries file.

    Filters out non-query sheets like '20 TestQueries', 'Notes', 'Testing Evaluation'.

    Args:
        excel_file: Path to the Pathfinder Test Queries .ods file

    Returns:
        List of query sheet names (e.g., ["PFTQ-1-c", "PFTQ-2-i", ...])
    """
    xls = pd.ExcelFile(excel_file, engine='odf')
    all_sheets = xls.sheet_names

    # Filter to sheets that look like queries (start with "PFTQ-")
    query_sheets = [s for s in all_sheets if s.startswith('PFTQ-')]

    return query_sheets


def load_all_queries(excel_file: str) -> List[Query]:
    """
    Load all query definitions from the Pathfinder Test Queries file.

    Only loads queries that have:
    - At least one start CURIE
    - At least one end CURIE
    - At least one expected node with CURIEs

    Args:
        excel_file: Path to the Pathfinder Test Queries .ods file

    Returns:
        List of Query objects
    """
    query_sheets = get_all_query_sheets(excel_file)
    queries = []

    for sheet_name in query_sheets:
        try:
            query = load_query_from_sheet(excel_file, sheet_name)
            # Only include queries with complete information
            if query.expected_nodes and query.start_curies and query.end_curies:
                queries.append(query)
            elif not query.start_curies or not query.end_curies:
                print(f"Warning: Skipping query {sheet_name} - missing start or end CURIEs")
        except Exception as e:
            # Log but don't fail - some sheets might be malformed
            print(f"Warning: Could not load query from sheet {sheet_name}: {e}")

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
