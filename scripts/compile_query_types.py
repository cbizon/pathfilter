#!/usr/bin/env python3
"""
Compile a query type list based on biolink classes of start and end nodes.

For each query, determine the biolink types of the start and end nodes,
and create a mapping of query_id -> (start_type, end_type).
"""

import json
import sys
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional


NODE_NORMALIZER_URL = "https://nodenormalization-sri.renci.org/get_normalized_nodes"


def get_biolink_types(curies: List[str]) -> Dict[str, Optional[str]]:
    """
    Get the most specific biolink type for each CURIE.

    Args:
        curies: List of CURIEs to look up

    Returns:
        Dictionary mapping CURIE to its most specific biolink type
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
        raise RuntimeError(f"Node normalization API request failed: {e}")

    # Extract the most specific type (first in the type list)
    result = {}
    for curie in curies:
        if curie in data and data[curie] is not None:
            types = data[curie].get("type", [])
            if types:
                # Get the most specific type (first in list)
                # Remove 'biolink:' prefix for cleaner output
                most_specific_type = types[0].replace("biolink:", "")
                result[curie] = most_specific_type
            else:
                result[curie] = None
        else:
            result[curie] = None

    return result


def compile_query_types(queries_file: Path) -> List[Tuple[str, str, str, str]]:
    """
    Compile query types from normalized queries file.

    Args:
        queries_file: Path to queries_normalized.json

    Returns:
        List of tuples: (query_name, query_label, start_type, end_type)
    """
    # Load queries
    with open(queries_file) as f:
        queries = json.load(f)

    # Collect all unique CURIEs that need type lookup
    curie_to_query = {}
    for query in queries:
        # Use first start CURIE
        if query["start_curies"]:
            start_curie = query["start_curies"][0]
            curie_to_query[start_curie] = query["name"]

        # Use first end CURIE
        if query["end_curies"]:
            end_curie = query["end_curies"][0]
            curie_to_query[end_curie] = query["name"]

    # Get types for all CURIEs in one batch
    all_curies = list(curie_to_query.keys())
    print(f"Looking up biolink types for {len(all_curies)} CURIEs...", file=sys.stderr)
    curie_types = get_biolink_types(all_curies)

    # Build result list
    results = []
    for query in queries:
        query_name = query["name"]

        # Get start and end types
        start_curie = query["start_curies"][0] if query["start_curies"] else None
        end_curie = query["end_curies"][0] if query["end_curies"] else None

        start_type = curie_types.get(start_curie) if start_curie else "Unknown"
        end_type = curie_types.get(end_curie) if end_curie else "Unknown"

        # Create descriptive label
        query_label = f"{query['start_label']} → {query['end_label']}"

        results.append((query_name, query_label, start_type or "Unknown", end_type or "Unknown"))

    return results


def main():
    # Find queries file
    queries_file = Path("normalized_input_data/queries_normalized.json")

    if not queries_file.exists():
        print(f"Error: {queries_file} not found", file=sys.stderr)
        print("Run: uv run python scripts/normalize_input_data.py", file=sys.stderr)
        sys.exit(1)

    # Compile query types
    query_types = compile_query_types(queries_file)

    # Output as TSV
    print("Query\tQuery_Label\tStart_Type\tEnd_Type")
    for query_name, query_label, start_type, end_type in sorted(query_types):
        print(f"{query_name}\t{query_label}\t{start_type}\t{end_type}")

    # Summary by type pair
    print("\n# Query Type Summary", file=sys.stderr)
    type_counts = {}
    for _, _, start_type, end_type in query_types:
        type_pair = f"({start_type}, {end_type})"
        type_counts[type_pair] = type_counts.get(type_pair, 0) + 1

    print("Type_Pair\tCount", file=sys.stderr)
    for type_pair, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"{type_pair}\t{count}", file=sys.stderr)


if __name__ == "__main__":
    main()
