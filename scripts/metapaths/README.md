# Metapath Analysis Scripts

## Overview

These scripts use **GraphBLAS sparse matrix multiplication** to compute all possible N-hop metapaths in the ROBOKOP knowledge graph and analyze their relationships with 1-hop edges.

## Key Approach: Matrix Multiplication

Instead of iteratively joining paths (which requires huge disk space), we represent the graph as sparse boolean matrices where each `(source_type, predicate, target_type)` triple gets its own matrix. Then:

- **1-hop paths**: Direct matrix entries
- **2-hop paths**: `A @ B` (matrix multiplication)
- **3-hop paths**: `(A @ B) @ C`
- **N-hop paths**: Continue multiplying

This approach keeps memory constant (~2GB) by using sparse matrices and never materializing full path lists.

## Scripts

### 1. `analyze_3hop_overlap.py` (Main Script)

Computes all 3-hop metapaths via triple matrix multiplication and calculates overlap with 1-hop edges.

**What it does:**
1. Loads KGX nodes and edges files
2. Builds sparse boolean matrices for each `(source_type, predicate, target_type)` triple
3. Creates forward (F) and reverse (R) versions for non-symmetric predicates
4. Computes all valid 3-hop combinations: `(Matrix1 @ Matrix2) @ Matrix3`
5. For each 3-hop result, compares with all matching 1-hop matrices to find overlap
6. Outputs TSV with columns: `3hop_metapath | 3hop_count | 1hop_metapath | 1hop_count | overlap | total_possible`

**Usage:**
```bash
uv run python scripts/metapaths/analyze_3hop_overlap.py \
    --edges ../SimplePredictions/input_graphs/robokop_base_nonredundant/edges.jsonl \
    --nodes ../SimplePredictions/input_graphs/robokop_base_nonredundant/nodes.jsonl \
    --output 3hop_1hop_overlap.tsv
```

**Output format:**
```
3hop_metapath                                                          3hop_count  1hop_metapath                      1hop_count  overlap  total_possible
SmallMolecule|affects|F|Gene|affects|R|SmallMolecule|affects|F|Gene   6173251587  SmallMolecule|affects|R|Gene       529197      5914     201487065416
SmallMolecule|affects|F|Gene|affects|R|SmallMolecule|affects|F|Gene   6173251587  SmallMolecule|related_to|F|Gene    687086      192170   201487065416
SmallMolecule|affects|F|Gene|affects|R|SmallMolecule|affects|F|Gene   6173251587  SmallMolecule|ANY|A|Gene           2946957     1808775  201487065416
```

**Metapath format:** `NodeType|predicate|direction|NodeType|predicate|direction|...`
- Pipe-separated
- `F` = forward (follow edge as-is)
- `R` = reverse (follow edge backwards)
- `ANY|A` = aggregated across all predicates and directions

**Performance:**
- Memory: ~2GB (constant, thanks to sparse matrices)
- Time: ~8-12 hours for full ROBOKOP 3-hop analysis
- Output: ~370 rows for typical graphs (26 unique 3-hop patterns × ~15 1-hop comparisons each)

### 2. `estimate_total_runtime.py`

Estimates total runtime by computing the size distribution of all Matrix3 iterations without actually running them.

**Strategy:**
1. For each valid Matrix1/Matrix2 combo, compute `A @ B` (fast)
2. Count how many Matrix3 iterations will use each `A @ B` result
3. Bucket by result size
4. Use benchmark timing data to estimate total runtime

**Usage:**
```bash
uv run python scripts/metapaths/estimate_total_runtime.py \
    --edges ../SimplePredictions/input_graphs/robokop_base_nonredundant/edges.jsonl \
    --nodes ../SimplePredictions/input_graphs/robokop_base_nonredundant/nodes.jsonl \
    --benchmark matrix_timing_benchmark.tsv
```

### 3. `generate_benchmark_samples.py`

Creates stratified samples of matrix multiplication operations for benchmarking.

**What it does:**
- Samples Matrix2 and Matrix3 operations across different size ranges
- Creates a representative set of operations to benchmark
- Outputs TSV with sampled operations and their characteristics

**Usage:**
```bash
uv run python scripts/metapaths/generate_benchmark_samples.py \
    --edges ../SimplePredictions/input_graphs/robokop_base_nonredundant/edges.jsonl \
    --nodes ../SimplePredictions/input_graphs/robokop_base_nonredundant/nodes.jsonl \
    --output benchmark_samples.tsv
```

### 4. `run_benchmark_samples.py`

Runs actual matrix multiplication operations from benchmark samples and records timing.

**Usage:**
```bash
uv run python scripts/metapaths/run_benchmark_samples.py \
    --edges ../SimplePredictions/input_graphs/robokop_base_nonredundant/edges.jsonl \
    --nodes ../SimplePredictions/input_graphs/robokop_base_nonredundant/nodes.jsonl \
    --samples benchmark_samples.tsv \
    --output matrix_timing_benchmark.tsv
```

### 5. `analyze_3hop_prediction.py`

Analyzes how well 3-hop metapaths predict 1-hop edges using classification metrics.

**What it does:**
1. Reads `3hop_1hop_overlap.tsv` from `analyze_3hop_overlap.py`
2. Treats each 3-hop metapath as a binary predictor of 1-hop edges
3. Calculates precision, recall, F1, MCC, etc. for each (3-hop, 1-hop) pair
4. Outputs detailed metrics and summary statistics

**Usage:**
```bash
uv run python scripts/metapaths/analyze_3hop_prediction.py
```

**Input:** Requires `3hop_1hop_overlap.tsv` in project root

**Output:**
- `metapath_prediction_metrics.tsv` - Detailed metrics for all pairs
- `metapath_prediction_by_3hop.tsv` - Aggregated by 3-hop metapath
- Console output with summary statistics and top predictions

### 6. `analyze_3hop_prediction.ipynb`

Interactive Jupyter notebook for exploring 3-hop prediction metrics with visualizations.

**Features:**
- Filter predictions by start/end node types (e.g., SmallMolecule → Disease)
- Display sorted by precision, recall, or F1
- Precision-recall scatter plots (log and linear scale)
- Pareto frontier analysis (optimal precision-recall tradeoffs)
- Summary statistics by prediction type

**Usage:**
```bash
jupyter notebook scripts/metapaths/analyze_3hop_prediction.ipynb
```

### 7. `type_utils.py`

Utility functions for handling Biolink node types.

**Key function:**
- `get_most_specific_type(categories)` - Returns the most specific Biolink type from a list

## Complete Workflow

### Generate 3-hop overlap analysis:

```bash
# Step 1: Compute all 3-hop metapaths and their overlap with 1-hop edges
uv run python scripts/metapaths/analyze_3hop_overlap.py \
    --edges ../SimplePredictions/input_graphs/robokop_base_nonredundant/edges.jsonl \
    --nodes ../SimplePredictions/input_graphs/robokop_base_nonredundant/nodes.jsonl \
    --output 3hop_1hop_overlap.tsv

# Step 2: Analyze 3-hop as predictors of 1-hop
uv run python scripts/metapaths/analyze_3hop_prediction.py

# Step 3: Explore interactively (optional)
jupyter notebook scripts/metapaths/analyze_3hop_prediction.ipynb
```

### Benchmark and estimate runtime (optional):

```bash
# Step 1: Generate benchmark samples
uv run python scripts/metapaths/generate_benchmark_samples.py \
    --edges ../SimplePredictions/input_graphs/robokop_base_nonredundant/edges.jsonl \
    --nodes ../SimplePredictions/input_graphs/robokop_base_nonredundant/nodes.jsonl \
    --output benchmark_samples.tsv

# Step 2: Run benchmarks
uv run python scripts/metapaths/run_benchmark_samples.py \
    --edges ../SimplePredictions/input_graphs/robokop_base_nonredundant/edges.jsonl \
    --nodes ../SimplePredictions/input_graphs/robokop_base_nonredundant/nodes.jsonl \
    --samples benchmark_samples.tsv \
    --output matrix_timing_benchmark.tsv

# Step 3: Estimate total runtime before running full analysis
uv run python scripts/metapaths/estimate_total_runtime.py \
    --edges ../SimplePredictions/input_graphs/robokop_base_nonredundant/edges.jsonl \
    --nodes ../SimplePredictions/input_graphs/robokop_base_nonredundant/nodes.jsonl \
    --benchmark matrix_timing_benchmark.tsv
```

## Key Concepts

### Metapath Format

Metapaths are pipe-separated strings encoding the path through the knowledge graph:

```
NodeType|predicate|direction|NodeType|predicate|direction|NodeType|predicate|direction|NodeType
```

**Example:** `SmallMolecule|affects|F|Gene|affects|R|SmallMolecule|treats|R|Disease`

- Start: `SmallMolecule`
- Edge 1: `affects` (Forward) → `Gene`
- Edge 2: `affects` (Reverse) ← `SmallMolecule`
- Edge 3: `treats` (Reverse) ← `Disease`

### Symmetric Predicates

Some predicates are symmetric (A→B implies B→A), so we don't create reverse versions:
- `interacts_with`
- `correlated_with`
- `associated_with`
- `similar_to`
- `related_to`
- etc.

### Aggregated (ANY) Metapaths

For each 3-hop pattern, we also compute overlap with "ANY" 1-hop - the union of all 1-hop edges between the same start/end types, regardless of predicate or direction.

Format: `StartType|ANY|A|EndType`

Example: `SmallMolecule|ANY|A|Gene` represents any connection from SmallMolecule to Gene.

## Performance Characteristics

### Memory Usage

**Constant ~2GB** regardless of graph size, thanks to:
- Sparse boolean matrices (only store edges, not empty cells)
- No materialization of full path lists
- Streaming processing of matrix operations

### Disk Usage

**Minimal** - only output files:
- `3hop_1hop_overlap.tsv`: ~50KB-5MB depending on graph
- `metapath_prediction_metrics.tsv`: ~200KB-10MB

No large intermediate files needed!

### Runtime

For full ROBOKOP graph (~20M nodes, ~180M edges):
- **1-hop matrix construction**: ~5 minutes
- **3-hop computation**: ~8-12 hours
- **Prediction analysis**: ~1 minute

Runtime scales with:
- Number of edge type triples
- Number of valid 3-hop combinations
- Density of resulting matrices

## Troubleshooting

### "Out of memory" error
- Should not happen with GraphBLAS sparse matrices
- If it does, reduce graph size or increase system RAM

### Process seems slow
- 3-hop analysis takes hours - this is expected
- Monitor progress messages (prints every Matrix2/Matrix3 iteration)
- Check memory usage stays constant (~2GB)

### Missing dependencies
```bash
# Install GraphBLAS (required)
uv add python-graphblas

# Install Jupyter (for notebooks)
uv add jupyter
```

## Technical Details

### Why GraphBLAS?

Traditional path enumeration approaches require storing and joining huge lists of paths:
- 1-hop: ~10M paths
- 2-hop: ~1B paths (100GB+ disk space)
- 3-hop: ~100B paths (10TB+ disk space)

GraphBLAS sparse matrices:
- Never materialize full path lists
- Only track existence of connections (boolean)
- Use optimized C libraries for sparse operations
- Memory usage: O(edges) not O(paths)

### Algorithm Complexity

For 3-hop computation:
- **Time**: O(M1 × M2 × M3) where M = number of edge type triples
- **Space**: O(edges in graph) - sparse matrix storage
- **Output**: O(3-hop patterns × 1-hop patterns) - typically ~300-500 rows

Compared to naive enumeration:
- **Time**: Similar (still need to multiply)
- **Space**: 1000x less (no materialization)
- **Scalability**: Can handle graphs with billions of paths

## Future Extensions

Potential enhancements:
1. **4-hop and beyond**: Extend to N-hop with configurable depth
2. **Selective computation**: Only compute specific start/end type combinations
3. **Path weighting**: Use float matrices to track path scores/probabilities
4. **Distributed computation**: Parallelize across multiple machines
5. **Incremental updates**: Efficiently update when graph changes
