"""Tests for query loader (JSON loading)."""
import pytest
from pathfilter.query_loader import (
    load_all_queries,
    find_path_file_for_query,
    Query
)


# Use normalized data files
NORMALIZED_QUERIES_FILE = "normalized_input_data/queries_normalized.json"
NORMALIZED_PATHS_DIR = "normalized_input_data/paths"
PATHS_DIR = "input_data/paths"  # Fallback for path finding tests


class TestLoadAllQueries:
    """Tests for loading queries from normalized JSON."""

    @pytest.mark.slow
    def test_load_all_queries_from_json(self):
        """Test loading all queries from normalized JSON file."""
        queries = load_all_queries(NORMALIZED_QUERIES_FILE)

        assert len(queries) > 0

        # All loaded queries should have expected nodes
        for query in queries:
            assert len(query.expected_nodes) > 0

        # Check that specific queries are present
        query_names = [q.name for q in queries]
        assert "PFTQ-1-c" in query_names
        assert "PFTQ-4" in query_names

    @pytest.mark.slow
    def test_queries_have_required_fields(self):
        """Test that all loaded queries have required fields."""
        queries = load_all_queries(NORMALIZED_QUERIES_FILE)

        for query in queries:
            assert query.name
            assert query.start_label
            assert len(query.start_curies) > 0
            assert query.end_label
            assert len(query.end_curies) > 0
            assert len(query.expected_nodes) > 0

    @pytest.mark.slow
    def test_queries_have_normalized_curies(self):
        """Test that loaded queries contain normalized CURIEs."""
        queries = load_all_queries(NORMALIZED_QUERIES_FILE)

        # Find PFTQ-1-c and check it has normalized CURIEs
        pftq1 = next((q for q in queries if q.name == "PFTQ-1-c"), None)
        assert pftq1 is not None

        # These should be normalized (preferred identifiers)
        assert pftq1.start_curies == ["CHEBI:31690"]
        assert "MONDO:0004979" in pftq1.end_curies or "MONDO:0004784" in pftq1.end_curies

        # Check expected nodes have CURIEs (normalized)
        assert "CKIT" in pftq1.expected_nodes or "KIT" in pftq1.expected_nodes
        assert len(pftq1.expected_nodes) > 0

    @pytest.mark.slow
    def test_auto_detect_json_from_ods_path(self):
        """Test that loader auto-detects JSON when given ODS path."""
        # This should auto-detect and load queries_normalized.json
        queries = load_all_queries("normalized_input_data/Pathfinder Test Queries.xlsx.ods")

        assert len(queries) > 0
        query_names = [q.name for q in queries]
        assert "PFTQ-1-c" in query_names


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

    @pytest.mark.slow
    def test_find_existing_path_file(self):
        """Test finding a path file that we know exists."""
        # Load queries from normalized JSON
        queries = load_all_queries(NORMALIZED_QUERIES_FILE)

        found_count = 0
        for query in queries:
            # Try normalized paths first, fallback to original
            path_file = find_path_file_for_query(query, NORMALIZED_PATHS_DIR)
            if not path_file:
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
