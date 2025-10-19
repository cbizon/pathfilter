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


## Project Structure

```
pathfilter/
├── src/pathfilter/          # Source code
│   ├── curie_utils.py       # CURIE parsing utilities
│   ├── query_loader.py      # Load query definitions from .ods file
│   ├── path_loader.py       # Load paths from xlsx files
│   ├── normalization.py     # Node Normalizer API client (batch processing)
│   ├── matching.py          # Path matching with expected nodes
│   ├── filters.py           # Filter functions (no_dupe_types, no_expression, etc.)
│   ├── evaluation.py        # Metrics calculation (recall, precision, enrichment)
│   └── cli.py               # Command-line interface
├── tests/                   # 94 tests (91 fast + 3 slow)
│   ├── test_*.py           # Unit tests for each module
│   └── Run with: uv run pytest -m "not slow"
├── input_data/              # NEVER MODIFY - Read-only test data
│   ├── Pathfinder Test Queries.xlsx.ods
│   └── paths/*.xlsx
├── archive/                 # Original prototype (filter.py, paths.tsv)
├── scripts/                 # Utility scripts
└── docs/                    # Documentation
```

## Running Evaluations

**Main command to run all evaluations:**
```bash
uv run python -m pathfilter.cli
```

**Evaluate specific query:**
```bash
uv run python -m pathfilter.cli --query PFTQ-4
```

**Compare filter strategies:**
```bash
uv run python -m pathfilter.cli --filters "default|strict|none"
```

**Export results to CSV:**
```bash
uv run python -m pathfilter.cli --output results.csv
```

## Key Implementation Details

### Node Normalization
- Uses Node Normalizer API with conflation enabled (drug_chemical_conflate=True, conflate=True)
- Batch processing: Collects all unique CURIEs from paths and normalizes in ONE API call
- Caches results with @lru_cache for efficiency
- Matches paths to expected nodes using normalized (preferred) identifiers

### Filter Functions
Migrated from archive/filter.py and adapted for Path objects:
- `no_dupe_types`: Ensures 4 unique node types (ChemicalEntity variants → ChemicalEntity, Protein → Gene)
- `no_expression`: Filters out "expressed_in" predicates
- `no_related_to`: Removes generic "related_to" predicates
- `no_end_pheno`: Filters paths ending with PhenotypicFeature → SmallMolecule
- `no_chemical_start`: Removes Disease → Chemical starts
- Pre-defined sets: DEFAULT_FILTERS, STRICT_FILTERS

### Evaluation Metrics
- **Recall**: (expected paths kept) / (expected paths total)
- **Precision**: (expected paths) / (total paths)
- **Enrichment**: precision_after / precision_before
- **Retention Rate**: paths_after / paths_before
- **Expected Nodes Recall**: (unique nodes kept) / (unique nodes total)

## Testing

**Fast tests (for development):**
```bash
uv run pytest -m "not slow"  # 91 tests in ~18 seconds
```

**All tests (including slow integration tests):**
```bash
uv run pytest  # 94 tests in ~2 minutes
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

