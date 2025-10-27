#!/usr/bin/env python3
"""
Analyze whether computing 3-hop paths in forward vs reverse direction
would have different performance characteristics.

For path A -> B -> C -> D (3 edges, 4 nodes):
- Forward: (MatrixAB @ MatrixBC) @ MatrixCD
  - Intermediate: MatrixAB @ MatrixBC (connects A to C)
- Reverse: (MatrixDC^T @ MatrixCB^T) @ MatrixBA^T
  - Intermediate: MatrixDC^T @ MatrixCB^T (connects D to B)

Key insight: The intermediate matrix size/sparsity determines performance.
If (AB @ BC) is much larger than (DC^T @ CB^T), reverse would be faster.

This script:
1. Loads all matrices (forward + reverse)
2. For each valid 3-hop combination, computes BOTH intermediate results
3. Compares size and estimates which direction would be faster
4. Outputs statistics on how often reverse is better
"""

import argparse
import json
from collections import defaultdict
import graphblas as gb
from type_utils import get_most_specific_type

SYMMETRIC_PREDICATES = {
    'biolink:interacts_with',
    'biolink:coexists_with',
    'biolink:correlated_with',
    'biolink:associated_with',
    'biolink:related_to',
    'biolink:similar_to',
    'biolink:homologous_to',
    'biolink:orthologous_to',
    'biolink:paralogous_to',
    'biolink:xenologous_to',
}


def load_node_types(nodes_file: str) -> dict:
    """Load node types from KGX nodes file."""
    print(f"Loading node types from {nodes_file}...", flush=True)
    node_types = {}

    with open(nodes_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if line_num % 1_000_000 == 0:
                print(f"  Loaded {line_num:,} nodes", flush=True)

            node = json.loads(line)
            node_id = node['id']
            categories = node.get('category', [])

            if categories:
                most_specific = get_most_specific_type(categories)
                primary_type = most_specific.replace('biolink:', '')
                node_types[node_id] = primary_type

    print(f"Loaded {len(node_types):,} node types", flush=True)
    return node_types


def build_matrices(edges_file: str, node_types: dict):
    """Build sparse matrices for each (source_type, predicate, target_type) triple."""
    print(f"\nCollecting edge types from {edges_file}...", flush=True)

    edge_triples = defaultdict(list)
    node_to_idx = defaultdict(dict)

    with open(edges_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if line_num % 1_000_000 == 0:
                print(f"  Processed {line_num:,} edges", flush=True)

            edge = json.loads(line)
            predicate = edge.get('predicate', '')

            if predicate == 'biolink:subclass_of':
                continue

            subject = edge['subject']
            obj = edge['object']
            src_type = node_types.get(subject)
            tgt_type = node_types.get(obj)

            if not src_type or not tgt_type:
                continue

            pred = predicate.replace('biolink:', '')
            triple = (src_type, pred, tgt_type)
            edge_triples[triple].append((subject, obj))

            if subject not in node_to_idx[src_type]:
                idx = len(node_to_idx[src_type])
                node_to_idx[src_type][subject] = idx

            if obj not in node_to_idx[tgt_type]:
                idx = len(node_to_idx[tgt_type])
                node_to_idx[tgt_type][obj] = idx

    print(f"\nBuilding GraphBLAS matrices...", flush=True)
    matrices = {}

    for triple, edges in edge_triples.items():
        src_type, pred, tgt_type = triple
        rows = [node_to_idx[src_type][src_id] for src_id, _ in edges]
        cols = [node_to_idx[tgt_type][tgt_id] for _, tgt_id in edges]

        nrows = len(node_to_idx[src_type])
        ncols = len(node_to_idx[tgt_type])

        matrix = gb.Matrix.from_coo(
            rows, cols, [1] * len(rows),
            nrows=nrows, ncols=ncols,
            dtype=gb.dtypes.BOOL,
            dup_op=gb.binary.any
        )

        matrices[triple] = matrix

    print(f"Built {len(matrices):,} matrices", flush=True)
    return matrices


def estimate_matrix_memory_bytes(matrix):
    """
    Estimate memory usage of a GraphBLAS sparse matrix in bytes.

    For BOOL dtype sparse matrix:
    - Each entry needs: row index (8 bytes) + col index (8 bytes) + value (1 byte)
    - Plus overhead for sparse structure (~17 bytes per entry total)
    """
    return matrix.nvals * 17  # Conservative estimate


def analyze_direction_performance(matrices, max_samples=1000):
    """
    Compare performance characteristics of forward vs reverse direction.

    Samples valid 3-hop paths and computes intermediate matrix sizes for both directions.
    Tracks both number of edges and memory footprint.
    """
    print(f"\n{'=' * 80}", flush=True)
    print("ANALYZING FORWARD VS REVERSE PERFORMANCE", flush=True)
    print(f"{'=' * 80}", flush=True)

    # Build extended matrix list with inverses
    all_matrices = []
    for (src_type, pred, tgt_type), matrix in matrices.items():
        # Forward
        all_matrices.append((src_type, pred, tgt_type, matrix, 'F'))

        # Reverse (if not symmetric)
        is_symmetric = f'biolink:{pred}' in SYMMETRIC_PREDICATES
        if not is_symmetric:
            all_matrices.append((tgt_type, pred, src_type, matrix.T, 'R'))

    print(f"Total matrices (with inverses): {len(all_matrices):,}", flush=True)

    # Group by source type
    by_source_type = defaultdict(list)
    for src_type, pred, tgt_type, matrix, direction in all_matrices:
        by_source_type[src_type].append((src_type, pred, tgt_type, matrix, direction))

    # Sample valid 3-hop paths and compare
    samples_checked = 0
    forward_faster = 0
    reverse_faster = 0
    equal = 0

    forward_smaller_intermediate = 0
    reverse_smaller_intermediate = 0

    # Track memory statistics
    forward_memory_list = []
    reverse_memory_list = []

    with open('direction_analysis.tsv', 'w') as f:
        f.write("forward_metapath\tforward_intermediate_edges\tforward_memory_mb\t"
                "reverse_metapath\treverse_intermediate_edges\treverse_memory_mb\t"
                "better_direction\tmemory_ratio\n")

        for idx1, (src_type1, pred1, tgt_type1, matrix1, dir1) in enumerate(all_matrices):
            if samples_checked >= max_samples:
                break

            if tgt_type1 not in by_source_type:
                continue

            for idx2, (src_type2, pred2, tgt_type2, matrix2, dir2) in enumerate(by_source_type[tgt_type1]):
                if samples_checked >= max_samples:
                    break

                if tgt_type2 not in by_source_type:
                    continue

                for src_type3, pred3, tgt_type3, matrix3, dir3 in by_source_type[tgt_type2]:
                    if samples_checked >= max_samples:
                        break

                    # Check dimension compatibility
                    if matrix1.ncols != matrix2.nrows or matrix2.ncols != matrix3.nrows:
                        continue

                    # FORWARD: (A @ B) @ C
                    # Compute intermediate A @ B
                    forward_intermediate = matrix1.mxm(matrix2, gb.semiring.any_pair).new()
                    forward_intermediate_size = forward_intermediate.nvals
                    forward_memory_bytes = estimate_matrix_memory_bytes(forward_intermediate)
                    forward_memory_mb = forward_memory_bytes / (1024 * 1024)

                    # REVERSE: (C^T @ B^T) @ A^T
                    # Compute intermediate C^T @ B^T
                    reverse_intermediate = matrix3.T.mxm(matrix2.T, gb.semiring.any_pair).new()
                    reverse_intermediate_size = reverse_intermediate.nvals
                    reverse_memory_bytes = estimate_matrix_memory_bytes(reverse_intermediate)
                    reverse_memory_mb = reverse_memory_bytes / (1024 * 1024)

                    # Track memory distributions
                    forward_memory_list.append(forward_memory_mb)
                    reverse_memory_list.append(reverse_memory_mb)

                    # Calculate memory ratio (forward / reverse)
                    if reverse_memory_mb > 0:
                        memory_ratio = forward_memory_mb / reverse_memory_mb
                    else:
                        memory_ratio = float('inf') if forward_memory_mb > 0 else 1.0

                    # Determine which is better (smaller intermediate is usually faster)
                    if forward_intermediate_size < reverse_intermediate_size:
                        better = "forward"
                        forward_smaller_intermediate += 1
                    elif reverse_intermediate_size < forward_intermediate_size:
                        better = "reverse"
                        reverse_smaller_intermediate += 1
                    else:
                        better = "equal"
                        equal += 1

                    # Format metapaths
                    forward_path = f"{src_type1}|{pred1}|{dir1}|{tgt_type1}|{pred2}|{dir2}|{tgt_type2}|{pred3}|{dir3}|{tgt_type3}"
                    reverse_path = f"{tgt_type3}|{pred3}|{'F' if dir3=='R' else 'R'}|{tgt_type2}|{pred2}|{'F' if dir2=='R' else 'R'}|{tgt_type1}|{pred1}|{'F' if dir1=='R' else 'R'}|{src_type1}"

                    f.write(f"{forward_path}\t{forward_intermediate_size}\t{forward_memory_mb:.3f}\t"
                            f"{reverse_path}\t{reverse_intermediate_size}\t{reverse_memory_mb:.3f}\t"
                            f"{better}\t{memory_ratio:.3f}\n")

                    samples_checked += 1

                    if samples_checked % 100 == 0:
                        print(f"Checked {samples_checked:,} paths | "
                              f"Forward better: {forward_smaller_intermediate} | "
                              f"Reverse better: {reverse_smaller_intermediate} | "
                              f"Equal: {equal}", flush=True)

    # Calculate memory statistics
    import statistics

    forward_memory_list.sort()
    reverse_memory_list.sort()

    def percentile(data, p):
        """Calculate percentile p (0-100) from sorted data."""
        if not data:
            return 0
        k = (len(data) - 1) * (p / 100.0)
        f = int(k)
        c = f + 1 if (f + 1) < len(data) else f
        if f == c:
            return data[f]
        return data[f] * (c - k) + data[c] * (k - f)

    def count_fits_in_memory(data, memory_budget_mb):
        """Count how many intermediates fit within memory budget."""
        return sum(1 for x in data if x <= memory_budget_mb)

    print(f"\n{'=' * 80}", flush=True)
    print("RESULTS: INTERMEDIATE MATRIX SIZE COMPARISON", flush=True)
    print(f"{'=' * 80}", flush=True)
    print(f"Total paths analyzed: {samples_checked:,}")
    print(f"Forward has smaller intermediate: {forward_smaller_intermediate} ({forward_smaller_intermediate/samples_checked*100:.1f}%)")
    print(f"Reverse has smaller intermediate: {reverse_smaller_intermediate} ({reverse_smaller_intermediate/samples_checked*100:.1f}%)")
    print(f"Equal: {equal} ({equal/samples_checked*100:.1f}%)")

    print(f"\n{'=' * 80}", flush=True)
    print("MEMORY STATISTICS (MB per intermediate matrix)", flush=True)
    print(f"{'=' * 80}", flush=True)

    print(f"\nFORWARD DIRECTION:")
    print(f"  Min:     {min(forward_memory_list):.2f} MB")
    print(f"  p25:     {percentile(forward_memory_list, 25):.2f} MB")
    print(f"  Median:  {percentile(forward_memory_list, 50):.2f} MB")
    print(f"  Mean:    {statistics.mean(forward_memory_list):.2f} MB")
    print(f"  p75:     {percentile(forward_memory_list, 75):.2f} MB")
    print(f"  p90:     {percentile(forward_memory_list, 90):.2f} MB")
    print(f"  p95:     {percentile(forward_memory_list, 95):.2f} MB")
    print(f"  p99:     {percentile(forward_memory_list, 99):.2f} MB")
    print(f"  Max:     {max(forward_memory_list):.2f} MB")

    print(f"\nREVERSE DIRECTION:")
    print(f"  Min:     {min(reverse_memory_list):.2f} MB")
    print(f"  p25:     {percentile(reverse_memory_list, 25):.2f} MB")
    print(f"  Median:  {percentile(reverse_memory_list, 50):.2f} MB")
    print(f"  Mean:    {statistics.mean(reverse_memory_list):.2f} MB")
    print(f"  p75:     {percentile(reverse_memory_list, 75):.2f} MB")
    print(f"  p90:     {percentile(reverse_memory_list, 90):.2f} MB")
    print(f"  p95:     {percentile(reverse_memory_list, 95):.2f} MB")
    print(f"  p99:     {percentile(reverse_memory_list, 99):.2f} MB")
    print(f"  Max:     {max(reverse_memory_list):.2f} MB")

    print(f"\n{'=' * 80}", flush=True)
    print("PARALLELIZATION POTENTIAL", flush=True)
    print(f"{'=' * 80}", flush=True)

    memory_budgets = [100, 500, 1000, 2000, 4000]
    print(f"\n{'Budget (MB)':<15} {'Forward Fits':<15} {'Reverse Fits':<15} {'Better':<10}")
    print(f"{'-'*55}")

    for budget in memory_budgets:
        forward_fits = count_fits_in_memory(forward_memory_list, budget)
        reverse_fits = count_fits_in_memory(reverse_memory_list, budget)
        forward_pct = forward_fits / samples_checked * 100
        reverse_pct = reverse_fits / samples_checked * 100

        better = "Forward" if forward_fits > reverse_fits else "Reverse" if reverse_fits > forward_fits else "Equal"

        print(f"{budget:<15} {forward_fits:>6} ({forward_pct:>5.1f}%)  "
              f"{reverse_fits:>6} ({reverse_pct:>5.1f}%)  {better:<10}")

    print(f"\nInterpretation:")
    print(f"- With {memory_budgets[1]} MB/worker: "
          f"Forward can parallelize {count_fits_in_memory(forward_memory_list, memory_budgets[1])} paths, "
          f"Reverse can parallelize {count_fits_in_memory(reverse_memory_list, memory_budgets[1])} paths")
    print(f"- Higher 'fits' count = more paths can run in parallel on memory-constrained workers")

    print(f"\n{'=' * 80}", flush=True)
    print(f"Wrote detailed results to direction_analysis.tsv")
    print(f"{'=' * 80}", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze whether forward or reverse direction is faster for 3-hop paths'
    )
    parser.add_argument('--edges', required=True, help='Path to edges.jsonl')
    parser.add_argument('--nodes', required=True, help='Path to nodes.jsonl')
    parser.add_argument('--max-samples', type=int, default=1000,
                        help='Maximum number of 3-hop paths to sample')

    args = parser.parse_args()

    # Load data and build matrices
    node_types = load_node_types(args.nodes)
    matrices = build_matrices(args.edges, node_types)

    # Analyze direction performance
    analyze_direction_performance(matrices, args.max_samples)


if __name__ == "__main__":
    main()
