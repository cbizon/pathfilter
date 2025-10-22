#!/usr/bin/env python3
"""
Join node path counts with ROBOKOP node degrees.

Combines path count analysis with graph topology information to understand
whether high-degree nodes (hub nodes) appear more frequently in paths.
"""

import argparse
import pandas as pd


def join_path_counts_with_degrees(
    path_counts_file: str,
    node_degrees_file: str,
    output_file: str,
    missing_nodes_file: str
):
    """
    Join node path counts with node degrees from ROBOKOP graph.

    Args:
        path_counts_file: Path to node_path_counts.tsv
        node_degrees_file: Path to robokop_node_degrees.tsv
        output_file: Path to output TSV file
        missing_nodes_file: Path to output file for expected nodes not in ROBOKOP
    """
    # Read path counts
    print(f"Reading path counts from {path_counts_file}...")
    path_counts = pd.read_csv(path_counts_file, sep='\t')
    print(f"  Loaded {len(path_counts):,} rows")

    # Read node degrees
    print(f"Reading node degrees from {node_degrees_file}...")
    node_degrees = pd.read_csv(node_degrees_file, sep='\t')
    print(f"  Loaded {len(node_degrees):,} nodes")

    # Perform left join (keep all rows from path_counts)
    print("Joining datasets...")
    merged = path_counts.merge(
        node_degrees,
        left_on='CURIE',
        right_on='Node_id',
        how='left'
    )

    # Fill missing values
    merged['Name'] = merged['Name'].fillna('')
    merged['Node_degree'] = merged['Node_degree'].fillna(0).astype(int)
    merged['Information_content'] = merged['Information_content'].fillna(100.0)

    # Drop the redundant Node_id column (same as CURIE)
    if 'Node_id' in merged.columns:
        merged = merged.drop(columns=['Node_id'])

    # Reorder columns for clarity
    columns = [
        'Query', 'CURIE', 'Name', 'Path_Count', 'Hit_Path_Count',
        'Hit_Path_Fraction', 'Node_degree', 'Information_content', 'Is_Expected'
    ]
    merged = merged[columns]

    # Report statistics
    total_nodes = len(merged)
    found_in_robokop = (merged['Node_degree'] > 0).sum()
    not_found = total_nodes - found_in_robokop

    print(f"\nJoin statistics:")
    print(f"  Total nodes in path counts: {total_nodes:,}")
    print(f"  Found in ROBOKOP: {found_in_robokop:,} ({100*found_in_robokop/total_nodes:.1f}%)")
    print(f"  Not found in ROBOKOP: {not_found:,} ({100*not_found/total_nodes:.1f}%)")

    # Identify expected nodes missing from ROBOKOP
    missing_expected = merged[(merged['Is_Expected'] == True) & (merged['Node_degree'] == 0)]
    num_missing_expected = len(missing_expected)
    total_expected = (merged['Is_Expected'] == True).sum()

    print(f"\nExpected node statistics:")
    print(f"  Total expected nodes: {total_expected:,}")
    print(f"  Expected nodes missing from ROBOKOP: {num_missing_expected:,} ({100*num_missing_expected/total_expected:.1f}%)")

    # Write main output
    merged.to_csv(output_file, sep='\t', index=False)
    print(f"\nOutput written to: {output_file}")

    # Write missing expected nodes
    missing_expected.to_csv(missing_nodes_file, sep='\t', index=False)
    print(f"Missing expected nodes written to: {missing_nodes_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Join node path counts with ROBOKOP node degrees"
    )
    parser.add_argument(
        '--path-counts',
        default='node_path_counts.tsv',
        help='Path to node_path_counts.tsv (default: node_path_counts.tsv)'
    )
    parser.add_argument(
        '--node-degrees',
        default='robokop_node_degrees.tsv',
        help='Path to robokop_node_degrees.tsv (default: robokop_node_degrees.tsv)'
    )
    parser.add_argument(
        '--output',
        default='node_path_counts_with_degrees.tsv',
        help='Path to output TSV file (default: node_path_counts_with_degrees.tsv)'
    )
    parser.add_argument(
        '--missing-nodes',
        default='missing_expected_nodes.tsv',
        help='Path to output file for expected nodes not in ROBOKOP (default: missing_expected_nodes.tsv)'
    )

    args = parser.parse_args()

    join_path_counts_with_degrees(
        args.path_counts,
        args.node_degrees,
        args.output,
        args.missing_nodes
    )


if __name__ == '__main__':
    main()
