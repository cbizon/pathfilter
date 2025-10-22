#!/bin/bash

# STEP 1: Normalize input data with fixed CURIE parser
echo "Step 1: Normalizing input data..."
uv run python scripts/normalize_input_data.py

# STEP 2: Calculate node characteristics (needed for node-based filters)
echo -e "\nStep 2: Calculating node degrees and information content from ROBOKOP graph..."
uv run python scripts/calculate_node_degrees.py \
  --edges ../SimplePredictions/input_graphs/robokop_base_nonredundant/edges.jsonl \
  --nodes ../SimplePredictions/input_graphs/robokop_base_nonredundant/nodes.jsonl \
  --output robokop_node_degrees.tsv

echo -e "\nStep 3: Analyzing node path counts..."
uv run python scripts/analyze_node_path_counts.py

echo -e "\nStep 4: Joining path counts with node degrees..."
uv run python scripts/join_path_counts_with_degrees.py \
  --path-counts node_path_counts.tsv \
  --node-degrees robokop_node_degrees.tsv \
  --output node_path_counts_with_degrees.tsv \
  --missing-nodes missing_expected_nodes.tsv

# STEP 5: Run filter evaluations (now can use node characteristics)
echo -e "\nStep 5: Running filter evaluations..."
uv run python -m pathfilter.cli --output all_filter_results.tsv

# STEP 6: Generate filter visualizations
echo -e "\nStep 6: Generating filter visualizations..."
uv run python scripts/visualize_results.py --results all_filter_results.tsv --output filter_enrichment_by_query.png
uv run python scripts/best_filters_table.py --results all_filter_results.tsv --output best_filters_table.tsv

# STEP 7: Run metapath analysis
echo -e "\nStep 7: Running metapath analysis..."
uv run python scripts/metapath_enrichment.py --output metapath_enrichment.tsv
uv run python scripts/aggregate_metapaths.py --input metapath_enrichment.tsv --output metapath_aggregated.tsv
uv run python scripts/sort_metapaths.py --input metapath_enrichment.tsv --output metapath_enrichment_sorted.tsv

# STEP 8: Generate metapath visualizations
echo -e "\nStep 8: Generating metapath visualizations..."
uv run python scripts/plot_metapath_scatter.py --input metapath_enrichment.tsv --output metapath_frequency_vs_enrichment.png
uv run python scripts/plot_metapath_consistency.py --input metapath_aggregated.tsv --output metapath_consistency.png
uv run python scripts/plot_unreliable_metapaths.py --aggregated metapath_aggregated.tsv --enrichment metapath_enrichment.tsv --output complete_misses.png

# STEP 9: Generate path count visualizations
echo -e "\nStep 9: Generating path count visualizations..."
uv run python scripts/plot_path_count_vs_hit_fraction.py \
  --input node_path_counts.tsv \
  --output path_count_vs_hit_fraction.png

echo -e "\nAll done!"
