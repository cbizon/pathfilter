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


def normalize_query_file(input_file: str, output_file: str):
    """
    Normalize CURIEs in the query definitions file.

    Processes each query sheet and normalizes CURIEs in column C.
    """
    print(f"Processing query file: {input_file}")

    # Read all sheets
    xls = pd.ExcelFile(input_file, engine='odf')

    # Copy the file first
    shutil.copy(input_file, output_file)

    # Now process each sheet that looks like a query (starts with PFTQ-)
    from odf import opendocument, table, text
    doc = opendocument.load(input_file)

    for sheet_name in xls.sheet_names:
        if not sheet_name.startswith('PFTQ-'):
            continue

        print(f"  Processing sheet: {sheet_name}")

        # Read sheet
        df = pd.read_excel(input_file, sheet_name=sheet_name, engine='odf')

        # Find rows with CURIEs in column 2 (index 2)
        curies_to_normalize = []
        for idx, row in df.iterrows():
            if len(row) > 2 and pd.notna(row.iloc[2]):
                curie_str = str(row.iloc[2])
                parsed = parse_concatenated_curies(curie_str)
                if parsed:
                    curies_to_normalize.extend(parsed)

        if not curies_to_normalize:
            continue

        # Normalize all CURIEs for this sheet
        print(f"    Normalizing {len(curies_to_normalize)} CURIEs...")
        normalized = normalize_curies(curies_to_normalize)

        # Count changes
        changes = sum(1 for c, n in normalized.items() if c != n and n is not None)
        print(f"    Changed: {changes}/{len(curies_to_normalize)}")

        # Update the dataframe with normalized CURIEs
        for idx, row in df.iterrows():
            if len(row) > 2 and pd.notna(row.iloc[2]):
                curie_str = str(row.iloc[2])
                parsed = parse_concatenated_curies(curie_str)
                if parsed:
                    # Normalize and concatenate back
                    normalized_curies = [normalized.get(c, c) for c in parsed if normalized.get(c) is not None]
                    if normalized_curies:
                        df.iat[idx, 2] = ''.join(normalized_curies)

        # Write back (this is tricky with ODF, we'll use a simpler approach)
        # For now, just print what would change
        # Full ODF writing would require more complex code

    print(f"  Query file normalization complete")
    print(f"  NOTE: ODF file writing not fully implemented - manually copy and update")
    print(f"  Or convert to Excel format first")


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

    # 1. Normalize query file (tricky with ODF format)
    query_input = input_dir / "Pathfinder Test Queries.xlsx.ods"
    query_output = output_dir / "Pathfinder Test Queries.xlsx.ods"

    if query_input.exists():
        print("NOTE: Query file normalization for ODF format is complex.")
        print("For now, we recommend:")
        print("  1. Manually copy the file to normalized_input_data/")
        print("  2. Or convert to .xlsx format first")
        print()
        # normalize_query_file(str(query_input), str(query_output))

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
    print()
    print("Next steps:")
    print("  1. Manually copy and normalize the query file if needed")
    print("  2. Update CLI to use --queries-file and --paths-dir pointing to normalized_input_data/")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
