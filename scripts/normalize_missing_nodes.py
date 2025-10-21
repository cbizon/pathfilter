"""Normalize missing expected nodes and output full API responses."""
import json
import csv
from collections import defaultdict
from pathlib import Path
import requests


NODE_NORMALIZER_URL = "https://nodenormalization-sri.renci.org/get_normalized_nodes"


def load_missing_nodes(tsv_path: str) -> dict[str, list[str]]:
    """
    Load missing nodes from TSV file, grouped by query.

    Returns:
        Dictionary mapping query ID to list of CURIEs
    """
    nodes_by_query = defaultdict(list)

    with open(tsv_path, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            query_id = row['Query']
            curie = row['CURIE']
            nodes_by_query[query_id].append(curie)

    return dict(nodes_by_query)


def get_normalization_responses(curies: list[str]) -> dict[str, dict]:
    """
    Get full normalization responses for a list of CURIEs.

    Args:
        curies: List of CURIEs to normalize

    Returns:
        Dictionary mapping CURIE to full API response for that CURIE
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

    return data


def main():
    # Load missing nodes
    missing_nodes_path = Path("missing_expected_nodes.tsv")
    if not missing_nodes_path.exists():
        raise FileNotFoundError(f"Missing nodes file not found: {missing_nodes_path}")

    print(f"Loading missing nodes from {missing_nodes_path}...")
    nodes_by_query = load_missing_nodes(missing_nodes_path)

    # Collect all unique CURIEs
    all_curies = []
    for curies_list in nodes_by_query.values():
        all_curies.extend(curies_list)
    unique_curies = list(set(all_curies))

    print(f"Found {len(unique_curies)} unique CURIEs across {len(nodes_by_query)} queries")

    # Get normalization responses for all CURIEs
    print(f"Normalizing {len(unique_curies)} CURIEs...")
    all_responses = get_normalization_responses(unique_curies)

    # Build output structure: { "PFTQ-..": { CURIE: nodenorm_response } }
    output = {}
    for query_id, curies in nodes_by_query.items():
        output[query_id] = {}
        for curie in curies:
            output[query_id][curie] = all_responses.get(curie)

    # Write output
    output_path = Path("missing_nodes_normalized.json")
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Wrote normalized results to {output_path}")

    # Print summary statistics
    total_curies = sum(len(curies) for curies in nodes_by_query.values())
    normalized_count = sum(
        1 for query_data in output.values()
        for response in query_data.values()
        if response is not None
    )

    print(f"\nSummary:")
    print(f"  Total CURIEs: {total_curies}")
    print(f"  Successfully normalized: {normalized_count}")
    print(f"  Failed to normalize: {total_curies - normalized_count}")


if __name__ == "__main__":
    main()
