# Metapath Generation Scripts

## Overview

These scripts generate N-hop metapaths from the ROBOKOP knowledge graph by iteratively joining 1-hop connections.

## Scripts

### 1. `extract_1hop_metapaths.py`
Extracts all 1-hop metapaths from ROBOKOP edges.jsonl.

**Output format:**
```
node_A    node_B    metapath    count
```

**Usage:**
```bash
uv run python scripts/metapaths/extract_1hop_metapaths.py \
    --edges ../SimplePredictions/input_graphs/robokop_base_nonredundant/edges.jsonl \
    --nodes ../SimplePredictions/input_graphs/robokop_base_nonredundant/nodes.jsonl \
    --output 1hop_metapaths.tsv \
    --exclude-predicates biolink:subclass_of
```

### 2. `extend_metapaths.py` (ORIGINAL - Memory-intensive)
Extends N-hop metapaths to (N+1)-hop by joining with 1-hop paths.

**Memory usage:** O(N-hop size + output size) - **NOT RECOMMENDED for N > 2**

**Problems:**
- Loads entire N-hop file into memory
- Accumulates all output in Counter before writing
- Memory explodes for 3+ hops (can exceed 100GB)

**When to use:**
- Small datasets only
- 1-hop → 2-hop conversion where you have plenty of RAM

### 3. `extend_metapaths_chunked.py` (RECOMMENDED)
Chunked processing with incremental aggregation.

**Memory usage:** O(1-hop index) - typically **~500MB-2GB regardless of N**

**Disk space:** O(chunk_size × avg_joins) - **manageable** (default: ~30GB per chunk)

**How it works:**
1. Loads 1-hop index into memory (only data structure kept in RAM)
2. Processes N-hop file in chunks (default: 500K rows)
3. For each chunk:
   - Generates joins to temp file (~30GB)
   - Aggregates with DuckDB (reduces to ~5-10GB)
   - Deletes temp file, keeps aggregated result
4. Merges all aggregated chunks at the end

**Advantages:**
- ✅ Uses ~100x less memory than original
- ✅ Uses ~10-20x less disk space than streaming version
- ✅ Handles arbitrarily large N-hop files
- ✅ Progress visible per chunk

**Usage:**

```bash
# Default chunk size (500K rows) - recommended
uv run python scripts/metapaths/extend_metapaths_chunked.py \
    --nhop 1hop_metapaths.tsv \
    --onehop 1hop_metapaths.tsv \
    --output 2hop_metapaths.tsv

# Smaller chunks (uses less disk space, slightly slower)
uv run python scripts/metapaths/extend_metapaths_chunked.py \
    --nhop 1hop_metapaths.tsv \
    --onehop 1hop_metapaths.tsv \
    --output 2hop_metapaths.tsv \
    --chunk-size 250000

# Keep intermediate files for debugging
uv run python scripts/metapaths/extend_metapaths_chunked.py \
    --nhop 1hop_metapaths.tsv \
    --onehop 1hop_metapaths.tsv \
    --output 2hop_metapaths.tsv \
    --keep-intermediates
```

### 4. `extend_metapaths_streaming.py` (Alternative - simpler but needs more disk)
Streaming version that uses disk-based operations.

**Memory usage:** O(1-hop index) - typically **~500MB-2GB regardless of N**

**Disk space:** O(total_joins) - **can be huge** (960GB for 1→2 hop on ROBOKOP!)

**Problem:** Writes ALL joins to a single temp file before aggregating, which can fill disk on large graphs.

**When to use:**
- Small to medium graphs where total joins < 100M
- When you have plenty of disk space (500GB+)
- For debugging/comparing results

**Not recommended for ROBOKOP 1-hop → 2-hop** (generates 6.4B joins = 960GB temp file)

## Complete Workflow (RECOMMENDED)

### Generating 3-hop metapaths using chunked processing

```bash
# Step 1: Extract 1-hop metapaths (~10M entries, ~500MB RAM)
uv run python scripts/metapaths/extract_1hop_metapaths.py \
    --edges ../SimplePredictions/input_graphs/robokop_base_nonredundant/edges.jsonl \
    --nodes ../SimplePredictions/input_graphs/robokop_base_nonredundant/nodes.jsonl \
    --output 1hop_metapaths.tsv

# Step 2: Generate 2-hop metapaths (~1B entries, ~500MB RAM, ~30GB disk per chunk)
uv run python scripts/metapaths/extend_metapaths_chunked.py \
    --nhop 1hop_metapaths.tsv \
    --onehop 1hop_metapaths.tsv \
    --output 2hop_metapaths.tsv \
    --chunk-size 500000

# Step 3: Generate 3-hop metapaths (~10B+ entries, still ~500MB RAM!)
uv run python scripts/metapaths/extend_metapaths_chunked.py \
    --nhop 2hop_metapaths.tsv \
    --onehop 1hop_metapaths.tsv \
    --output 3hop_metapaths.tsv \
    --chunk-size 500000
```

## Performance Comparison

### 1-hop → 2-hop (ROBOKOP scale: 16.7M input → 6.4B joins)

| Script | Memory | Disk Space | Time | Status |
|--------|--------|------------|------|--------|
| `extend_metapaths.py` | **50-200GB** 💀 | 0 GB | 30 min | OOM crash |
| `extend_metapaths_streaming.py` | **500 MB** ✅ | **960 GB** 💀 | 60 min | Disk full crash |
| `extend_metapaths_chunked.py` | **500 MB** ✅ | **~100 GB** ✅ | 90 min | **Works!** |

### 2-hop → 3-hop (estimated)

| Script | Memory | Disk Space | Time | Status |
|--------|--------|------------|------|--------|
| `extend_metapaths.py` | **200GB+** 💀 | 0 GB | N/A | OOM crash |
| `extend_metapaths_streaming.py` | **500 MB** ✅ | **5+ TB** 💀 | N/A | Disk full crash |
| `extend_metapaths_chunked.py` | **500 MB** ✅ | **~500 GB** ✅ | 8-12 hrs | **Works!** |

## Disk Space Requirements

### Chunked processing (recommended)

Per-chunk temp files (automatically deleted after aggregation):
- **1-hop → 2-hop:** ~30GB per chunk, ~34 chunks = ~100GB total intermediate files
- **2-hop → 3-hop:** ~50GB per chunk = ~500GB total intermediate files
- **3-hop → 4-hop:** ~100GB per chunk = ~1TB+ total intermediate files

Set temp directory with large disk space:
```bash
export TMPDIR=/path/to/large/disk
uv run python scripts/metapaths/extend_metapaths_chunked.py ...
```

### Streaming processing (not recommended for large graphs)

Single monolithic temp file (960GB for ROBOKOP 1→2 hop):
- **1-hop → 2-hop:** ~960GB temp file (6.4B joins)
- **2-hop → 3-hop:** ~5TB+ temp file
- **3-hop → 4-hop:** ~50TB+ temp file (impractical)

## DuckDB Setup (Recommended)

For faster aggregation, install DuckDB:

```bash
uv add duckdb
```

DuckDB is 2-3x faster than sort/uniq and uses cleaner SQL-based aggregation.

## Algorithm Details

### Original Algorithm (extend_metapaths.py)
```
1. Load 1-hop index: node_A -> [(node_B, metapath), ...]
2. Load ALL N-hop paths into list ← MEMORY PROBLEM
3. For each N-hop path:
     For each matching 1-hop continuation:
       Accumulate in Counter ← MEMORY PROBLEM
4. Write Counter to file
```

**Problems:** Both input and output in memory = 200GB+ for large graphs

### Streaming Algorithm (extend_metapaths_streaming.py)
```
1. Load 1-hop index: node_A -> [(node_B, metapath), ...]
2. Stream N-hop file line by line ← NO LOADING
3. For each N-hop path:
     For each matching 1-hop continuation:
       Write immediately to temp file ← NO ACCUMULATION
4. Sort temp file on disk (uses external merge sort)
5. Count duplicates and write final output
```

**Problems:** Single 960GB temp file fills disk

### Chunked Algorithm (extend_metapaths_chunked.py) - RECOMMENDED
```
1. Load 1-hop index: node_A -> [(node_B, metapath), ...]
2. For each chunk of N-hop file (e.g., 500K rows):
     a. Generate joins to temp file (~30GB)
     b. Aggregate temp file with DuckDB (reduces to ~5GB)
     c. Save aggregated chunk, delete temp
3. Merge all aggregated chunks with DuckDB
```

**Key insights:**
- Never materialize the full input or output in memory
- Never materialize the full unaggregated joins on disk
- Process in bounded chunks, aggregate incrementally

## Troubleshooting

### "Out of memory" error
- Use `extend_metapaths_chunked.py` instead of `extend_metapaths.py`
- Reduce `--chunk-size` (e.g., from 500K to 250K)

### "No space left on device"
- **Chunked version:** Needs ~30-50GB per chunk (default 500K rows)
  - Reduce `--chunk-size` to use less disk space (slower, but works)
  - Set `TMPDIR` to location with more space:
    ```bash
    export TMPDIR=/path/to/large/disk
    uv run python scripts/metapaths/extend_metapaths_chunked.py ...
    ```

- **Streaming version:** Needs 960GB+ for ROBOKOP 1→2 hop
  - Switch to chunked version instead

### DuckDB import error
```bash
uv add duckdb
```

### Process seems stuck / no progress updates
- Each chunk takes time to process (10-30 min per 500K rows for 1→2 hop)
- Progress is printed per chunk and every 100K input rows
- Monitor disk usage to verify temp files are being created/deleted

### Want to resume after crash
- Currently no resume capability - must restart from beginning
- Use `--keep-intermediates` to save chunks before crash, then manually merge
- Future enhancement: add checkpoint/resume functionality
