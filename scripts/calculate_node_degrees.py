#!/usr/bin/env python3
"""
Calculate node degrees from KGX node and edge files.

Node degree is defined as the number of unique nodes connected to a given node,
regardless of edge direction or multiplicity.
"""

import argparse
import json
import sys
from collections import defaultdict


def calculate_node_degrees(edges_file: str, nodes_file: str, output_file: str):
    """
    Calculate node degrees from KGX files and write to TSV.

    Args:
        edges_file: Path to edges.jsonl file
        nodes_file: Path to nodes.jsonl file
        output_file: Path to output TSV file
    """
    # Pass 1: Process edges file to build neighbor sets
    print(f"Processing edges file: {edges_file}", file=sys.stderr)
    neighbors = defaultdict(set)
    edge_count = 0

    with open(edges_file, 'r') as f:
        for line in f:
            edge = json.loads(line)
            subject = edge['subject']
            obj = edge['object']

            # Add bidirectional connections
            neighbors[subject].add(obj)
            neighbors[obj].add(subject)

            edge_count += 1
            if edge_count % 100000 == 0:
                print(f"  Processed {edge_count:,} edges...", file=sys.stderr)

    print(f"Processed {edge_count:,} total edges", file=sys.stderr)
    print(f"Found {len(neighbors):,} unique nodes with connections", file=sys.stderr)

    # Pass 2: Process nodes file and write output
    print(f"\nProcessing nodes file: {nodes_file}", file=sys.stderr)
    node_count = 0
    info_content_count = 0

    with open(nodes_file, 'r') as nf, open(output_file, 'w') as of:
        # Write header
        of.write("Node_id\tName\tNode_degree\tInformation_content\n")

        for line in nf:
            node = json.loads(line)
            node_id = node['id']
            name = node.get('name', '')
            info_content = node.get('information_content', '')

            # Track how many nodes have information content
            if info_content:
                info_content_count += 1

            # Calculate degree
            degree = len(neighbors.get(node_id, set()))

            # Write output
            of.write(f"{node_id}\t{name}\t{degree}\t{info_content}\n")

            node_count += 1
            if node_count % 100000 == 0:
                print(f"  Processed {node_count:,} nodes...", file=sys.stderr)

    print(f"Processed {node_count:,} total nodes", file=sys.stderr)
    print(f"Nodes with information_content: {info_content_count:,} ({info_content_count/node_count*100:.1f}%)", file=sys.stderr)
    print(f"Output written to: {output_file}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Calculate node degrees from KGX node and edge files"
    )
    parser.add_argument(
        '--edges',
        required=True,
        help='Path to KGX edges.jsonl file'
    )
    parser.add_argument(
        '--nodes',
        required=True,
        help='Path to KGX nodes.jsonl file'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Path to output TSV file'
    )

    args = parser.parse_args()

    calculate_node_degrees(args.edges, args.nodes, args.output)


if __name__ == '__main__':
    main()
