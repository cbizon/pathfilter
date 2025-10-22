# Pathfilter

Path filtering and evaluation for Pathfinder queries.

## Overview

Pathfilter evaluates different filtering strategies on knowledge graph paths to determine which filters best retain paths containing expected nodes while reducing overall path counts.

## Installation

```bash
# Clone the repository
git clone https://github.com/cbizon/pathfilter.git
cd pathfilter

# Install dependencies with uv
uv sync
```

## Input Data Setup

**IMPORTANT**: The input data files are not included in the repository. You need to provide them separately.

### First Time Setup - Data Normalization

**Before running evaluations**, you must normalize the input data once:

```bash
uv run python scripts/normalize_input_data.py
```

This pre-normalizes all CURIEs in the input data using the Node Normalizer API, creating a `normalized_input_data/` directory. This one-time step provides a 16x performance improvement for evaluations (~0.7s vs 11s per query).

### Complete Analysis Pipeline

To run the entire analysis pipeline (normalization, filter evaluation, metapath analysis, node analysis, and all visualizations):

```bash
./rerun_all.sh
```

This script runs all analyses in the correct order:
1. Normalize input data
2. Evaluate all filter combinations
3. Generate filter visualizations (enrichment charts, best filters table)
4. Run metapath enrichment analysis
5. Generate metapath visualizations (scatter plots, consistency analysis)
6. Analyze node path counts
7. Calculate node degrees from ROBOKOP graph
8. Join path counts with node degrees
9. Generate path count visualizations

**Note**: The script expects ROBOKOP graph files at `../SimplePredictions/input_graphs/robokop_base_nonredundant/`. Edit the script if your graph files are located elsewhere.

### Required Directory Structure

```
pathfilter/
├── input_data/                            # Original data (read-only)
│   ├── Pathfinder Test Queries.xlsx.ods  # Query definitions
│   └── paths/                             # Path data files
│       ├── CHEBI_15647_to_UNII_31YO63LBSN.xlsx
│       ├── CHEBI_27881_to_NCBIGene_2739_paths.xlsx
│       ├── ... (one xlsx file per query)
└── normalized_input_data/                 # Auto-generated (do not edit)
    ├── Pathfinder Test Queries.xlsx.ods  # Pre-normalized queries
    └── paths/                             # Pre-normalized paths
```

### Input File Formats

**Query Definitions File**: `input_data/Pathfinder Test Queries.xlsx.ods`
- Overall list sheet with all queries
- Individual sheets per query (e.g., "PFTQ-1-c", "PFTQ-4")
- Each query sheet contains:
  - Row 0: Start node (label in col 1, CURIE(s) in col 2)
  - Row 1: End node (label in col 1, CURIE(s) in col 2)
  - Rows 2+: Expected nodes (label in col 1, CURIE(s) in col 2)
  - Note: CURIEs in column C may be concatenated without delimiters

**Path Files**: `input_data/paths/*.xlsx`
- Excel 2007+ format (.xlsx)
- One file per query, named: `{START_CURIE}_to_{END_CURIE}.xlsx`
  - Example: `CHEBI_31690_to_MONDO_0004979.xlsx`
  - Colons in CURIEs are replaced with underscores
- Required columns:
  - `path`: Node labels connected by " -> "
  - `num_paths`: Integer count
  - `categories`: Biolink categories connected by " --> "
  - `first_hop_predicates`, `second_hop_predicates`, `third_hop_predicates`: Predicate sets
  - `has_gene`: Boolean
  - `metapaths`: List of metapaths
  - `path_curies`: **CRITICAL** - Node CURIEs connected by " --> " (used for matching)

## Quick Start

### Evaluate All Queries with All Filter Combinations (Default)

```bash
uv run python -m pathfilter.cli --output results.tsv
```

This evaluates 256 filter combinations (2^8 path filters) across all queries (~1 minute for 20 queries). With node-based filters, this increases to 1,792 combinations. Results are written to TSV for analysis.

**Performance**: Uses optimized caching (applies each filter once, uses set intersections for combinations) to achieve O(N×F) complexity instead of O(N×F×C).

### Evaluate a Single Query

```bash
uv run python -m pathfilter.cli --query PFTQ-4 --output results.tsv
```

### Compare Specific Filter Strategies

```bash
# Compare default vs strict filtering
uv run python -m pathfilter.cli --filters "default|strict" --output results.tsv

# Use specific filters
uv run python -m pathfilter.cli --filters "no_dupe_types,no_expression" --output results.tsv
```

## Available Filters

- **default**: `no_dupe_types` + `no_expression` + `no_related_to`
- **strict**: default filters + `no_end_pheno`
- **Path-based filters**:
  - `no_dupe_types`: Remove paths with duplicate node types (requires 4 unique types after normalization: ChemicalEntity variants → Chemical, Protein → Gene)
  - `no_dupe_but_gene`: Like `no_dupe_types`, but allows Gene/Protein duplicates while requiring all other types to be unique
  - `no_nonconsecutive_dupe`: Remove paths where the same type appears at non-consecutive positions (A→B→A filtered, A→A→B allowed)
  - `no_expression`: Filter out `expressed_in` predicates
  - `no_related_to`: Remove generic `related_to` predicates
  - `no_end_pheno`: Filter paths ending with PhenotypicFeature→SmallMolecule
  - `no_chemical_start`: Remove paths starting with Disease→Chemical
  - `no_repeat_predicates`: Remove paths where the same predicate appears multiple times
  - `no_abab`: Remove paths with alternating type patterns (A→B→A→B), considering type equivalences (Disease/PhenotypicFeature, Chemical variants, Gene/Protein)
  - `all_paths`: No filtering (baseline)
- **Node-based filters** (require `node_path_counts_with_degrees.tsv`):
  - `min_ic_30`, `min_ic_50`, `min_ic_70`: Remove paths with any intermediate node having information content below threshold
  - `max_degree_1000`, `max_degree_5000`, `max_degree_10000`: Remove paths with any intermediate node having degree above threshold
  - Node filters only check intermediate nodes (positions 1 and 2), not start/end nodes

## Evaluation Metrics

For each filter strategy, the system calculates:

- **Recall**: Fraction of expected paths retained
- **Precision**: Fraction of paths containing expected nodes
- **Enrichment**: Improvement in precision (precision_after / precision_before)
- **Retention Rate**: Fraction of total paths kept
- **Expected Nodes Recall**: Fraction of unique expected nodes still found

## Visualizing and Analyzing Results

### Generate Enrichment Charts

Create bar charts showing enrichment for each filter across all queries:

```bash
uv run python scripts/visualize_results.py --results all_filter_results.tsv --output enrichment_by_query.png
```

This generates:
- PNG file with subplots for each query (single-column horizontal bar layout for readability with 64 combinations)
- Color-coded bars (green: strong enrichment >1.5, blue: moderate ≥1.0, coral: harmful <1.0)
- Query titles with start/end node labels

### Generate Best Filters Table

Create a summary table showing the best filter for each query:

```bash
uv run python scripts/best_filters_table.py --results all_filter_results.tsv --output best_filters.tsv
```

Output includes:
- Query ID and descriptive name
- Best filter (or "none" if no filter improves results)
- Enrichment factor
- Sorted by enrichment (highest to lowest)
- Statistics on most common effective filters

## Metapath Enrichment Analysis

Beyond evaluating filters, you can analyze which **structural patterns** (metapaths) in the knowledge graph correlate with finding expected nodes. Metapaths describe the types and predicates along a path (e.g., `SmallMolecule ---affects--> Gene ---target_for--> Disease`).

### What is Metapath Analysis?

Each path in the knowledge graph can match multiple structural patterns. Metapath analysis calculates enrichment metrics for each pattern to identify which structures are most likely to contain expected nodes. This helps understand:
- Which types of relationships lead to better results
- Which patterns work consistently across queries
- Which patterns are common but unreliable

### Running Metapath Analysis

**Analyze all queries** (~3 minutes):

```bash
uv run python scripts/metapath_enrichment.py --output metapath_enrichment.tsv
```

This generates `metapath_enrichment.tsv` with columns:
- `query_id`: Query identifier
- `metapath`: Structural pattern (e.g., `biolink:Gene ---affects--> biolink:Disease`)
- `total_paths`: Number of paths using this metapath
- `hit_paths`: Number of paths with this metapath containing expected nodes
- `precision`: Fraction of paths with this metapath that are hits
- `enrichment`: How much better than query baseline (>1.0 = better, <1.0 = worse)
- `frequency`: How common this metapath is in the query (can be >1.0 if paths have multiple metapaths)

**Important**: Queries with no hits in any path (e.g., PFTQ-11, PFTQ-14) are automatically excluded since enrichment is meaningless there.

### Aggregating Metapaths Across Queries

To identify consistently effective metapaths:

```bash
uv run python scripts/aggregate_metapaths.py --input metapath_enrichment.tsv --output metapath_aggregated.tsv
```

This creates `metapath_aggregated.tsv` with per-metapath statistics:
- `enrichment_min/max/mean`: Enrichment statistics across all queries where the metapath appears
- `frequency_min/max/mean`: Frequency statistics
- `num_queries`: Number of queries containing this metapath

**Key Finding**: Metapaths with `enrichment_min > 1.0` and `num_queries > 1` are consistently effective across multiple queries.

### Visualizing Metapath Patterns

**Frequency vs Enrichment scatter plot** (log-log scale):

```bash
uv run python scripts/plot_metapath_scatter.py --input metapath_enrichment.tsv --output metapath_frequency_vs_enrichment.png
```

Shows which metapaths are both common and effective (upper right = ideal).

**Consistency plot** (minimum enrichment vs number of queries):

```bash
uv run python scripts/plot_metapath_consistency.py --input metapath_aggregated.tsv --output metapath_consistency.png
```

Identifies generalizable metapaths (upper right = works well across many queries).

**Complete misses plot** (metapaths that fail in at least one query):

```bash
uv run python scripts/plot_unreliable_metapaths.py --aggregated metapath_aggregated.tsv --enrichment metapath_enrichment.tsv --output complete_misses.png
```

Shows common metapaths (appear in 7 queries) that have enrichment=0 in at least one query, revealing unreliable patterns.

### Sorting and Filtering

**Sort aggregated results**:

```bash
uv run python scripts/sort_metapaths.py --input metapath_enrichment.tsv --output metapath_enrichment_sorted.tsv
```

Sorts by query_id, then enrichment (descending) within each query.

**Filter by minimum queries**:

```bash
uv run python scripts/aggregate_metapaths.py --min-queries 3 --output metapath_multi_query.tsv
```

Only include metapaths appearing in 3+ queries.

### Interpretation

- **Enrichment > 1.0**: Metapath is better than baseline for finding expected nodes
- **Enrichment = 0**: Metapath never finds expected nodes in that query
- **Frequency > 1.0**: Metapath appears multiple times per path on average
- **High `enrichment_min` with high `num_queries`**: Most reliable patterns
- **Common patterns with `enrichment_min = 0`**: Appear frequently but fail unpredictably

## Node Path Count Analysis

Analyze how frequently nodes appear in paths and how this relates to expected nodes.

### Running Node Path Count Analysis

```bash
uv run python scripts/analyze_node_path_counts.py
```

This generates:
- `node_path_counts.tsv`: Detailed per-query node statistics with columns:
  - `Query`: Query identifier
  - `CURIE`: Node identifier
  - `Path_Count`: Total number of paths this node appears in (excludes start/end nodes)
  - `Hit_Path_Count`: Number of "hit paths" (paths containing expected nodes) this node appears in
  - `Hit_Path_Fraction`: Fraction of all hit paths in this query that contain this node
  - `Is_Expected`: Whether this is an expected node
- `node_path_count_stats.tsv`: Summary statistics per query
- `node_path_count_distribution.png`: Violin plots showing path count distributions for expected vs other nodes per query

**Note**: Start and end nodes are excluded from counts since they appear in every path by definition.

### Visualizing Path Count vs Hit Fraction

Create scatter plots comparing node path counts to hit path fractions:

```bash
uv run python scripts/plot_path_count_vs_hit_fraction.py --input node_path_counts.tsv --output path_count_vs_hit_fraction.png
```

This generates a multi-panel plot with:
- One subplot per query (4 columns)
- X-axis: Path_Count (log scale if max > 100)
- Y-axis: Hit_Path_Fraction
- Colors: Red for expected nodes, Blue for other nodes
- Helps identify whether frequently-appearing nodes correlate with hit paths

## KGX Graph Node Degree Analysis

Calculate node degrees (number of unique neighbors) from KGX knowledge graph files.

### Running Node Degree Analysis

```bash
uv run python scripts/calculate_node_degrees.py \
  --edges /path/to/edges.jsonl \
  --nodes /path/to/nodes.jsonl \
  --output node_degrees.tsv
```

This generates `node_degrees.tsv` with columns:
- `Node_id`: CURIE identifier
- `Name`: Node name from KGX nodes file
- `Node_degree`: Number of unique nodes connected to this node
- `Information_content`: Information content value (when available in KGX nodes file)

### Node Degree Definition

- **Direction-agnostic**: Both incoming and outgoing edges count
- **Edge multiplicity ignored**: Multiple edges between same nodes = degree increment of 1
- **Unique neighbors**: Only counts distinct connected nodes

### Implementation Details

- **Streaming architecture**: Processes large KGX files without loading into memory
- **Pass 1**: Streams edges file to build neighbor sets per node
- **Pass 2**: Streams nodes file to calculate degrees and write output
- **Memory efficient**: Only stores `dict[node_id → set(neighbors)]` in memory

### Combining Path Counts with Node Degrees

Join path count analysis with ROBOKOP node degrees to understand whether hub nodes appear more frequently in paths:

```bash
uv run python scripts/join_path_counts_with_degrees.py \
  --path-counts node_path_counts.tsv \
  --node-degrees robokop_node_degrees.tsv \
  --output node_path_counts_with_degrees.tsv
```

This generates `node_path_counts_with_degrees.tsv` with combined data:
- All columns from `node_path_counts.tsv`
- `Name`: Node name from ROBOKOP graph
- `Node_degree`: Number of unique neighbors in ROBOKOP graph
- Left join: Keeps all path count nodes, fills missing ROBOKOP data with degree=0 and empty name
- Reports statistics on how many nodes were found vs not found in ROBOKOP

### Visualizing Node Characteristics

**Plot path count vs node degree by query** (colored by expected status):

```bash
uv run python scripts/plot_degree_vs_pathcount.py \
  --input node_path_counts_with_degrees.tsv \
  --output degree_vs_pathcount.png
```

Creates scatter plots (one per query) showing relationship between ROBOKOP node degree and path frequency, with expected nodes highlighted in red.

**Plot degree vs information content**:

```bash
uv run python scripts/plot_degree_vs_info_content.py \
  --input robokop_node_degrees.tsv \
  --output degree_vs_info_content.png
```

Creates two visualizations:
1. Scatter plot: Node degree (log scale) vs information content
2. Distribution: log₁₀(degree) / information_content ratio (log count scale)

Helps understand the relationship between node connectivity and information content in the knowledge graph.

## Project Structure

```
pathfilter/
├── src/pathfilter/          # Source code
│   ├── curie_utils.py       # CURIE parsing utilities
│   ├── query_loader.py      # Load queries from normalized JSON
│   ├── path_loader.py       # Load paths from xlsx files
│   ├── normalization.py     # Node normalizer API client
│   ├── matching.py          # Path/node matching (uses pre-normalized data)
│   ├── filters.py           # Filter functions
│   ├── evaluation.py        # Metrics calculation
│   ├── metapath_analysis.py # Metapath enrichment analysis
│   └── cli.py               # Command-line interface
├── tests/                   # Test suite (168 tests: 156 fast + 12 slow)
│   ├── test_normalize_input_data.py  # ODF parsing tests
│   └── test_query_loader.py          # JSON loading tests
├── input_data/              # Original test data (read-only)
│   ├── Pathfinder Test Queries.xlsx.ods
│   └── paths/               # Path xlsx files
├── normalized_input_data/   # Pre-normalized data (auto-generated)
│   ├── queries_normalized.json       # Pre-normalized queries with expected nodes
│   └── paths/                        # Pre-normalized path xlsx files
└── scripts/                 # Utility scripts
    ├── normalize_input_data.py         # Pre-normalization script (includes ODF parsing)
    ├── visualize_results.py            # Create filter enrichment visualizations
    ├── best_filters_table.py           # Generate best filters table
    ├── metapath_enrichment.py          # Analyze metapath enrichment per query
    ├── aggregate_metapaths.py          # Aggregate metapath stats across queries
    ├── sort_metapaths.py               # Sort metapath results
    ├── plot_metapath_scatter.py        # Frequency vs enrichment scatter plot
    ├── plot_metapath_consistency.py    # Consistency across queries plot
    ├── plot_unreliable_metapaths.py    # Complete misses analysis plot
    ├── analyze_node_path_counts.py     # Analyze node path counts and hit paths per query
    ├── plot_path_count_vs_hit_fraction.py # Scatter plots of path count vs hit fraction
    ├── calculate_node_degrees.py       # Calculate node degrees and information content from KGX files
    ├── join_path_counts_with_degrees.py # Join path counts with ROBOKOP node degrees
    ├── plot_degree_vs_pathcount.py     # Scatter plots of degree vs path count by query
    ├── plot_degree_vs_info_content.py  # Degree vs information content analysis
    └── normalize_missing_nodes.py      # Normalize CURIEs for missing expected nodes
```

### Key Architecture: Pre-Normalized Data

The system uses a **pre-normalized architecture** for performance and correctness:

1. **One-time normalization**: Run `scripts/normalize_input_data.py` to normalize all CURIEs upfront
   - Parses ODF query files and normalizes start/end/expected node CURIEs
   - Saves queries to `queries_normalized.json` for fast loading
   - Normalizes path files to `normalized_input_data/paths/`
2. **No API calls during evaluation**: Matching uses simple set operations on pre-normalized CURIEs
3. **16x faster**: ~0.7s vs 11s per query evaluation
4. **Consistent normalization**: Both path nodes AND expected nodes use the same normalized identifiers
   - **Critical fix**: Previously expected nodes weren't being normalized, causing false negatives
   - Example: `UniProtKB:P01375` (TNF protein) and `NCBIGene:7124` (TNF gene) are the same entity
   - Normalization maps both to `NCBIGene:7124` so matching works correctly
5. **Separation of concerns**:
   - `normalize_input_data.py` handles all ODF parsing and CURIE normalization
   - `query_loader.py` only loads from pre-normalized JSON (fast, simple)

## Running Tests

```bash
# Run fast tests (excludes slow integration tests)
uv run pytest -m "not slow"

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=pathfilter
```

## Development

### Environment

Always use `uv run` to execute commands in the isolated environment:

```bash
uv run pytest
uv run python -m pathfilter.cli
```

### Adding New Filters

1. Add filter function to `src/pathfilter/filters.py`
2. Add to `AVAILABLE_FILTERS` dict in `src/pathfilter/cli.py`
3. Write tests in `tests/test_filters.py`

### Code Quality

- Maintain high test coverage
- Use type hints
- Follow existing code structure
- Don't create classes just to group code (prefer functions)

## API Documentation

### Node Normalizer

Uses the Node Normalizer API at https://nodenormalization-sri.renci.org/ to:
- Map CURIEs to preferred identifiers
- Enable equivalent CURIE matching
- Apply gene/protein and drug/chemical conflation

### Input Data

- **Query Definitions**: `input_data/Pathfinder Test Queries.xlsx.ods`
  - Each query has start/end nodes and expected nodes to find
  - Expected nodes defined by CURIEs in column C
- **Path Data**: `input_data/paths/*.xlsx`
  - One file per query with ~5000-20000 paths
  - Contains path CURIEs, categories, predicates

## License

MIT License - See LICENSE file for details
