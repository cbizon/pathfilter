# PATHFINDER FILTER

## Basic Setup

* github: This project has a github repo at https://github.com/cbizon/pathfilter
* uv: we are using uv for package and environment management and an isolated environment
* tests: we are using pytest, and want to maintain high code coverage

### Environment Management - CRITICAL
**NEVER EVER INSTALL ANYTHING INTO SYSTEM LIBRARIES OR ANACONDA BASE ENVIRONMENT**
- ALWAYS use the isolated virtual environment at `.venv/`
- ALWAYS use `uv run` to execute commands, which automatically uses the isolated environment
- The virtual environment is sacred. System packages are not your garbage dump.

## Key Dependencies

### APIs

@nodenorm.md
@nameres.md

## Basic Workflow

Pathfinder is a method for finding paths in a graph between two nodes.  However, it generates too many paths. We are evaluating filters on the paths.   Each input query is a pair of nodes, and paths are generated.  We then have a filtering code that filters the paths down through different rules and combinations of rules.  Each inpt query also has a set of nodes that we would like to find on the path.  For each filter we can therefore evaluate how many of the acceptable paths are kept, and the enrichment of acceptable paths by filtering.

## Input

The input data may never be changed. 

The definitions of queries and expected results are found in input_data/Pathfinder\ Test\ Queries.xlsx.ods. There is an overall list sheet, but then a sheet per query.  Each query lists the input nodes as well as the nodes that we expect to find in the results.  The curies in column C are the definition of these expected nodes.  If there is nothing in column c for a row, we should ignore that row for the moment.  If there are no expected results for a query, we can ignore that query.

paths themselves are in input_data/paths.  Each query has its own xlsx file defined by the input curies.

KGX files are describe here:
@kgx.md

A KGX version of the ROBOKOP graph is found in 

## Project Structure

```
pathfilter/
├── src/pathfilter/          # Source code
│   ├── curie_utils.py       # CURIE parsing utilities
│   ├── query_loader.py      # Load queries from normalized JSON (NOT ODS)
│   ├── path_loader.py       # Load paths from xlsx files
│   ├── normalization.py     # Node Normalizer API client (batch processing)
│   ├── matching.py          # Path matching with expected nodes
│   ├── filters.py           # Filter functions (no_dupe_types, no_expression, etc.)
│   ├── evaluation.py        # Metrics calculation (recall, precision, enrichment)
│   └── cli.py               # Command-line interface
├── tests/                   # 94 tests (91 fast + 3 slow)
│   ├── test_normalize_input_data.py  # ODF parsing tests (slow)
│   ├── test_query_loader.py          # JSON loading tests
│   └── Run with: uv run pytest -m "not slow"
├── input_data/              # NEVER MODIFY - Read-only test data
│   ├── Pathfinder Test Queries.xlsx.ods
│   └── paths/*.xlsx
├── normalized_input_data/   # AUTO-GENERATED - Pre-normalized data
│   ├── queries_normalized.json       # Queries with normalized CURIEs
│   └── paths/*.xlsx                  # Paths with normalized CURIEs
├── archive/                 # Original prototype (filter.py, paths.tsv)
├── scripts/                 # Utility scripts
│   ├── normalize_input_data.py    # Pre-normalize CURIEs (includes ODF parsing)
│   ├── visualize_results.py       # Create enrichment bar charts per query
│   ├── best_filters_table.py      # Generate table of best filters by query
│   ├── analyze_node_path_counts.py # Analyze node path counts and hit paths per query
│   ├── plot_path_count_vs_hit_fraction.py # Scatter plots of path count vs hit fraction
│   ├── calculate_node_degrees.py  # Calculate node degrees and information content from KGX
│   ├── join_path_counts_with_degrees.py # Join path counts with ROBOKOP node degrees
│   ├── plot_degree_vs_pathcount.py      # Degree vs path count scatter plots by query
│   ├── plot_degree_vs_info_content.py   # Degree vs information content analysis
│   └── normalize_missing_nodes.py       # Normalize missing expected node CURIEs
└── docs/                    # Documentation
```

## Running Evaluations

### **FIRST TIME SETUP** - Normalize Input Data
```bash
uv run python scripts/normalize_input_data.py
```
This creates `normalized_input_data/` with pre-normalized CURIEs. Only run once or when input data changes.

### Running Evaluations

**Evaluate all queries with all filter combinations (default):**
```bash
uv run python -m pathfilter.cli --output results.tsv
```
This tests 64 filter combinations (6 individual filters, all combinations) across all queries (~1 minute for 20 queries).

**Performance**: Uses optimized caching - applies each filter once, uses set intersections for combinations. O(N×F) instead of O(N×F×C) complexity.

**Evaluate specific query:**
```bash
uv run python -m pathfilter.cli --query PFTQ-4 --output results.tsv
```

**Custom filter combinations:**
```bash
uv run python -m pathfilter.cli --filters "no_dupe_types|no_expression" --output results.tsv
```

### Visualizing Results

**Create enrichment bar charts for each query:**
```bash
uv run python scripts/visualize_results.py --results all_filter_results.tsv --output enrichment_by_query.png
```
Generates PNG visualization with single-column horizontal bar layout (optimized for 64 combinations), subplots for each query showing enrichment vs filters.

**Generate table of best filters per query:**
```bash
uv run python scripts/best_filters_table.py --results all_filter_results.tsv --output best_filters.tsv
```
Creates a TSV table sorted by enrichment showing the best filter for each query (favoring simpler filters in ties).

## Key Implementation Details

### **Pre-Normalized Architecture (CRITICAL!)**

**IMPORTANT FIX**: Expected nodes are now properly normalized to fix false negatives.

**Architecture**:
1. **normalize_input_data.py** (run once):
   - Parses ODS query files (handles "garbagey" concatenated CURIEs in column C)
   - Normalizes ALL CURIEs (start, end, expected nodes) via Node Normalizer API
   - Saves to `normalized_input_data/queries_normalized.json` (avoids ODF writing complexity)
   - Normalizes path xlsx files to `normalized_input_data/paths/`

2. **query_loader.py** (during evaluation):
   - ONLY loads from `queries_normalized.json` (no ODF parsing, no API calls)
   - Auto-detects JSON if given ODS path
   - Returns Query objects with pre-normalized CURIEs

3. **matching.py** (during evaluation):
   - Simple set operations on normalized CURIEs (no API calls)
   - Path nodes: normalized ✓
   - Expected nodes: normalized ✓
   - Apples-to-apples comparison!

**Critical Bug Fixed**:
- Previously: Expected nodes NOT normalized → false negatives
- Example: `UniProtKB:P01375` (TNF protein) vs `NCBIGene:7124` (TNF gene) = MISS ✗
- Now: Both normalize to `NCBIGene:7124` = HIT ✓

**Performance**:
- 16x faster: 0.7s vs 11s per query
- No redundant API calls during evaluation
- Normalization batched efficiently in preprocessing

### Node Normalization Details
- Uses Node Normalizer API: https://nodenormalization-sri.renci.org/
- Conflation enabled: drug_chemical_conflate=True, conflate=True
- Returns preferred (clique leader) identifiers
- ~96% of CURIEs already normalized, but architecture ensures consistency

### Filter Functions
Migrated from archive/filter.py and adapted for Path objects:
- `no_dupe_types`: Ensures 4 unique node types (ChemicalEntity variants → ChemicalEntity, Protein → Gene)
- `no_expression`: Filters out "expressed_in" predicates
- `no_related_to`: Removes generic "related_to" predicates
- `no_end_pheno`: Filters paths ending with PhenotypicFeature → SmallMolecule
- `no_chemical_start`: Removes Disease → Chemical starts
- `no_repeat_predicates`: Removes paths where same predicate appears multiple times
- `no_abab`: Removes alternating type patterns (A→B→A→B) with type equivalences (Disease/PhenotypicFeature, Chemical variants, Gene/Protein)
- Pre-defined sets: DEFAULT_FILTERS, STRICT_FILTERS

**Performance Optimization**: `evaluate_multiple_strategies()` uses caching - applies each filter once, generates combinations via set intersections. O(N×F) instead of O(N×F×C) complexity.

### Evaluation Metrics
- **Recall**: (expected paths kept) / (expected paths total)
- **Precision**: (expected paths) / (total paths)
- **Enrichment**: precision_after / precision_before
- **Retention Rate**: paths_after / paths_before
- **Expected Nodes Recall**: (unique nodes kept) / (unique nodes total)

## Testing

**Fast tests (for development):**
```bash
uv run pytest -m "not slow"  # 104 tests in ~8 seconds
```

**All tests (including slow integration tests):**
```bash
uv run pytest  # 116 tests in ~2 minutes
```

Tests marked with `@pytest.mark.slow` load real data files and make API calls.

## Key Ideas

## ***RULES OF THE ROAD***

- Ask clarifying questions

- Don't make classes just to group code. It is non-pythonic and hard to test.

- Do not implement bandaids - treat the root cause of problems

- Don't use try/except as a way to hide problems.  It is often good just to let something fail and figure out why.

- Once we have a test, do not delete it without explicit permission.  

- Do not return made up results if an API fails.  Let it fail.

- If you cannot access a file, do not just guess at its contents - come back and ask for help

- When changing code, don't make duplicate functions - just change the function. We can always roll back changes if needed.

- Keep the directories clean, don't leave a bunch of junk laying around.

- When making pull requests, NEVER ever mention a `co-authored-by` or similar aspects. In particular, never mention the tool used to create the commit message or PR.

- Check git status before commits
- Use tsv not csv.
- For visualizations, output PNG only. Never create PDF files.
