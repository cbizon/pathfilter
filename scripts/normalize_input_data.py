#!/usr/bin/env python3
"""
Normalize all CURIEs in input data files.

This script reads the original input_data/ files and creates normalized versions
in normalized_input_data/. Run this once before evaluation to avoid repeated
API calls during analysis.

Usage:
    uv run python scripts/normalize_input_data.py
"""
import sys
from pathlib import Path
import pandas as pd
from openpyxl import load_workbook
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pathfilter.normalization import normalize_curies
from pathfilter.curie_utils import parse_concatenated_curies, parse_path_curies


def load_query_from_ods(excel_file: str, sheet_name: str) -> dict:
    """
    Load a single query definition from a sheet in the ODS file.

    This is the authoritative ODF parsing logic moved from query_loader.py.

    Returns:
        Dictionary with query data structure
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

    return {
        "name": sheet_name,
        "start_label": start_label,
        "start_curies": start_curies,
        "end_label": end_label,
        "end_curies": end_curies,
        "expected_nodes": expected_nodes
    }


def normalize_queries_to_json(input_file: str, output_file: str):
    """
    Load queries from ODS file, normalize all CURIEs, and save to JSON.

    This replaces the broken ODF file writing approach.
    """
    print(f"Processing query file: {input_file}")

    # Get all query sheets
    xls = pd.ExcelFile(input_file, engine='odf')
    query_sheets = [s for s in xls.sheet_names if s.startswith('PFTQ-')]

    print(f"  Found {len(query_sheets)} query sheets")

    normalized_queries = []

    for sheet_name in query_sheets:
        try:
            print(f"  Processing sheet: {sheet_name}")

            # Load query using the ODF parsing logic
            query_data = load_query_from_ods(input_file, sheet_name)

            # Only process queries with complete information
            if not query_data['expected_nodes'] or not query_data['start_curies'] or not query_data['end_curies']:
                print(f"    Skipping - incomplete query definition")
                continue

            # Collect all CURIEs to normalize
            all_curies = []
            all_curies.extend(query_data['start_curies'])
            all_curies.extend(query_data['end_curies'])
            for curies_list in query_data['expected_nodes'].values():
                all_curies.extend(curies_list)

            print(f"    Normalizing {len(all_curies)} CURIEs...")

            # Normalize them
            normalized = normalize_curies(all_curies)

            # Count changes
            changes = sum(1 for c, n in normalized.items() if c != n and n is not None)
            print(f"    Changed: {changes}/{len(all_curies)}")

            # Apply normalization to query data
            query_data['start_curies'] = [normalized.get(c, c) for c in query_data['start_curies'] if normalized.get(c) is not None]
            query_data['end_curies'] = [normalized.get(c, c) for c in query_data['end_curies'] if normalized.get(c) is not None]

            normalized_expected = {}
            for label, curies in query_data['expected_nodes'].items():
                normalized_curies = [normalized.get(c, c) for c in curies if normalized.get(c) is not None]
                if normalized_curies:
                    normalized_expected[label] = normalized_curies
            query_data['expected_nodes'] = normalized_expected

            normalized_queries.append(query_data)

        except Exception as e:
            print(f"    Warning: Could not load query from sheet {sheet_name}: {e}")
            continue

    # Write to JSON
    import json
    with open(output_file, 'w') as f:
        json.dump(normalized_queries, f, indent=2)

    print(f"  Wrote {len(normalized_queries)} normalized queries to {output_file}")


def normalize_path_file(input_file: str, output_file: str):
    """
    Normalize CURIEs in a path xlsx file.

    Updates the path_curies column with normalized CURIEs.
    """
    print(f"Processing: {Path(input_file).name}")

    # Load the Excel file
    df = pd.read_excel(input_file)

    # Collect all unique CURIEs from path_curies column
    all_curies = set()
    for path_curie_str in df['path_curies']:
        curies = parse_path_curies(str(path_curie_str))
        all_curies.update(curies)

    print(f"  Total unique CURIEs: {len(all_curies)}")

    # Normalize all CURIEs in one batch
    print(f"  Normalizing...")
    normalized = normalize_curies(list(all_curies))

    # Count changes
    changes = sum(1 for c, n in normalized.items() if c != n and n is not None)
    print(f"  Changed: {changes}/{len(all_curies)} ({changes/len(all_curies)*100:.1f}%)")

    # Update path_curies column
    def normalize_path_curies_str(path_curie_str):
        curies = parse_path_curies(str(path_curie_str))
        normalized_curies = [normalized.get(c, c) for c in curies if normalized.get(c) is not None]
        return ' --> '.join(normalized_curies)

    df['path_curies'] = df['path_curies'].apply(normalize_path_curies_str)

    # Save to output
    df.to_excel(output_file, index=False)
    print(f"  Saved to: {Path(output_file).name}")


def main():
    """Main normalization workflow."""
    # Setup paths
    project_root = Path(__file__).parent.parent
    input_dir = project_root / "input_data"
    output_dir = project_root / "normalized_input_data"

    # Check input exists
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        print("Please ensure input_data/ directory exists with query and path files.")
        return 1

    # Create output directory
    output_dir.mkdir(exist_ok=True)
    (output_dir / "paths").mkdir(exist_ok=True)

    print("=" * 70)
    print("NORMALIZING INPUT DATA")
    print("=" * 70)
    print()

    # 1. Normalize query file to JSON
    query_input = input_dir / "Pathfinder Test Queries.xlsx.ods"
    query_output = output_dir / "queries_normalized.json"

    if query_input.exists():
        print("Normalizing query definitions...")
        print()
        normalize_queries_to_json(str(query_input), str(query_output))
        print()
    else:
        print(f"Error: Query file not found: {query_input}")
        return 1

    # 2. Normalize all path files
    paths_input = input_dir / "paths"
    paths_output = output_dir / "paths"

    if not paths_input.exists():
        print(f"Error: Paths directory not found: {paths_input}")
        return 1

    print("Normalizing path files...")
    print()

    # Get all xlsx files
    xlsx_files = list(paths_input.glob("*.xlsx"))
    print(f"Found {len(xlsx_files)} path files to normalize")
    print()

    for i, input_file in enumerate(xlsx_files, 1):
        print(f"[{i}/{len(xlsx_files)}] ", end="")
        output_file = paths_output / input_file.name

        try:
            normalize_path_file(str(input_file), str(output_file))
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        print()

    print("=" * 70)
    print("NORMALIZATION COMPLETE")
    print("=" * 70)
    print()
    print(f"Normalized data written to: {output_dir}")
    print(f"  - Query definitions: {query_output}")
    print(f"  - Path files: {paths_output}/")
    print()
    print("Query loader will automatically use normalized data.")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
