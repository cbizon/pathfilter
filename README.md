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

### Required Directory Structure

```
pathfilter/
├── input_data/
│   ├── Pathfinder Test Queries.xlsx.ods  # Query definitions
│   └── paths/                             # Path data files
│       ├── CHEBI_15647_to_UNII_31YO63LBSN.xlsx
│       ├── CHEBI_27881_to_NCBIGene_2739_paths.xlsx
│       ├── ... (one xlsx file per query)
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

### Evaluate a Single Query

```bash
uv run python -m pathfilter.cli --query PFTQ-4
```

### Evaluate All Queries

```bash
uv run python -m pathfilter.cli
```

### Compare Filter Strategies

```bash
# Compare default vs strict filtering
uv run python -m pathfilter.cli --filters "default|strict"

# Use specific filters
uv run python -m pathfilter.cli --filters "no_dupe_types,no_expression"
```

### Export Results to CSV

```bash
uv run python -m pathfilter.cli --output results.csv
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

## Project Structure

```
pathfilter/
├── src/pathfilter/          # Source code
│   ├── curie_utils.py       # CURIE parsing
│   ├── query_loader.py      # Query definitions
│   ├── path_loader.py       # Path data loading
│   ├── normalization.py     # Node normalizer API
│   ├── matching.py          # Path/node matching
│   ├── filters.py           # Filter functions
│   ├── evaluation.py        # Metrics calculation
│   └── cli.py               # Command-line interface
├── tests/                   # Test suite (94 tests)
├── input_data/              # Test data
│   ├── Pathfinder Test Queries.xlsx.ods
│   └── paths/               # Path xlsx files
└── scripts/                 # Utility scripts
    └── run_evaluation.py
```

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
