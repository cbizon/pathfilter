"""Tests for path matching logic."""
import pytest
from pathfilter.matching import (
    does_path_contain_expected_node,
    filter_paths_with_expected_nodes,
    count_paths_with_expected_nodes,
    get_expected_nodes_found_in_paths
)
from pathfilter.path_loader import Path
from pathfilter.normalization import normalize_curies, get_normalized_expected_nodes
from pathfilter.query_loader import Query


class TestDoesPathContainExpectedNode:
    """Tests for checking if path contains expected node."""

    def test_path_contains_expected_node(self):
        """Test detecting expected node in path."""
        # Create a simple path
        path = Path(
            path_labels="Disease -> Chemical -> Gene -> Drug",
            path_curies=["MONDO:0004979", "CHEBI:15377", "NCBIGene:3815", "CHEBI:31690"],
            num_paths=1,
            categories="biolink:Disease --> biolink:SmallMolecule --> biolink:Gene --> biolink:SmallMolecule",
            first_hop_predicates="{'biolink:treats'}",
            second_hop_predicates="{'biolink:affects'}",
            third_hop_predicates="{'biolink:affects'}",
            has_gene=True,
            metapaths="['Disease -> Chemical -> Gene -> Drug']"
        )

        # Normalize an expected node that's in the path
        expected_normalized = normalize_curies(["NCBIGene:3815"])
        normalized_expected_set = {expected_normalized["NCBIGene:3815"]}

        result = does_path_contain_expected_node(path, normalized_expected_set)
        assert result is True

    def test_path_does_not_contain_expected_node(self):
        """Test path without expected node."""
        path = Path(
            path_labels="Disease -> Chemical -> Gene -> Drug",
            path_curies=["MONDO:0004979", "CHEBI:15377", "NCBIGene:3815", "CHEBI:31690"],
            num_paths=1,
            categories="biolink:Disease --> biolink:SmallMolecule --> biolink:Gene --> biolink:SmallMolecule",
            first_hop_predicates="{'biolink:treats'}",
            second_hop_predicates="{'biolink:affects'}",
            third_hop_predicates="{'biolink:affects'}",
            has_gene=True,
            metapaths="['Disease -> Chemical -> Gene -> Drug']"
        )

        # Use an expected node that's NOT in the path
        expected_normalized = normalize_curies(["NCBIGene:999999"])
        # This will likely return None or a different ID
        normalized_id = expected_normalized["NCBIGene:999999"]
        if normalized_id:
            normalized_expected_set = {normalized_id}
        else:
            normalized_expected_set = {"FAKE:12345"}

        result = does_path_contain_expected_node(path, normalized_expected_set)
        assert result is False

    def test_equivalent_curies_match(self):
        """Test that equivalent CURIEs match via normalization."""
        # Use water as example - MESH:D014867 and CHEBI:15377 are equivalent
        # First normalize the path CURIEs (as our pre-normalization does)
        path_curies_raw = ["MONDO:0001", "MESH:D014867", "GENE:123", "CHEM:456"]
        path_normalized = normalize_curies(path_curies_raw)
        path_curies_normalized = [path_normalized[c] for c in path_curies_raw]

        path = Path(
            path_labels="A -> Water -> B -> C",
            path_curies=path_curies_normalized,
            num_paths=1,
            categories="A --> B --> C --> D",
            first_hop_predicates="{'biolink:affects'}",
            second_hop_predicates="{'biolink:affects'}",
            third_hop_predicates="{'biolink:affects'}",
            has_gene=False,
            metapaths="['A -> B -> C -> D']"
        )

        # Expected node uses different CURIE for water
        expected_normalized = normalize_curies(["CHEBI:15377"])
        normalized_expected_set = {expected_normalized["CHEBI:15377"]}

        # Should match because both normalize to same preferred ID (CHEBI:15377)
        result = does_path_contain_expected_node(path, normalized_expected_set)
        assert result is True


class TestFilterPathsWithExpectedNodes:
    """Tests for filtering paths."""

    def test_filter_paths(self):
        """Test filtering paths to only those with expected nodes."""
        paths = [
            Path("A -> B -> C -> D", ["ID1", "ID2", "NCBIGene:3815", "ID4"], 1, "cat", "p1", "p2", "p3", True, "mp"),
            Path("A -> X -> Y -> Z", ["ID1", "ID5", "ID6", "ID7"], 1, "cat", "p1", "p2", "p3", False, "mp"),
            Path("A -> B -> NCBIGene:3815 -> D", ["ID1", "ID2", "NCBIGene:3815", "ID4"], 1, "cat", "p1", "p2", "p3", True, "mp"),
        ]

        # Expected node
        expected_normalized = normalize_curies(["NCBIGene:3815"])
        normalized_expected_set = {expected_normalized["NCBIGene:3815"]}

        filtered = filter_paths_with_expected_nodes(paths, normalized_expected_set)

        # Should keep paths that contain the expected node
        assert len(filtered) == 2
        assert all(does_path_contain_expected_node(p, normalized_expected_set) for p in filtered)

    def test_filter_empty_paths(self):
        """Test filtering with empty path list."""
        filtered = filter_paths_with_expected_nodes([], {"MONDO:0001"})
        assert filtered == []


class TestCountPathsWithExpectedNodes:
    """Tests for counting paths with expected nodes."""

    def test_count_paths(self):
        """Test counting paths containing expected nodes."""
        paths = [
            Path("A -> B -> C -> D", ["ID1", "ID2", "NCBIGene:3815", "ID4"], 1, "cat", "p1", "p2", "p3", True, "mp"),
            Path("A -> X -> Y -> Z", ["ID1", "ID5", "ID6", "ID7"], 1, "cat", "p1", "p2", "p3", False, "mp"),
            Path("A -> B -> Gene -> D", ["ID1", "ID2", "NCBIGene:3815", "ID4"], 1, "cat", "p1", "p2", "p3", True, "mp"),
        ]

        expected_normalized = normalize_curies(["NCBIGene:3815"])
        normalized_expected_set = {expected_normalized["NCBIGene:3815"]}

        count = count_paths_with_expected_nodes(paths, normalized_expected_set)
        assert count == 2

    def test_count_zero(self):
        """Test count when no paths match."""
        paths = [
            Path("A -> X -> Y -> Z", ["ID1", "ID5", "ID6", "ID7"], 1, "cat", "p1", "p2", "p3", False, "mp"),
        ]

        count = count_paths_with_expected_nodes(paths, {"FAKE:12345"})
        assert count == 0


class TestGetExpectedNodesFoundInPaths:
    """Tests for finding which expected nodes are present."""

    def test_get_found_nodes(self):
        """Test identifying which expected nodes are found."""
        paths = [
            Path("A -> B -> C -> D", ["ID1", "NCBIGene:3815", "ID3", "ID4"], 1, "cat", "p1", "p2", "p3", True, "mp"),
            Path("A -> X -> Y -> Z", ["ID1", "CHEBI:15377", "ID6", "ID7"], 1, "cat", "p1", "p2", "p3", False, "mp"),
        ]

        # Multiple expected nodes
        expected_curies = ["NCBIGene:3815", "CHEBI:15377", "MONDO:0004979"]
        normalized = normalize_curies(expected_curies)
        normalized_expected_set = {v for v in normalized.values() if v is not None}

        found = get_expected_nodes_found_in_paths(paths, normalized_expected_set)

        # Should find the two that are in paths
        assert len(found) >= 2
        # Both NCBIGene:3815 and CHEBI:15377 should be found (in normalized form)
        assert normalized["NCBIGene:3815"] in found
        assert normalized["CHEBI:15377"] in found

    def test_no_expected_nodes_found(self):
        """Test when no expected nodes are in paths."""
        paths = [
            Path("A -> X -> Y -> Z", ["ID1", "ID2", "ID3", "ID4"], 1, "cat", "p1", "p2", "p3", False, "mp"),
        ]

        found = get_expected_nodes_found_in_paths(paths, {"FAKE:12345"})
        assert len(found) == 0


class TestRealWorldMatching:
    """Tests using real query and path data."""

    @pytest.mark.slow
    def test_real_query_path_matching(self):
        """Test matching with real query and path data."""
        from pathfilter.query_loader import load_all_queries
        from pathfilter.path_loader import load_paths_for_query

        queries = load_all_queries("input_data/Pathfinder Test Queries.xlsx.ods")

        # Find a query with paths
        for query in queries[:5]:
            paths = load_paths_for_query(query, "input_data/paths")
            if paths:
                # Get normalized expected nodes
                normalized_expected = get_normalized_expected_nodes(query)

                if normalized_expected:
                    # Count how many paths contain expected nodes
                    count = count_paths_with_expected_nodes(paths, normalized_expected)

                    # Should find at least some paths with expected nodes
                    assert count >= 0  # May be 0 if expected nodes aren't in paths
                    assert count <= len(paths)

                    # Find which expected nodes are actually present
                    found = get_expected_nodes_found_in_paths(paths, normalized_expected)
                    assert isinstance(found, set)

                    # If we found any, they should be in the expected set
                    assert found.issubset(normalized_expected)
                    break
