"""Tests for query loader."""
import pytest
from pathfilter.query_loader import (
    load_query_from_sheet,
    get_all_query_sheets,
    load_all_queries,
    find_path_file_for_query,
    Query
)


# Use actual test data files
TEST_QUERIES_FILE = "input_data/Pathfinder Test Queries.xlsx.ods"
PATHS_DIR = "input_data/paths"


class TestLoadQueryFromSheet:
    """Tests for loading a single query from a sheet."""

    def test_load_pftq1_query(self):
        """Test loading PFTQ-1-c query."""
        query = load_query_from_sheet(TEST_QUERIES_FILE, "PFTQ-1-c")

        assert query.name == "PFTQ-1-c"
        assert query.start_label == "imatinib"
        assert query.start_curies == ["CHEBI:31690"]
        assert query.end_label == "asthma"
        assert "MONDO:0004979" in query.end_curies
        assert "MONDO:0004784" in query.end_curies

        # Check expected nodes
        assert "CKIT" in query.expected_nodes
        assert "Histamine" in query.expected_nodes
        assert "SCF-1" in query.expected_nodes
        assert "MAST cell" in query.expected_nodes

        # Check some CURIEs
        assert "NCBIGene:3815" in query.expected_nodes["CKIT"]
        assert "CHEBI:18295" in query.expected_nodes["Histamine"]

    def test_load_pftq4_query(self):
        """Test loading PFTQ-4 query."""
        query = load_query_from_sheet(TEST_QUERIES_FILE, "PFTQ-4")

        assert query.name == "PFTQ-4"
        assert query.start_label == "SLC6A20"
        assert "NCBIGene:54716" in query.start_curies
        assert "NCBIGene:27240" in query.start_curies
        assert query.end_label == "COVID-19"
        assert query.end_curies == ["MONDO:0100096"]

        # Check expected nodes
        assert "ACE2" in query.expected_nodes
        assert "NRF2" in query.expected_nodes

    def test_query_without_expected_nodes(self):
        """Test that query loads even if some expected nodes lack CURIEs."""
        # PFTQ-20 has some expected nodes with NaN in column C
        query = load_query_from_sheet(TEST_QUERIES_FILE, "PFTQ-20")

        assert query.name == "PFTQ-20"
        # Should only include expected nodes that have CURIEs
        for label, curies in query.expected_nodes.items():
            assert len(curies) > 0, f"Expected node '{label}' should have CURIEs"


class TestGetAllQuerySheets:
    """Tests for getting all query sheet names."""

    def test_get_query_sheets(self):
        """Test getting all query sheets."""
        sheets = get_all_query_sheets(TEST_QUERIES_FILE)

        assert len(sheets) > 0
        assert "PFTQ-1-c" in sheets
        assert "PFTQ-4" in sheets
        # Should not include non-query sheets
        assert "20 TestQueries" not in sheets
        assert "Notes" not in sheets


class TestLoadAllQueries:
    """Tests for loading all queries."""

    def test_load_all_queries(self):
        """Test loading all queries from the file."""
        queries = load_all_queries(TEST_QUERIES_FILE)

        assert len(queries) > 0

        # All loaded queries should have expected nodes
        for query in queries:
            assert len(query.expected_nodes) > 0

        # Check that specific queries are present
        query_names = [q.name for q in queries]
        assert "PFTQ-1-c" in query_names
        assert "PFTQ-4" in query_names

    def test_queries_have_required_fields(self):
        """Test that all loaded queries have required fields."""
        queries = load_all_queries(TEST_QUERIES_FILE)

        for query in queries:
            assert query.name
            assert query.start_label
            assert len(query.start_curies) > 0
            assert query.end_label
            assert len(query.end_curies) > 0
            assert len(query.expected_nodes) > 0


class TestFindPathFileForQuery:
    """Tests for finding path files."""

    def test_find_path_file_pftq1(self):
        """Test finding path file for PFTQ-1."""
        query = Query(
            name="PFTQ-1-c",
            start_label="imatinib",
            start_curies=["CHEBI:31690"],
            end_label="asthma",
            end_curies=["MONDO:0004979"]
        )

        # This file may or may not exist - just test the function works
        path_file = find_path_file_for_query(query, PATHS_DIR)

        if path_file:
            assert path_file.endswith(".xlsx")
            assert "CHEBI_31690" in path_file or "MONDO_0004979" in path_file

    def test_find_existing_path_file(self):
        """Test finding a path file that we know exists."""
        # Load a real query and find its path file
        queries = load_all_queries(TEST_QUERIES_FILE)

        found_count = 0
        for query in queries:
            path_file = find_path_file_for_query(query, PATHS_DIR)
            if path_file:
                found_count += 1
                assert path_file.endswith(".xlsx")
                # Verify file actually exists
                import os
                assert os.path.exists(path_file)

        # Should find at least some path files
        assert found_count > 0, "Should find at least one matching path file"

    def test_find_path_file_not_found(self):
        """Test behavior when path file doesn't exist."""
        query = Query(
            name="TEST",
            start_label="fake",
            start_curies=["FAKE:123"],
            end_label="fake",
            end_curies=["FAKE:456"]
        )

        path_file = find_path_file_for_query(query, PATHS_DIR)
        assert path_file is None
