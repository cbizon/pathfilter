"""Tests for CURIE parsing utilities."""
import pytest
from pathfilter.curie_utils import parse_concatenated_curies, parse_path_curies


class TestParseConcatenatedCuries:
    """Tests for parse_concatenated_curies function."""

    def test_single_curie(self):
        """Test parsing a single CURIE."""
        result = parse_concatenated_curies("CHEBI:31690")
        assert result == ["CHEBI:31690"]

    def test_two_mondo_curies(self):
        """Test parsing two MONDO CURIEs."""
        result = parse_concatenated_curies("MONDO:0004979MONDO:0004784")
        assert result == ["MONDO:0004979", "MONDO:0004784"]

    def test_mixed_prefixes(self):
        """Test parsing CURIEs with different prefixes."""
        result = parse_concatenated_curies("CHEBI:18295PR:000049994")
        assert result == ["CHEBI:18295", "PR:000049994"]

    def test_ncbi_gene_and_ncit(self):
        """Test parsing NCBIGene and NCIT CURIEs."""
        result = parse_concatenated_curies("NCBIGene:3815NCIT:C39712")
        assert result == ["NCBIGene:3815", "NCIT:C39712"]

    def test_complex_concatenation(self):
        """Test parsing multiple CURIEs of various types."""
        result = parse_concatenated_curies("NCBIGene:54716NCBIGene:27240")
        assert result == ["NCBIGene:54716", "NCBIGene:27240"]

    def test_empty_string(self):
        """Test parsing an empty string."""
        result = parse_concatenated_curies("")
        assert result == []

    def test_nan_value(self):
        """Test parsing NaN value."""
        result = parse_concatenated_curies("nan")
        assert result == []

    def test_none_value(self):
        """Test parsing None value."""
        result = parse_concatenated_curies(None)
        assert result == []

    def test_whitespace_only(self):
        """Test parsing whitespace-only string."""
        result = parse_concatenated_curies("   ")
        assert result == []

    def test_with_hyphens_in_id(self):
        """Test parsing CURIEs with hyphens in ID."""
        result = parse_concatenated_curies("UNII:7SE5582Q2P")
        assert result == ["UNII:7SE5582Q2P"]

    def test_ensembl_curies(self):
        """Test parsing ENSEMBL CURIEs."""
        result = parse_concatenated_curies("ENSEMBL:ENSG00000229666ENSEMBL:ENSG00000269145")
        assert result == ["ENSEMBL:ENSG00000229666", "ENSEMBL:ENSG00000269145"]

    def test_very_long_concatenation(self):
        """Test parsing many concatenated CURIEs."""
        input_str = "NCBIGene:22983NCBIGene:23139NCBIGene:23031NCBIGene:375449"
        result = parse_concatenated_curies(input_str)
        expected = ["NCBIGene:22983", "NCBIGene:23139", "NCBIGene:23031", "NCBIGene:375449"]
        assert result == expected

    def test_chv_prefix(self):
        """Test parsing CHV CURIEs."""
        result = parse_concatenated_curies("CHV:0000014716NCBIGene:3815")
        assert result == ["CHV:0000014716", "NCBIGene:3815"]

    def test_umls_prefix(self):
        """Test parsing UMLS CURIEs."""
        result = parse_concatenated_curies("NCBIGene:4254UMLS:C4743026")
        assert result == ["NCBIGene:4254", "UMLS:C4743026"]


class TestParsePathCuries:
    """Tests for parse_path_curies function."""

    def test_typical_path(self):
        """Test parsing a typical path_curies string."""
        input_str = "CHEBI:15647 --> NCBIGene:100133941 --> NCBIGene:4907 --> UNII:31YO63LBSN"
        result = parse_path_curies(input_str)
        expected = ["CHEBI:15647", "NCBIGene:100133941", "NCBIGene:4907", "UNII:31YO63LBSN"]
        assert result == expected

    def test_short_path(self):
        """Test parsing a short path with two nodes."""
        input_str = "MONDO:0005011 --> MONDO:0005180"
        result = parse_path_curies(input_str)
        expected = ["MONDO:0005011", "MONDO:0005180"]
        assert result == expected

    def test_empty_string(self):
        """Test parsing an empty path string."""
        result = parse_path_curies("")
        assert result == []

    def test_single_curie_no_arrow(self):
        """Test parsing a single CURIE without arrows."""
        result = parse_path_curies("CHEBI:31690")
        assert result == ["CHEBI:31690"]

    def test_with_extra_whitespace(self):
        """Test that extra whitespace is handled."""
        input_str = "CHEBI:15647  -->  NCBIGene:100133941  -->  UNII:31YO63LBSN"
        result = parse_path_curies(input_str)
        # Should still parse correctly even with extra spaces
        expected = ["CHEBI:15647", "NCBIGene:100133941", "UNII:31YO63LBSN"]
        assert result == expected
