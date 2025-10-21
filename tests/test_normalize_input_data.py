"""Tests for normalize_input_data script (ODF parsing)."""
import pytest
import sys
from pathlib import Path

# Add scripts directory to path so we can import from normalize_input_data
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from normalize_input_data import load_query_from_ods


# Use actual test data files
TEST_QUERIES_FILE = "input_data/Pathfinder Test Queries.xlsx.ods"


class TestLoadQueryFromOds:
    """Tests for loading and parsing queries from ODS file."""

    @pytest.mark.slow
    def test_load_pftq1_query(self):
        """Test loading PFTQ-1-c query."""
        query_data = load_query_from_ods(TEST_QUERIES_FILE, "PFTQ-1-c")

        assert query_data["name"] == "PFTQ-1-c"
        assert query_data["start_label"] == "imatinib"
        assert query_data["start_curies"] == ["CHEBI:31690"]
        assert query_data["end_label"] == "asthma"
        assert "MONDO:0004979" in query_data["end_curies"]
        assert "MONDO:0004784" in query_data["end_curies"]

        # Check expected nodes
        assert "CKIT" in query_data["expected_nodes"]
        assert "Histamine" in query_data["expected_nodes"]
        assert "SCF-1" in query_data["expected_nodes"]
        assert "MAST cell" in query_data["expected_nodes"]

        # Check some CURIEs
        assert "NCBIGene:3815" in query_data["expected_nodes"]["CKIT"]
        assert "CHEBI:18295" in query_data["expected_nodes"]["Histamine"]

    @pytest.mark.slow
    def test_load_pftq4_query(self):
        """Test loading PFTQ-4 query."""
        query_data = load_query_from_ods(TEST_QUERIES_FILE, "PFTQ-4")

        assert query_data["name"] == "PFTQ-4"
        assert query_data["start_label"] == "SLC6A20"
        assert "NCBIGene:54716" in query_data["start_curies"]
        assert "NCBIGene:27240" in query_data["start_curies"]
        assert query_data["end_label"] == "COVID-19"
        assert query_data["end_curies"] == ["MONDO:0100096"]

        # Check expected nodes
        assert "ACE2" in query_data["expected_nodes"]
        assert "NRF2" in query_data["expected_nodes"]

    @pytest.mark.slow
    def test_query_without_expected_nodes(self):
        """Test that query loads even if some expected nodes lack CURIEs."""
        # PFTQ-20 has some expected nodes with NaN in column C
        query_data = load_query_from_ods(TEST_QUERIES_FILE, "PFTQ-20")

        assert query_data["name"] == "PFTQ-20"
        # Should only include expected nodes that have CURIEs
        for label, curies in query_data["expected_nodes"].items():
            assert len(curies) > 0, f"Expected node '{label}' should have CURIEs"

    @pytest.mark.slow
    def test_handles_concatenated_curies_in_column_c(self):
        """Test that the parser correctly handles garbagey concatenated CURIEs in column C."""
        # This is the key test - column C can have various formats that need parsing
        query_data = load_query_from_ods(TEST_QUERIES_FILE, "PFTQ-1-c")

        # Verify all expected nodes have valid CURIE lists
        for label, curies in query_data["expected_nodes"].items():
            assert isinstance(curies, list)
            assert len(curies) > 0
            for curie in curies:
                assert ":" in curie, f"Invalid CURIE format: {curie}"
