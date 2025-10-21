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

    def test_annotation_stripping_simple(self):
        """Test parsing CURIEs with simple text annotations."""
        result = parse_concatenated_curies("NCBIGene:2739 -> human gene")
        assert result == ["NCBIGene:2739"]

    def test_annotation_stripping_multiple_curies(self):
        """Test parsing multiple CURIEs with annotations from PFTQ-2-i."""
        input_str = "NCBIGene:2739 -> human geneAraPort:AT3G14420 -> Arabidopsis geneNCBIGene:855009 -> yeast gene"
        result = parse_concatenated_curies(input_str)
        assert result == ["NCBIGene:2739", "AraPort:AT3G14420", "NCBIGene:855009"]

    def test_annotation_stripping_concatenated_prefix(self):
        """Test parsing CURIEs where annotation text is concatenated with next CURIE prefix."""
        input_str = "UMLS:C5543862 -> human protein RNFT2NCBIGene:269695 -> rat geneNCBIGene:84900 -> human gene RNFT2"
        result = parse_concatenated_curies(input_str)
        assert result == ["UMLS:C5543862", "NCBIGene:269695", "NCBIGene:84900"]

    def test_annotation_stripping_single_go_term(self):
        """Test parsing single GO term without annotations."""
        result = parse_concatenated_curies("GO:0034599")
        assert result == ["GO:0034599"]


class TestIsValidCurie:
    """Tests for is_valid_curie validation function."""

    def test_valid_curies(self):
        """Test that valid CURIEs pass validation."""
        from pathfilter.curie_utils import is_valid_curie

        valid_curies = [
            "CHEBI:31690",
            "NCBIGene:2739",
            "GO:0034599",
            "MONDO:0004979",
            "UniProtKB:Q14494-1",
            "ENSEMBL:ENSG00000267497",
        ]
        for curie in valid_curies:
            assert is_valid_curie(curie), f"{curie} should be valid"

    def test_invalid_curies(self):
        """Test that invalid strings fail validation."""
        from pathfilter.curie_utils import is_valid_curie

        invalid_curies = [
            "human gene",  # No colon
            "NCBIGene:2739 -> human gene",  # Contains annotation
            "invalid",  # No colon
            "TOO:MANY:COLONS",  # Multiple colons
            "nocolon",  # No colon
            "",  # Empty string
            "lowercase:123",  # Prefix doesn't start with uppercase
            "PREFIX:",  # Empty ID
            ":12345",  # Empty prefix
        ]
        for curie in invalid_curies:
            assert not is_valid_curie(curie), f"{curie} should be invalid"


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
