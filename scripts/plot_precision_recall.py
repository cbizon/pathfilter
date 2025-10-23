#!/usr/bin/env python3
"""
Visualize precision vs recall tradeoff for filter combinations.

Creates stacked subplots, one per query, showing each filter combination
as a point in precision-recall space.
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from pathfilter.query_loader import load_all_queries


def is_pareto_optimal(recall, precision):
    """Identify Pareto optimal points (maximize both recall and precision)."""
    is_optimal = []
    for i in range(len(recall)):
        dominated = False
        for j in range(len(recall)):
            if i != j:
                # Point j dominates point i if it's >= in both dimensions and > in at least one
                if (recall[j] >= recall[i] and precision[j] >= precision[i] and
                    (recall[j] > recall[i] or precision[j] > precision[i])):
                    dominated = True
                    break
        is_optimal.append(not dominated)
    return is_optimal


def parse_filter_rules(filter_strategy):
    """Parse filter strategy string into a set of rules."""
    if pd.isna(filter_strategy) or filter_strategy == 'none':
        return set()
    return set(filter_strategy.split('+'))


def is_proper_superset(filter_a, filter_b):
    """Check if filter_a is a proper superset of filter_b."""
    rules_a = parse_filter_rules(filter_a)
    rules_b = parse_filter_rules(filter_b)
    # Proper superset: A ⊃ B (A contains all of B, and A has more rules)
    return rules_b < rules_a  # < operator checks proper subset


def remove_redundant_filters(points_df):
    """Remove filter combinations that are proper supersets of simpler ones with same precision/recall."""
    if len(points_df) == 0:
        return points_df

    # Group by (precision, recall)
    grouped = points_df.groupby(['precision', 'recall'])

    filtered_rows = []
    for (prec, rec), group in grouped:
        # For each group with same precision/recall, remove proper supersets
        group_list = group.to_dict('records')
        keep_indices = []

        for i, row_i in enumerate(group_list):
            filter_i = row_i['rule']
            is_superset_of_another = False

            # Check if this filter is a proper superset of any other filter in the group
            for j, row_j in enumerate(group_list):
                if i != j:
                    filter_j = row_j['rule']
                    if is_proper_superset(filter_i, filter_j):
                        # filter_i is a proper superset of filter_j, so filter_i is redundant
                        is_superset_of_another = True
                        break

            if not is_superset_of_another:
                keep_indices.append(i)

        # Keep only the non-redundant filters
        for idx in keep_indices:
            filtered_rows.append(group_list[idx])

    return pd.DataFrame(filtered_rows)


def plot_precision_recall(results_file: Path, output_file: Path, pareto_output_file: Path):
    """Create precision vs recall scatter plots for each query."""
    # Read results
    df = pd.read_csv(results_file, sep='\t')

    # Load query information for titles
    queries_file = Path('normalized_input_data/queries_normalized.json')
    if not queries_file.exists():
        queries_file = Path('input_data/Pathfinder Test Queries.xlsx.ods')

    query_objects = load_all_queries(str(queries_file))
    query_titles = {q.name: f"{q.start_label} → {q.end_label}" for q in query_objects}

    # Get unique queries
    queries = sorted(df['query'].unique())

    # Create figure with subplots - wider and taller to accommodate legend
    n_queries = len(queries)
    fig, axes = plt.subplots(n_queries, 1, figsize=(20, 6 * n_queries))

    # Handle single query case
    if n_queries == 1:
        axes = [axes]

    # Collect all Pareto optimal points
    all_pareto_points = []

    # Plot each query
    for ax, query in zip(axes, queries):
        query_df = df[df['query'] == query].copy()

        # Identify Pareto optimal points
        recall = query_df['recall'].values
        precision = query_df['precision_after'].values
        pareto_mask = is_pareto_optimal(recall, precision)
        query_df['pareto'] = pareto_mask

        # Split into Pareto and non-Pareto
        pareto_df = query_df[query_df['pareto']].copy()
        non_pareto_df = query_df[~query_df['pareto']]

        # Filter Pareto points: remove (0,0) and redundant combinations
        pareto_df = pareto_df[~((pareto_df['precision_after'] == 0) & (pareto_df['recall'] == 0))]

        # Create temporary dataframe for redundancy filtering
        temp_pareto = pd.DataFrame([{
            'Query': query,
            'rule': row['filter_strategy'],
            'precision': row['precision_after'],
            'recall': row['recall']
        } for _, row in pareto_df.iterrows()])

        if len(temp_pareto) > 0:
            temp_pareto = remove_redundant_filters(temp_pareto)
            # Filter pareto_df to only include non-redundant ones
            filtered_strategies = set(temp_pareto['rule'])
            pareto_df = pareto_df[pareto_df['filter_strategy'].isin(filtered_strategies)]

        # Collect filtered Pareto points for output file
        for _, row in pareto_df.iterrows():
            all_pareto_points.append({
                'Query': query,
                'rule': row['filter_strategy'],
                'precision': row['precision_after'],
                'recall': row['recall']
            })

        # Plot non-Pareto points first
        ax.scatter(
            non_pareto_df['recall'],
            non_pareto_df['precision_after'],
            alpha=0.4,
            s=40,
            c='steelblue',
            edgecolors='black',
            linewidth=0.5
        )

        # Plot Pareto points on top
        ax.scatter(
            pareto_df['recall'],
            pareto_df['precision_after'],
            alpha=0.9,
            s=80,
            c='red',
            edgecolors='darkred',
            linewidth=1.5,
            marker='*',
            zorder=5
        )

        # Styling
        ax.set_xlabel('Recall (After Filtering)', fontsize=11)
        ax.set_ylabel('Precision (After Filtering)', fontsize=11)
        query_title = query_titles.get(query, query)
        ax.set_title(f'{query}: {query_title}', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')

        # Set axis limits based on actual data
        recall_min = query_df['recall'].min()
        recall_max = query_df['recall'].max()
        precision_min = query_df['precision_after'].min()
        precision_max = query_df['precision_after'].max()

        # Add 5% padding (or 0.05 absolute if range is zero)
        recall_range = recall_max - recall_min
        precision_range = precision_max - precision_min

        recall_padding = 0.05 * recall_range if recall_range > 0 else 0.05
        precision_padding = 0.05 * precision_range if precision_range > 0 else 0.005

        ax.set_xlim(
            max(0, recall_min - recall_padding),
            min(1, recall_max + recall_padding)
        )
        ax.set_ylim(
            max(0, precision_min - precision_padding),
            min(1, precision_max + precision_padding)
        )

        # Add diagonal reference line (precision = recall) only in visible range
        diag_min = max(ax.get_xlim()[0], ax.get_ylim()[0])
        diag_max = min(ax.get_xlim()[1], ax.get_ylim()[1])
        if diag_min < diag_max:
            ax.plot([diag_min, diag_max], [diag_min, diag_max], 'k--', alpha=0.3, linewidth=1)

        # Add count annotation
        ax.text(
            0.02, 0.98,
            f'n = {len(query_df)} combinations\nPareto: {len(pareto_df)}',
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3)
        )

        # Add legend for filtered Pareto points on the right side
        if len(pareto_df) > 0:
            # Sort Pareto points by recall (left to right on plot)
            pareto_sorted = pareto_df.sort_values('recall')

            # Create legend text - one line per filter with R, P, and rule
            legend_lines = []
            for _, row in pareto_sorted.iterrows():
                filter_str = row['filter_strategy'].replace('+', ', ')
                legend_lines.append(
                    f"R={row['recall']:.3f}, P={row['precision_after']:.4f}: {filter_str}"
                )

            legend_text = '\n'.join(legend_lines)

            # Add text box on the right
            ax.text(
                1.01, 0.5,
                legend_text,
                transform=ax.transAxes,
                fontsize=9,
                verticalalignment='center',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8, edgecolor='darkred'),
                family='monospace'
            )

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Saved precision-recall plot to {output_file}")

    # Write Pareto optimal points to TSV file
    pareto_df_output = pd.DataFrame(all_pareto_points)

    # Filter out (0, 0) points
    pareto_df_output = pareto_df_output[~((pareto_df_output['precision'] == 0) & (pareto_df_output['recall'] == 0))]

    # Remove redundant filter combinations (proper supersets with same precision/recall)
    pareto_df_output = remove_redundant_filters(pareto_df_output)

    # Sort by Query, then by precision (descending)
    pareto_df_output = pareto_df_output.sort_values(['Query', 'precision'], ascending=[True, False])
    pareto_df_output.to_csv(pareto_output_file, sep='\t', index=False)
    print(f"Saved Pareto optimal points to {pareto_output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Plot precision vs recall for filter combinations'
    )
    parser.add_argument(
        '--results',
        type=Path,
        default='all_filter_results.tsv',
        help='Input TSV file with filter evaluation results'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default='precision_recall.png',
        help='Output PNG file'
    )
    parser.add_argument(
        '--pareto-output',
        type=Path,
        default='pareto_optimal_points.tsv',
        help='Output TSV file for Pareto optimal points'
    )

    args = parser.parse_args()

    if not args.results.exists():
        print(f"Error: Results file not found: {args.results}")
        return 1

    plot_precision_recall(args.results, args.output, args.pareto_output)
    return 0


if __name__ == '__main__':
    exit(main())
