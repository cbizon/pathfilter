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
├── tests/                   # 168 tests (156 fast + 12 slow)
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
│   ├── plot_precision_recall.py   # Create Pareto front precision-recall plots
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

### **Complete Workflow** - Use rerun_all.sh

The complete analysis workflow is automated in `rerun_all.sh`. This script ensures node characteristics are calculated BEFORE filtering (required for node-based filters):

```bash
./rerun_all.sh
```

**Workflow steps:**
1. **Normalize input data** - Pre-normalize all CURIEs (only needed when input data changes)
2. **Calculate node degrees** - Extract node degree and information content from ROBOKOP KGX files
3. **Analyze node path counts** - Count how many paths each node appears in
4. **Join characteristics** - Combine node degrees, information content, and path counts into unified dataset
5. **Run filter evaluations** - Test all filter combinations (can now use node characteristics)
6. **Generate visualizations** - Create enrichment charts and tables
7. **Metapath analysis** - Analyze metapath patterns
8. **Additional visualizations** - Path count scatter plots, etc.

### **Manual Steps** (if needed)

**STEP 1: Normalize Input Data** (only run once or when input data changes)
```bash
uv run python scripts/normalize_input_data.py
```
This creates `normalized_input_data/` with pre-normalized CURIEs.

**STEP 2: Calculate Node Characteristics** (required before filtering with node-based filters)
```bash
# Calculate node degrees and information content from ROBOKOP
uv run python scripts/calculate_node_degrees.py \
  --edges ../SimplePredictions/input_graphs/robokop_base_nonredundant/edges.jsonl \
  --nodes ../SimplePredictions/input_graphs/robokop_base_nonredundant/nodes.jsonl \
  --output robokop_node_degrees.tsv

# Analyze how many paths each node appears in
uv run python scripts/analyze_node_path_counts.py

# Combine all node characteristics into one file
uv run python scripts/join_path_counts_with_degrees.py \
  --path-counts node_path_counts.tsv \
  --node-degrees robokop_node_degrees.tsv \
  --output node_path_counts_with_degrees.tsv
```

This creates `node_path_counts_with_degrees.tsv` with columns:
- `Node_id`, `Name`, `Query`, `Node_type`
- `Path_count` (how many paths the node appears in)
- `Hit_paths` (how many paths with expected nodes)
- `Node_degree` (connections in ROBOKOP graph)
- `Information_content` (specificity metric from Node Normalizer)

**STEP 3: Run Filter Evaluations**

**Evaluate all queries with all filter combinations (default):**
```bash
uv run python -m pathfilter.cli --output results.tsv
```
This tests all filter combinations across all queries (~1 minute for 20 queries).

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

**Create enrichment bar charts for each query (frontier visualization):**
```bash
uv run python scripts/visualize_results.py --results all_filter_results.tsv --output enrichment_by_query.png
```
Generates PNG visualization using **frontier filtering** to reduce clutter:
- Shows ALL individual filters (to see baseline performance)
- Only shows combinations that set new best/worst enrichment records
- Reduces 1,792 combinations → ~10-20 bars per query
- Filter labels prefixed with `[combo_size]` for clarity
- Color coded: Green (>1.5x), Blue (≥1.0x), Coral (<1.0x)

**Generate table of best filters per query:**
```bash
uv run python scripts/best_filters_table.py --results all_filter_results.tsv --output best_filters.tsv
```
Creates a TSV table sorted by enrichment showing the best filter for each query (favoring simpler filters in ties).

**Create precision-recall Pareto front plots:**
```bash
uv run python scripts/plot_precision_recall.py --results all_filter_results.tsv --output precision_recall.png --pareto-output pareto_optimal_points.tsv
```
Generates visualization and table of Pareto optimal filter combinations:
- **PNG output**: One subplot per query showing precision vs recall scatter plot
  - Blue dots: Dominated filter combinations
  - Red stars: Pareto optimal (non-dominated) filters
  - Legend on right: Lists filtered Pareto points with precision/recall values
  - Subplot titles include query ID and descriptive name (e.g., "PFTQ-10: imatinib → asthma")
- **TSV output**: Table of Pareto optimal points with columns: `Query | rule | precision | recall`
  - Automatically filters out (0, 0) points
  - Removes redundant filter combinations (only keeps simplest filters when multiple have same precision/recall)
  - Example: If "no_dupe_types, no_expression" and "no_dupe_types, no_expression, no_related_to" have identical values, only the simpler one is kept
  - Sorted by query, then precision (descending)

**Pareto optimality**: A filter combination is Pareto optimal if no other combination achieves both higher precision AND higher recall. These represent the best tradeoff choices between the two metrics.

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

### Node Characteristics Data

**IMPORTANT**: Node-based filters require pre-computed node characteristics. Run `rerun_all.sh` or manually calculate before filtering.

**Data Pipeline**:
1. **calculate_node_degrees.py**: Extracts from ROBOKOP KGX files
   - Node degree: Number of unique connections in ROBOKOP graph
   - Information content: Specificity metric from Node Normalizer (higher = more specific)
   - Output: `robokop_node_degrees.tsv`

2. **analyze_node_path_counts.py**: Analyzes path frequency per query
   - Path_count: How many paths the node appears in
   - Hit_paths: How many paths contain expected nodes
   - Output: `node_path_counts.tsv`

3. **join_path_counts_with_degrees.py**: Combines both datasets
   - Joins on normalized node IDs
   - Tracks missing expected nodes separately
   - Output: `node_path_counts_with_degrees.tsv`

**Node Characteristics Available for Filtering**:
- **Information Content**: Higher values = more specific/rare nodes (e.g., rare diseases have high IC)
- **Node Degree**: Higher values = more connected/promiscuous nodes (e.g., TNF, TP53)
- **Path Count**: How many paths a node appears in (per query)

These characteristics enable filtering strategies like:
- Remove high-degree hub nodes (reduces noise)
- Keep high information content nodes (increases specificity)
- Filter by path count thresholds (balance recall/precision)

### Filter Functions

**Path-Based Filters** (8 total):
- `no_dupe_types`: Ensures 4 unique node types (ChemicalEntity variants → ChemicalEntity, Protein → Gene)
- `no_dupe_but_gene`: Like no_dupe_types, but allows Gene/Protein duplicates while requiring all other types unique
- `no_nonconsecutive_dupe`: Removes paths where same type appears non-consecutively (A→B→A filtered, A→A→B allowed)
- `no_expression`: Filters out "expressed_in" predicates
- `no_related_to`: Removes generic "related_to" predicates
- `no_end_pheno`: Filters paths ending with PhenotypicFeature → SmallMolecule
- `no_chemical_start`: Removes Disease → Chemical starts
- `no_repeat_predicates`: Removes paths where same predicate appears multiple times
- `no_abab`: Removes alternating type patterns (A→B→A→B) with type equivalences (Disease/PhenotypicFeature, Chemical variants, Gene/Protein)

**Node-Based Filters** (require node_path_counts_with_degrees.tsv):
- **IC filters**: `min_ic_30`, `min_ic_50`, `min_ic_70` - Remove paths with any intermediate node having information content < threshold
- **Degree filters**: `max_degree_1000`, `max_degree_5000`, `max_degree_10000` - Remove paths with any intermediate node having degree > threshold
- Nodes with missing IC treated as 100.0 (very specific, pass all thresholds)
- Nodes with missing degree treated as 0 (no connections, pass all max_degree thresholds)
- Only check intermediate nodes (positions 1 and 2), NOT start/end nodes (query-specific)
- Node filters NEVER combined with each other, only with path-based filters

**Pre-defined Filter Sets**:
- `DEFAULT_FILTERS`: no_dupe_types + no_expression + no_related_to
- `STRICT_FILTERS`: DEFAULT_FILTERS + no_end_pheno

**Performance Optimization**:
- `evaluate_multiple_strategies()` uses caching - applies each filter once, generates combinations via set intersections
- O(N×F) instead of O(N×F×C) complexity
- Smart combination logic prevents redundant node filter combinations
- With 8 path filters + 6 node filters: 1,792 combinations (2^8 × 7)

### Evaluation Metrics
- **Recall**: (expected paths kept) / (expected paths total)
- **Precision**: (expected paths) / (total paths)
- **Enrichment**: precision_after / precision_before
- **Retention Rate**: paths_after / paths_before
- **Expected Nodes Recall**: (unique nodes kept) / (unique nodes total)

## Testing

**Fast tests (for development):**
```bash
uv run pytest -m "not slow"  # 156 tests in ~7 seconds
```

**All tests (including slow integration tests):**
```bash
uv run pytest  # 168 tests in ~2 minutes
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
