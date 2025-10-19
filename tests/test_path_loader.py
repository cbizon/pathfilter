"""Tests for path loader."""
import pytest
from pathfilter.path_loader import (
    load_paths_from_file,
    load_paths_for_query,
    Path
)
from pathfilter.query_loader import Query


# Use actual test data
TEST_PATH_FILE = "input_data/paths/CHEBI_15647_to_UNII_31YO63LBSN.xlsx"
PATHS_DIR = "input_data/paths"


class TestLoadPathsFromFile:
    """Tests for loading paths from an xlsx file."""

    def test_load_paths_basic(self):
        """Test loading paths from a file."""
        paths = load_paths_from_file(TEST_PATH_FILE)

        assert len(paths) > 0
        assert all(isinstance(p, Path) for p in paths)

    def test_path_structure(self):
        """Test that loaded paths have correct structure."""
        paths = load_paths_from_file(TEST_PATH_FILE)
        path = paths[0]

        # Check all fields are populated
        assert path.path_labels
        assert isinstance(path.path_curies, list)
        assert len(path.path_curies) > 0
        assert isinstance(path.num_paths, int)
        assert path.num_paths > 0
        assert path.categories
        assert path.first_hop_predicates
        assert path.second_hop_predicates
        assert path.third_hop_predicates
        assert isinstance(path.has_gene, bool)
        assert path.metapaths

    def test_path_curies_parsed(self):
        """Test that path_curies are properly parsed into list."""
        paths = load_paths_from_file(TEST_PATH_FILE)
        path = paths[0]

        # Should have 4 nodes (start -> hop1 -> hop2 -> end)
        assert len(path.path_curies) == 4

        # All should be valid CURIEs (contain colon)
        for curie in path.path_curies:
            assert ':' in curie

        # First and last should match filename
        assert path.path_curies[0] == "CHEBI:15647"
        assert path.path_curies[-1] == "UNII:31YO63LBSN"

    def test_labels_vs_curies(self):
        """Test that path labels and curies align."""
        paths = load_paths_from_file(TEST_PATH_FILE)
        path = paths[0]

        # Count arrows in labels
        label_nodes = path.path_labels.split(' -> ')
        # Should match number of CURIEs
        assert len(label_nodes) == len(path.path_curies)

    def test_load_multiple_paths(self):
        """Test loading file with many paths."""
        paths = load_paths_from_file(TEST_PATH_FILE)

        # This file should have thousands of paths
        assert len(paths) > 1000

        # All should be valid Path objects
        for path in paths[:100]:  # Check first 100
            assert isinstance(path, Path)
            assert len(path.path_curies) > 0

    def test_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            load_paths_from_file("nonexistent_file.xlsx")

    def test_has_gene_field(self):
        """Test that has_gene field is properly loaded."""
        paths = load_paths_from_file(TEST_PATH_FILE)

        # Should have some paths with genes and some without
        has_gene_values = [p.has_gene for p in paths[:100]]
        assert True in has_gene_values  # At least one with gene


class TestLoadPathsForQuery:
    """Tests for loading paths for a specific query."""

    def test_load_paths_for_query(self):
        """Test loading paths using a query object."""
        # Create a query that matches our test file
        query = Query(
            name="TEST",
            start_label="Leukotriene B4",
            start_curies=["CHEBI:15647"],
            end_label="Nivolumab",
            end_curies=["UNII:31YO63LBSN"]
        )

        paths = load_paths_for_query(query, PATHS_DIR)

        assert paths is not None
        assert len(paths) > 0
        assert all(isinstance(p, Path) for p in paths)

    def test_query_without_matching_file(self):
        """Test behavior when no path file exists for query."""
        query = Query(
            name="TEST",
            start_label="fake",
            start_curies=["FAKE:123"],
            end_label="fake",
            end_curies=["FAKE:456"]
        )

        paths = load_paths_for_query(query, PATHS_DIR)
        assert paths is None

    @pytest.mark.slow
    def test_load_paths_from_real_query(self):
        """Test loading paths from a real query definition."""
        from pathfilter.query_loader import load_all_queries

        queries = load_all_queries("input_data/Pathfinder Test Queries.xlsx.ods")

        # Try to load paths for queries
        loaded_count = 0
        for query in queries[:5]:  # Test first 5
            paths = load_paths_for_query(query, PATHS_DIR)
            if paths:
                loaded_count += 1
                assert len(paths) > 0
                # Verify first/last CURIEs match query
                first_curie = paths[0].path_curies[0]
                last_curie = paths[0].path_curies[-1]
                # First/last should be one of query's start/end CURIEs
                assert (first_curie in query.start_curies or
                        first_curie in query.end_curies)
                assert (last_curie in query.start_curies or
                        last_curie in query.end_curies)

        # Should find at least some matching path files
        assert loaded_count > 0
