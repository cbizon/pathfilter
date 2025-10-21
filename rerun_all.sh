#!/bin/bash

# Normalize input data with fixed CURIE parser
uv run python scripts/normalize_input_data.py

# Run filter evaluations
uv run python -m pathfilter.cli --output all_filter_results.tsv

# Generate filter visualizations
uv run python scripts/visualize_results.py --results all_filter_results.tsv --output filter_enrichment_by_query.png
uv run python scripts/best_filters_table.py --results all_filter_results.tsv --output best_filters_table.tsv

# Run metapath analysis
uv run python scripts/metapath_enrichment.py --output metapath_enrichment.tsv
uv run python scripts/aggregate_metapaths.py --input metapath_enrichment.tsv --output metapath_aggregated.tsv
uv run python scripts/sort_metapaths.py --input metapath_enrichment.tsv --output metapath_enrichment_sorted.tsv

# Generate metapath visualizations
uv run python scripts/plot_metapath_scatter.py --input metapath_enrichment.tsv --output metapath_frequency_vs_enrichment.png
uv run python scripts/plot_metapath_consistency.py --input metapath_aggregated.tsv --output metapath_consistency.png
uv run python scripts/plot_unreliable_metapaths.py --aggregated metapath_aggregated.tsv --enrichment metapath_enrichment.tsv --output complete_misses.png

# Analyze node path counts
uv run python scripts/analyze_node_path_counts.py

# Calculate node degrees from ROBOKOP graph
uv run python scripts/calculate_node_degrees.py \
  --edges ../SimplePredictions/input_graphs/robokop_base_nonredundant/edges.jsonl \
  --nodes ../SimplePredictions/input_graphs/robokop_base_nonredundant/nodes.jsonl \
  --output robokop_node_degrees.tsv

# Join path counts with node degrees
uv run python scripts/join_path_counts_with_degrees.py \
  --path-counts node_path_counts.tsv \
  --node-degrees robokop_node_degrees.tsv \
  --output node_path_counts_with_degrees.tsv \
  --missing-nodes missing_expected_nodes.tsv

# Generate path count visualizations
uv run python scripts/plot_path_count_vs_hit_fraction.py \
  --input node_path_counts.tsv \
  --output path_count_vs_hit_fraction.png
