# Data Format Analysis

## Summary of Input Data Structure

### Query Definitions
**File**: `input_data/Pathfinder Test Queries.xlsx.ods`

**Structure**:
- Main sheet: `20 TestQueries` - contains overview of all queries
- Individual query sheets: Named as `PFTQ-1-c`, `PFTQ-2-i`, `PFTQ-4`, etc.

**Query Sheet Format** (e.g., PFTQ-1-c):
- Row 0: Start node - Column 1: label, Column 2: CURIE(s)
- Row 1: End node - Column 1: label, Column 2: CURIE(s)
- Rows 2+: Expected Node - Column 1: label, Column 2: CURIE(s)
  - Only rows with CURIEs in column 2 should be considered
  - CURIEs may be concatenated without delimiters (e.g., "CHEBI:18295PR:000049994")
- Additional constraint rows (Expected Predicates, Category Constraints, etc.)

**Key Observations**:
- Some queries have multiple CURIEs for start/end nodes (concatenated)
- Expected nodes list multiple equivalent CURIEs for the same concept
- Need to parse concatenated CURIEs (pattern: PREFIX:ID repeated)

### Path Data Files

#### Prototype File: `paths.tsv`
**Format**: Tab-separated values, NO header row
**Columns** (8 total):
1. path (string with labels, e.g., "asthma -> Artenimol -> ATG12 -> Imatinib")
2. num_paths (integer)
3. categories (string, e.g., "biolink:Disease --> biolink:SmallMolecule --> biolink:Gene --> biolink:SmallMolecule")
4. first_hop_predicates (set string, e.g., "{'biolink:treats_or_applied_or_studied_to_treat'}")
5. second_hop_predicates (set string)
6. third_hop_predicates (set string)
7. has_gene (boolean, "TRUE"/"FALSE")
8. metapaths (list string)

**Missing**: No path_curies column - cannot match CURIEs to expected nodes!

#### Query-specific Files: `input_data/paths/*.xlsx`
**Format**: Excel 2007+ (.xlsx)
**File naming**: `{START_CURIE}_to_{END_CURIE}.xlsx` (with underscores replacing colons)
  - Example: `CHEBI_15647_to_UNII_31YO63LBSN.xlsx`

**Columns** (9 total):
1. path (string with labels)
2. num_paths (integer)
3. categories (string)
4. first_hop_predicates (set string)
5. second_hop_predicates (set string)
6. third_hop_predicates (set string)
7. has_gene (boolean)
8. metapaths (list string)
9. **path_curies** (string, e.g., "CHEBI:15647 --> NCBIGene:100133941 --> NCBIGene:4907 --> UNII:31YO63LBSN")

**Key Differences from paths.tsv**:
1. ✅ Has header row
2. ✅ Has path_curies column (CRITICAL for matching expected nodes)
3. ✅ Query-specific (one file per query)

### Expected Workflow

1. **Load query definitions** from `Pathfinder Test Queries.xlsx.ods`
   - Parse each query sheet to extract:
     - Start/End node CURIEs
     - Expected node CURIEs (from column C, non-empty only)
   - Normalize expected CURIEs using node normalizer API

2. **Map queries to path files**
   - Match query start/end CURIEs to path file names
   - Handle multiple CURIEs for same query (need strategy)

3. **Load paths** from query-specific xlsx files
   - Parse path_curies column to extract node CURIEs
   - This is essential for matching against expected nodes

4. **Apply filters** to paths
   - Use existing filter functions from filter.py
   - Track before/after statistics

5. **Evaluate results**
   - Check if path contains any expected nodes (via path_curies)
   - Calculate metrics: recall, precision, enrichment

### Critical Findings

**BLOCKER**: paths.tsv lacks path_curies column
- Cannot be used for matching expected nodes
- Must use query-specific xlsx files instead
- Prototype probably used string matching on labels (e.g., " KIT ", " Histamine ")

**CURIE Parsing Challenge**:
- Query definitions have concatenated CURIEs without clear delimiters
- Need robust parsing: look for CURIE pattern (PREFIX:ID) and split appropriately
- Common prefixes: CHEBI, MONDO, NCBIGene, UNII, NCIT, CHV, PR, UMLS, CL, ENSEMBL, etc.

**Query-to-File Mapping**:
- Files use underscored CURIEs in naming
- Queries may have multiple start/end CURIEs - need to find corresponding file(s)
- Not all query sheets may have corresponding path files

## Recommended Data Structure

```python
@dataclass
class Query:
    name: str  # e.g., "PFTQ-1-c"
    start_curies: List[str]
    end_curies: List[str]
    expected_nodes: Dict[str, List[str]]  # label -> list of CURIEs
    expected_nodes_normalized: Set[str]  # all equivalent CURIEs after normalization
    path_file: str  # path to xlsx file

@dataclass
class Path:
    path_labels: str  # "asthma -> Artenimol -> ATG12 -> Imatinib"
    path_curies: List[str]  # ["MONDO:0004979", "CHEBI:...", "NCBIGene:...", "CHEBI:31690"]
    num_paths: int
    categories: str
    predicates: List[str]  # [first_hop, second_hop, third_hop]
    has_gene: bool
    metapaths: str
```
