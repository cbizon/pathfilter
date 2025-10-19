"""Tests for node normalization."""
import pytest
from pathfilter.normalization import (
    normalize_curies,
    normalize_curie,
    get_normalized_expected_nodes,
    normalize_path_curies
)
from pathfilter.query_loader import Query


class TestNormalizeCuries:
    """Tests for normalizing multiple CURIEs."""

    def test_normalize_water_curies(self):
        """Test normalizing different CURIEs for water."""
        curies = ["MESH:D014867", "CHEBI:15377"]
        result = normalize_curies(curies)

        # Both should normalize to the same preferred ID
        assert result["MESH:D014867"] is not None
        assert result["CHEBI:15377"] is not None
        # Should both map to same preferred identifier
        assert result["MESH:D014867"] == result["CHEBI:15377"]

    def test_normalize_single_curie(self):
        """Test normalizing a single CURIE."""
        result = normalize_curies(["MONDO:0004976"])

        assert "MONDO:0004976" in result
        assert result["MONDO:0004976"] is not None
        # MONDO is often the preferred identifier for diseases
        assert "MONDO:" in result["MONDO:0004976"]

    def test_normalize_empty_list(self):
        """Test normalizing empty list."""
        result = normalize_curies([])
        assert result == {}

    def test_normalize_invalid_curie(self):
        """Test normalizing an invalid/unknown CURIE."""
        result = normalize_curies(["INVALID:12345"])

        # Should return None for unknown CURIEs
        assert result["INVALID:12345"] is None

    def test_normalize_mixed_valid_invalid(self):
        """Test normalizing mix of valid and invalid CURIEs."""
        curies = ["MONDO:0004976", "INVALID:99999"]
        result = normalize_curies(curies)

        # Valid should normalize
        assert result["MONDO:0004976"] is not None
        # Invalid should be None
        assert result["INVALID:99999"] is None


class TestNormalizeCurie:
    """Tests for normalizing single CURIE (cached)."""

    def test_normalize_single(self):
        """Test single CURIE normalization."""
        result = normalize_curie("CHEBI:15377")
        assert result is not None
        assert ":" in result

    def test_caching(self):
        """Test that results are cached."""
        # First call
        result1 = normalize_curie("MONDO:0004976")
        # Second call should be cached
        result2 = normalize_curie("MONDO:0004976")

        assert result1 == result2
        assert result1 is not None


class TestGetNormalizedExpectedNodes:
    """Tests for normalizing query expected nodes."""

    def test_normalize_query_expected_nodes(self):
        """Test normalizing all expected nodes for a query."""
        query = Query(
            name="TEST",
            start_label="test",
            start_curies=["CHEBI:31690"],
            end_label="test",
            end_curies=["MONDO:0004979"],
            expected_nodes={
                "KIT": ["NCBIGene:3815", "NCIT:C39712"],
                "Histamine": ["CHEBI:18295"]
            }
        )

        normalized = get_normalized_expected_nodes(query)

        # Should get normalized IDs for all expected nodes
        assert len(normalized) > 0
        # All should be valid CURIEs
        for curie in normalized:
            assert curie is not None
            assert ":" in curie

    def test_empty_expected_nodes(self):
        """Test query with no expected nodes."""
        query = Query(
            name="TEST",
            start_label="test",
            start_curies=["CHEBI:31690"],
            end_label="test",
            end_curies=["MONDO:0004979"],
            expected_nodes={}
        )

        normalized = get_normalized_expected_nodes(query)
        assert len(normalized) == 0


class TestNormalizePathCuries:
    """Tests for normalizing path CURIEs."""

    def test_normalize_path(self):
        """Test normalizing a path's CURIEs."""
        path_curies = [
            "MONDO:0004979",
            "CHEBI:15377",
            "NCBIGene:3815",
            "CHEBI:31690"
        ]

        normalized = normalize_path_curies(path_curies)

        # Should return same number of items
        assert len(normalized) == len(path_curies)

        # All should be normalized (or None)
        for norm_curie in normalized:
            if norm_curie is not None:
                assert ":" in norm_curie

    def test_normalize_path_maintains_order(self):
        """Test that path order is maintained."""
        path_curies = ["CHEBI:15377", "NCBIGene:3815", "MONDO:0004979"]

        normalized = normalize_path_curies(path_curies)

        assert len(normalized) == 3
        # Order should be preserved
        # Can't check exact values, but can check they're different
        assert normalized[0] != normalized[1]  # Different concepts
        assert normalized[1] != normalized[2]

    def test_normalize_empty_path(self):
        """Test normalizing empty path."""
        result = normalize_path_curies([])
        assert result == []


class TestRealWorldData:
    """Tests using real query data."""

    @pytest.mark.slow
    def test_normalize_real_query_data(self):
        """Test normalization with actual query data."""
        from pathfilter.query_loader import load_all_queries

        queries = load_all_queries("input_data/Pathfinder Test Queries.xlsx.ods")

        # Test first query with expected nodes
        if queries:
            query = queries[0]
            normalized = get_normalized_expected_nodes(query)

            assert len(normalized) > 0
            # All should be valid preferred IDs
            for curie in normalized:
                assert curie is not None
                assert ":" in curie
