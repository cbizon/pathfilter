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
uv run python -m pathfilter.cli --output results.csv
```

This evaluates 16 filter combinations (1 baseline + 4 individual + 6 pairs + 4 triplets + 1 all) across all queries (~5-10 minutes for 20 queries). Results are written to CSV for analysis.

### Evaluate a Single Query

```bash
uv run python -m pathfilter.cli --query PFTQ-4 --output results.csv
```

### Compare Specific Filter Strategies

```bash
# Compare default vs strict filtering
uv run python -m pathfilter.cli --filters "default|strict" --output results.csv

# Use specific filters
uv run python -m pathfilter.cli --filters "no_dupe_types,no_expression" --output results.csv
```

## Available Filters

- **default**: `no_dupe_types` + `no_expression` + `no_related_to`
- **strict**: default filters + `no_end_pheno`
- **Individual filters**:
  - `no_dupe_types`: Remove paths with duplicate node types
  - `no_expression`: Filter out `expressed_in` predicates
  - `no_related_to`: Remove generic `related_to` predicates
  - `no_end_pheno`: Filter paths ending with PhenotypicFeature→SmallMolecule
  - `no_chemical_start`: Remove paths starting with Disease→Chemical
  - `all_paths`: No filtering (baseline)

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
uv run python scripts/visualize_results.py --results all_filter_results.csv --output enrichment_by_query.png
```

This generates:
- PNG file with subplots for each query
- PDF version for publication-quality graphics
- Color-coded bars (green: strong enrichment, blue: moderate, coral: harmful)
- Query titles with start/end node labels

### Generate Best Filters Table

Create a summary table showing the best filter for each query:

```bash
uv run python scripts/best_filters_table.py --results all_filter_results.csv --output best_filters.tsv
```

Output includes:
- Query ID and descriptive name
- Best filter (or "none" if no filter improves results)
- Enrichment factor
- Sorted by enrichment (highest to lowest)
- Statistics on most common effective filters

## Project Structure

```
pathfilter/
├── src/pathfilter/          # Source code
│   ├── curie_utils.py       # CURIE parsing
│   ├── query_loader.py      # Query definitions
│   ├── path_loader.py       # Path data loading
│   ├── normalization.py     # Node normalizer API
│   ├── matching.py          # Path/node matching (uses pre-normalized data)
│   ├── filters.py           # Filter functions
│   ├── evaluation.py        # Metrics calculation
│   └── cli.py               # Command-line interface
├── tests/                   # Test suite (94 tests)
├── input_data/              # Original test data (read-only)
│   ├── Pathfinder Test Queries.xlsx.ods
│   └── paths/               # Path xlsx files
├── normalized_input_data/   # Pre-normalized data (auto-generated)
│   ├── Pathfinder Test Queries.xlsx.ods
│   └── paths/               # Pre-normalized path xlsx files
└── scripts/                 # Utility scripts
    ├── normalize_input_data.py    # Pre-normalization script
    ├── visualize_results.py       # Create enrichment visualizations
    └── best_filters_table.py      # Generate best filters table
```

### Key Architecture: Pre-Normalized Data

The system uses a **pre-normalized architecture** for performance:

1. **One-time normalization**: Run `scripts/normalize_input_data.py` to normalize all CURIEs upfront
2. **No API calls during evaluation**: Matching uses simple set operations on pre-normalized CURIEs
3. **16x faster**: ~0.7s vs 11s per query evaluation
4. **~96% already normalized**: Most CURIEs don't change, but the architecture avoids redundant API calls

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
