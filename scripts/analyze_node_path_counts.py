"""Analyze node path counts per query and compare expected vs all nodes."""
import argparse
from collections import Counter
from pathlib import Path
from typing import List
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathfilter.query_loader import load_all_queries
from pathfilter.path_loader import load_paths_for_query


def count_node_path_counts_per_query(queries, paths_dir: str) -> pd.DataFrame:
    """
    Count how many paths each node appears in, keeping queries separate.

    Includes expected nodes even if they have 0 path counts.
    Also tracks "hit paths" (paths containing at least one expected node).

    Args:
        queries: List of Query objects
        paths_dir: Directory containing path files

    Returns:
        DataFrame with columns: Query, CURIE, Path_Count, Hit_Path_Count, Hit_Path_Fraction, Is_Expected
    """
    all_data = []

    for query in queries:
        # Get expected nodes for this query
        expected_nodes = set()
        for label, curies in query.expected_nodes.items():
            expected_nodes.update(curies)

        # Load paths and count nodes
        paths = load_paths_for_query(query, paths_dir)
        if not paths:
            print(f"Warning: No paths found for query {query.name}")
            # Still include expected nodes with 0 counts
            for curie in expected_nodes:
                all_data.append({
                    'Query': query.name,
                    'CURIE': curie,
                    'Path_Count': 0,
                    'Hit_Path_Count': 0,
                    'Hit_Path_Fraction': 0.0,
                    'Is_Expected': True
                })
            continue

        # Identify hit paths (paths containing at least one expected node)
        hit_path_indices = []
        for idx, path in enumerate(paths):
            path_nodes = set(path.path_curies)
            if path_nodes & expected_nodes:  # Intersection - path contains expected node
                hit_path_indices.append(idx)

        total_hit_paths = len(hit_path_indices)

        # Count paths each node appears in (total and hit paths)
        node_path_count = Counter()
        node_hit_path_count = Counter()

        for idx, path in enumerate(paths):
            is_hit_path = idx in hit_path_indices
            for curie in path.path_curies:
                node_path_count[curie] += 1
                if is_hit_path:
                    node_hit_path_count[curie] += 1

        # Add all nodes found in paths
        for curie, count in node_path_count.items():
            hit_count = node_hit_path_count.get(curie, 0)
            hit_fraction = hit_count / total_hit_paths if total_hit_paths > 0 else 0.0

            all_data.append({
                'Query': query.name,
                'CURIE': curie,
                'Path_Count': count,
                'Hit_Path_Count': hit_count,
                'Hit_Path_Fraction': hit_fraction,
                'Is_Expected': curie in expected_nodes
            })

        # Add expected nodes that weren't found (0 count)
        found_nodes = set(node_path_count.keys())
        missing_expected = expected_nodes - found_nodes
        for curie in missing_expected:
            all_data.append({
                'Query': query.name,
                'CURIE': curie,
                'Path_Count': 0,
                'Hit_Path_Count': 0,
                'Hit_Path_Fraction': 0.0,
                'Is_Expected': True
            })

        print(f"Processed {query.name}: {len(paths)} paths, {total_hit_paths} hit paths, "
              f"{len(node_path_count)} unique nodes, {len(expected_nodes)} expected ({len(missing_expected)} missing)")

    return pd.DataFrame(all_data)


def analyze_path_count_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate summary statistics for path counts by query.

    Args:
        df: DataFrame with Query, CURIE, Path_Count, Is_Expected columns

    Returns:
        DataFrame with statistics per query
    """
    stats = []

    for query in df['Query'].unique():
        query_df = df[df['Query'] == query]
        expected_df = query_df[query_df['Is_Expected']]
        other_df = query_df[~query_df['Is_Expected']]

        stats.append({
            'Query': query,
            'Total_Nodes': len(query_df),
            'Expected_Nodes': len(expected_df),
            'Expected_Found': len(expected_df[expected_df['Path_Count'] > 0]),
            'Expected_Missing': len(expected_df[expected_df['Path_Count'] == 0]),
            'Mean_Path_Count_Expected': expected_df['Path_Count'].mean() if len(expected_df) > 0 else 0,
            'Mean_Path_Count_Other': other_df['Path_Count'].mean() if len(other_df) > 0 else 0,
            'Median_Path_Count_Expected': expected_df['Path_Count'].median() if len(expected_df) > 0 else 0,
            'Median_Path_Count_Other': other_df['Path_Count'].median() if len(other_df) > 0 else 0,
        })

    return pd.DataFrame(stats)


def create_visualization(df: pd.DataFrame, output_file: str):
    """
    Create visualization comparing path count distributions per query.

    Args:
        df: DataFrame with Query, CURIE, Path_Count, Is_Expected columns
        output_file: Path to save the visualization
    """
    # Create figure with subplots
    queries = sorted(df['Query'].unique())
    n_queries = len(queries)

    # Create a grid layout
    n_cols = 4
    n_rows = (n_queries + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, 5 * n_rows))
    axes = axes.flatten() if n_queries > 1 else [axes]

    for idx, query in enumerate(queries):
        ax = axes[idx]
        query_df = df[df['Query'] == query]

        # Only plot nodes that appear in paths (Path_Count > 0)
        plot_df = query_df[query_df['Path_Count'] > 0]

        if len(plot_df) == 0:
            ax.text(0.5, 0.5, f'{query}\nNo paths found',
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
            continue

        # Create violin plot
        sns.violinplot(data=plot_df, x='Is_Expected', y='Path_Count', ax=ax)
        ax.set_yscale('log')
        ax.set_xlabel('Is Expected Node')
        ax.set_ylabel('Path Count (log scale)')
        ax.set_title(f'{query}')

    # Hide extra subplots
    for idx in range(n_queries, len(axes)):
        axes[idx].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Visualization saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Analyze node path counts per query')
    parser.add_argument('--input-dir', default='normalized_input_data',
                        help='Directory containing normalized query data')
    parser.add_argument('--paths-dir', default='input_data/paths',
                        help='Directory containing path files')
    parser.add_argument('--output', default='node_path_counts.tsv',
                        help='Output file for path count data')
    parser.add_argument('--stats-output', default='node_path_count_stats.tsv',
                        help='Output file for summary statistics')
    parser.add_argument('--viz-output', default='node_path_count_distribution.png',
                        help='Output file for visualization')
    args = parser.parse_args()

    # Load queries
    queries_file = Path(args.input_dir) / 'Pathfinder Test Queries.xlsx.ods'
    print(f"Loading queries from {queries_file}")
    queries = load_all_queries(str(queries_file))
    print(f"Loaded {len(queries)} queries with expected nodes\n")

    # Count node path counts per query
    print("Counting node path counts per query...")
    df = count_node_path_counts_per_query(queries, args.paths_dir)

    # Save detailed path count data
    df.to_csv(args.output, sep='\t', index=False)
    print(f"\nPath count data saved to {args.output}")
    print(f"Total rows: {len(df)}")
    print(f"Queries: {df['Query'].nunique()}")
    print(f"Unique nodes across all queries: {df['CURIE'].nunique()}")

    # Calculate and save summary statistics
    print("\nCalculating summary statistics per query...")
    stats_df = analyze_path_count_stats(df)
    stats_df.to_csv(args.stats_output, sep='\t', index=False)
    print(f"Summary statistics saved to {args.stats_output}")
    print("\n" + stats_df.to_string(index=False))

    # Create visualization
    print("\nCreating visualization...")
    create_visualization(df, args.viz_output)

    # Print some interesting findings
    print("\nTop 10 highest path count nodes (across all queries):")
    top_nodes = df.nlargest(10, 'Path_Count')[['Query', 'CURIE', 'Path_Count', 'Is_Expected']]
    for _, row in top_nodes.iterrows():
        expected = "EXPECTED" if row['Is_Expected'] else ""
        print(f"  {row['Query']}: {row['CURIE']} = {row['Path_Count']} {expected}")


if __name__ == '__main__':
    main()
