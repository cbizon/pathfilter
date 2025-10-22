"""Tests for filter functions."""
import pytest
import tempfile
import os
from pathfilter.filters import (
    no_dupe_types,
    no_expression,
    no_related_to,
    no_end_pheno,
    no_chemical_start,
    no_repeat_predicates,
    no_abab,
    all_paths,
    apply_filters,
    load_information_content,
    create_min_ic_filter,
    DEFAULT_FILTERS,
    STRICT_FILTERS
)
from pathfilter.path_loader import Path


def make_path(categories="A --> B --> C --> D",
              first_hop="{'biolink:affects'}",
              second_hop="{'biolink:affects'}",
              third_hop="{'biolink:affects'}"):
    """Helper to create test paths."""
    return Path(
        path_labels="A -> B -> C -> D",
        path_curies=["ID1", "ID2", "ID3", "ID4"],
        num_paths=1,
        categories=categories,
        first_hop_predicates=first_hop,
        second_hop_predicates=second_hop,
        third_hop_predicates=third_hop,
        has_gene=True,
        metapaths="['test']"
    )


class TestNoDupeTypes:
    """Tests for no_dupe_types filter."""

    def test_four_unique_types_pass(self):
        """Path with 4 unique types should pass."""
        path = make_path("biolink:Disease --> biolink:SmallMolecule --> biolink:Gene --> biolink:Protein")
        # Note: Protein normalizes to Gene, SmallMolecule stays, so we need truly different types
        path = make_path("biolink:Disease --> biolink:SmallMolecule --> biolink:Gene --> biolink:AnatomicalEntity")
        assert no_dupe_types(path) is True

    def test_duplicate_types_fail(self):
        """Path with duplicate types should fail."""
        path = make_path("biolink:Disease --> biolink:Disease --> biolink:Gene --> biolink:SmallMolecule")
        assert no_dupe_types(path) is False

    def test_chemical_normalization(self):
        """ChemicalEntity and SmallMolecule should be treated as same type."""
        path = make_path("biolink:Disease --> biolink:ChemicalEntity --> biolink:Gene --> biolink:SmallMolecule")
        # Has Disease, Chemical (2x), Gene = 3 unique types, needs 4
        assert no_dupe_types(path) is False

    def test_protein_gene_normalization(self):
        """Protein should normalize to Gene."""
        path = make_path("biolink:Disease --> biolink:SmallMolecule --> biolink:Protein --> biolink:Gene")
        # Has Disease, Chemical, Gene (2x) = 3 unique types, needs 4
        assert no_dupe_types(path) is False


class TestNoExpression:
    """Tests for no_expression filter."""

    def test_no_expressed_in_pass(self):
        """Path without expressed_in should pass."""
        path = make_path(
            first_hop="{'biolink:affects'}",
            second_hop="{'biolink:interacts_with'}",
            third_hop="{'biolink:regulates'}"
        )
        assert no_expression(path) is True

    def test_expressed_in_first_hop_fail(self):
        """Path with expressed_in in first hop should fail."""
        path = make_path(first_hop="{'biolink:expressed_in'}")
        assert no_expression(path) is False

    def test_expressed_in_second_hop_fail(self):
        """Path with expressed_in in second hop should fail."""
        path = make_path(second_hop="{'biolink:expressed_in'}")
        assert no_expression(path) is False

    def test_expressed_in_third_hop_fail(self):
        """Path with expressed_in in third hop should fail."""
        path = make_path(third_hop="{'biolink:expressed_in'}")
        assert no_expression(path) is False


class TestNoRelatedTo:
    """Tests for no_related_to filter."""

    def test_no_related_to_pass(self):
        """Path without related_to should pass."""
        path = make_path(
            first_hop="{'biolink:affects'}",
            second_hop="{'biolink:treats'}",
            third_hop="{'biolink:causes'}"
        )
        assert no_related_to(path) is True

    def test_related_to_in_predicates_fail(self):
        """Path with related_to predicate should fail."""
        path = make_path(first_hop="{'biolink:related_to'}")
        assert no_related_to(path) is False

    def test_related_to_in_categories_fail(self):
        """Path with related_to in categories should fail."""
        path = make_path(categories="biolink:Disease --> {'biolink:related_to'} --> biolink:Gene --> biolink:Drug")
        assert no_related_to(path) is False


class TestNoEndPheno:
    """Tests for no_end_pheno filter."""

    def test_not_ending_with_pheno_pass(self):
        """Path not ending with PhenotypicFeature->SmallMolecule should pass."""
        path = make_path("biolink:Disease --> biolink:Gene --> biolink:Protein --> biolink:SmallMolecule")
        assert no_end_pheno(path) is True

    def test_ending_with_pheno_fail(self):
        """Path ending with PhenotypicFeature->SmallMolecule should fail."""
        path = make_path("biolink:Disease --> biolink:Gene --> biolink:PhenotypicFeature --> biolink:SmallMolecule")
        assert no_end_pheno(path) is False


class TestNoChemicalStart:
    """Tests for no_chemical_start filter."""

    def test_not_disease_chemical_start_pass(self):
        """Path not starting with Disease->Chemical should pass."""
        path = make_path("biolink:Disease --> biolink:Gene --> biolink:SmallMolecule --> biolink:Disease")
        assert no_chemical_start(path) is True

    def test_disease_small_molecule_start_fail(self):
        """Path starting with Disease->SmallMolecule should fail."""
        path = make_path("biolink:Disease --> biolink:SmallMolecule --> biolink:Gene --> biolink:Protein")
        assert no_chemical_start(path) is False

    def test_disease_chemical_entity_start_fail(self):
        """Path starting with Disease->ChemicalEntity should fail."""
        path = make_path("biolink:Disease --> biolink:ChemicalEntity --> biolink:Gene --> biolink:Protein")
        assert no_chemical_start(path) is False

    def test_disease_molecular_mixture_start_fail(self):
        """Path starting with Disease->MolecularMixture should fail."""
        path = make_path("biolink:Disease --> biolink:MolecularMixture --> biolink:Gene --> biolink:Protein")
        assert no_chemical_start(path) is False


class TestAllPaths:
    """Tests for all_paths filter."""

    def test_always_pass(self):
        """all_paths should always return True."""
        path = make_path()
        assert all_paths(path) is True


class TestApplyFilters:
    """Tests for applying multiple filters."""

    def test_single_filter(self):
        """Test applying a single filter."""
        paths = [
            make_path("biolink:Disease --> biolink:SmallMolecule --> biolink:Gene --> biolink:AnatomicalEntity"),
            make_path("biolink:Disease --> biolink:Disease --> biolink:Gene --> biolink:SmallMolecule"),
        ]

        filtered = apply_filters(paths, [no_dupe_types])
        assert len(filtered) == 1

    def test_multiple_filters(self):
        """Test applying multiple filters."""
        paths = [
            # Passes both filters
            make_path(
                "biolink:Disease --> biolink:SmallMolecule --> biolink:Gene --> biolink:AnatomicalEntity",
                first_hop="{'biolink:affects'}"
            ),
            # Fails no_dupe_types
            make_path(
                "biolink:Disease --> biolink:Disease --> biolink:Gene --> biolink:SmallMolecule",
                first_hop="{'biolink:affects'}"
            ),
            # Fails no_expression
            make_path(
                "biolink:Disease --> biolink:SmallMolecule --> biolink:Gene --> biolink:AnatomicalEntity",
                first_hop="{'biolink:expressed_in'}"
            ),
        ]

        filtered = apply_filters(paths, [no_dupe_types, no_expression])
        assert len(filtered) == 1

    def test_no_filters(self):
        """Test with no filters (all pass)."""
        paths = [make_path() for _ in range(5)]
        filtered = apply_filters(paths, [all_paths])
        assert len(filtered) == 5

    def test_default_filters(self):
        """Test using DEFAULT_FILTERS."""
        paths = [
            # Good path
            make_path(
                "biolink:Disease --> biolink:SmallMolecule --> biolink:Gene --> biolink:AnatomicalEntity",
                first_hop="{'biolink:treats'}",
                second_hop="{'biolink:affects'}",
                third_hop="{'biolink:located_in'}"
            ),
            # Has duplicate types
            make_path(
                "biolink:Disease --> biolink:Disease --> biolink:Gene --> biolink:SmallMolecule"
            ),
        ]

        filtered = apply_filters(paths, DEFAULT_FILTERS)
        assert len(filtered) == 1


class TestNoRepeatPredicates:
    """Tests for no_repeat_predicates filter."""

    def test_all_unique_predicates_pass(self):
        """Path with all unique predicates should pass."""
        path = make_path(
            first_hop="{'biolink:treats'}",
            second_hop="{'biolink:affects'}",
            third_hop="{'biolink:located_in'}"
        )
        assert no_repeat_predicates(path) is True

    def test_repeated_predicate_fail(self):
        """Path with repeated predicate should fail."""
        path = make_path(
            first_hop="{'biolink:affects'}",
            second_hop="{'biolink:treats'}",
            third_hop="{'biolink:affects'}"
        )
        assert no_repeat_predicates(path) is False

    def test_all_same_predicates_fail(self):
        """Path with all same predicates should fail."""
        path = make_path(
            first_hop="{'biolink:affects'}",
            second_hop="{'biolink:affects'}",
            third_hop="{'biolink:affects'}"
        )
        assert no_repeat_predicates(path) is False

    def test_two_repeated_predicates_fail(self):
        """Path with two instances of repeated predicate should fail."""
        path = make_path(
            first_hop="{'biolink:treats'}",
            second_hop="{'biolink:treats'}",
            third_hop="{'biolink:located_in'}"
        )
        assert no_repeat_predicates(path) is False


class TestNoABAB:
    """Tests for no_abab filter."""

    def test_non_abab_pattern_pass(self):
        """Path without ABAB pattern should pass."""
        path = make_path("biolink:Disease --> biolink:SmallMolecule --> biolink:Gene --> biolink:AnatomicalEntity")
        assert no_abab(path) is True

    def test_abab_disease_gene_fail(self):
        """Disease -> Gene -> Disease -> Gene should fail."""
        path = make_path("biolink:Disease --> biolink:Gene --> biolink:Disease --> biolink:Gene")
        assert no_abab(path) is False

    def test_abab_chemical_gene_fail(self):
        """Chemical -> Gene -> Chemical -> Gene should fail."""
        path = make_path("biolink:SmallMolecule --> biolink:Gene --> biolink:ChemicalEntity --> biolink:Gene")
        assert no_abab(path) is False

    def test_abab_with_disease_pheno_equivalence_fail(self):
        """Disease -> Gene -> PhenotypicFeature -> Gene should fail (Disease == Pheno)."""
        path = make_path("biolink:Disease --> biolink:Gene --> biolink:PhenotypicFeature --> biolink:Gene")
        assert no_abab(path) is False

    def test_abab_with_protein_gene_equivalence_fail(self):
        """Disease -> Gene -> Disease -> Protein should fail (Gene == Protein)."""
        path = make_path("biolink:Disease --> biolink:Gene --> biolink:Disease --> biolink:Protein")
        assert no_abab(path) is False

    def test_abab_with_chemical_equivalence_fail(self):
        """SmallMolecule -> Gene -> MolecularMixture -> Gene should fail (both chemicals)."""
        path = make_path("biolink:SmallMolecule --> biolink:Gene --> biolink:MolecularMixture --> biolink:Gene")
        assert no_abab(path) is False

    def test_abba_pattern_pass(self):
        """ABBA pattern should pass (not ABAB)."""
        path = make_path("biolink:Disease --> biolink:Gene --> biolink:Gene --> biolink:Disease")
        assert no_abab(path) is True

    def test_aaab_pattern_pass(self):
        """AAAB pattern should pass (not ABAB)."""
        path = make_path("biolink:Disease --> biolink:Disease --> biolink:Disease --> biolink:Gene")
        assert no_abab(path) is True

    def test_all_same_type_pass(self):
        """AAAA pattern should pass (not ABAB since A==B required for ABAB)."""
        path = make_path("biolink:Disease --> biolink:Disease --> biolink:Disease --> biolink:Disease")
        assert no_abab(path) is True


class TestInformationContentFilters:
    """Tests for information content-based filters."""

    @pytest.fixture
    def sample_ic_file(self):
        """Create a temporary node_degrees file for testing."""
        content = """Node_id\tName\tNode_degree\tInformation_content
MONDO:0004979\tAsthma\t100\t75.5
NCBIGene:7124\tTNF\t500\t45.2
CHEBI:31690\tImatinib\t50\t60.0
MONDO:0005148\tType 2 diabetes\t200\t
UniProtKB:P12345\tSomeProtein\t10\t100.0
PUBCHEM:12345\tGenericCompound\t5\t20.5"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tsv') as f:
            f.write(content)
            temp_path = f.name

        yield temp_path

        # Cleanup
        os.unlink(temp_path)

    def test_load_information_content(self, sample_ic_file):
        """Test loading IC data from TSV file."""
        ic_data = load_information_content(sample_ic_file)

        # Check loaded values
        assert ic_data['MONDO:0004979'] == 75.5
        assert ic_data['NCBIGene:7124'] == 45.2
        assert ic_data['CHEBI:31690'] == 60.0
        assert ic_data['UniProtKB:P12345'] == 100.0
        assert ic_data['PUBCHEM:12345'] == 20.5

        # Missing IC should be treated as 100.0
        assert ic_data['MONDO:0005148'] == 100.0

    def test_create_min_ic_filter_pass(self, sample_ic_file):
        """Test IC filter passes paths where all nodes meet threshold."""
        ic_data = load_information_content(sample_ic_file)
        filter_func = create_min_ic_filter(ic_data, min_ic=40.0)

        # All nodes have IC >= 40
        path = Path(
            path_labels="test",
            path_curies=["MONDO:0004979", "NCBIGene:7124", "CHEBI:31690", "UniProtKB:P12345"],
            num_paths=1,
            categories="test",
            first_hop_predicates="test",
            second_hop_predicates="test",
            third_hop_predicates="test",
            has_gene=True,
            metapaths="test"
        )

        assert filter_func(path) is True

    def test_create_min_ic_filter_fail(self, sample_ic_file):
        """Test IC filter rejects paths where any node is below threshold."""
        ic_data = load_information_content(sample_ic_file)
        filter_func = create_min_ic_filter(ic_data, min_ic=50.0)

        # NCBIGene:7124 has IC=45.2, below threshold of 50
        path = Path(
            path_labels="test",
            path_curies=["MONDO:0004979", "NCBIGene:7124", "CHEBI:31690", "UniProtKB:P12345"],
            num_paths=1,
            categories="test",
            first_hop_predicates="test",
            second_hop_predicates="test",
            third_hop_predicates="test",
            has_gene=True,
            metapaths="test"
        )

        assert filter_func(path) is False

    def test_create_min_ic_filter_missing_node(self, sample_ic_file):
        """Test IC filter treats missing nodes as IC=100.0."""
        ic_data = load_information_content(sample_ic_file)
        filter_func = create_min_ic_filter(ic_data, min_ic=70.0)

        # UNKNOWN:123 not in IC data, should be treated as 100.0
        # MONDO:0004979 has IC=75.5, UniProtKB:P12345 has IC=100.0, both pass
        path = Path(
            path_labels="test",
            path_curies=["MONDO:0004979", "UNKNOWN:123", "UniProtKB:P12345"],
            num_paths=1,
            categories="test",
            first_hop_predicates="test",
            second_hop_predicates="test",
            third_hop_predicates="test",
            has_gene=True,
            metapaths="test"
        )

        assert filter_func(path) is True

    def test_create_min_ic_filter_empty_ic(self, sample_ic_file):
        """Test IC filter treats empty IC values as 100.0."""
        ic_data = load_information_content(sample_ic_file)
        filter_func = create_min_ic_filter(ic_data, min_ic=90.0)

        # MONDO:0005148 has empty IC, should be treated as 100.0
        path = Path(
            path_labels="test",
            path_curies=["MONDO:0005148", "UniProtKB:P12345"],
            num_paths=1,
            categories="test",
            first_hop_predicates="test",
            second_hop_predicates="test",
            third_hop_predicates="test",
            has_gene=True,
            metapaths="test"
        )

        assert filter_func(path) is True

    def test_min_ic_30_threshold(self, sample_ic_file):
        """Test IC filter with threshold of 30."""
        ic_data = load_information_content(sample_ic_file)
        filter_func = create_min_ic_filter(ic_data, min_ic=30.0)

        # PUBCHEM:12345 has IC=20.5, below threshold
        path = Path(
            path_labels="test",
            path_curies=["MONDO:0004979", "PUBCHEM:12345", "CHEBI:31690", "NCBIGene:7124"],
            num_paths=1,
            categories="test",
            first_hop_predicates="test",
            second_hop_predicates="test",
            third_hop_predicates="test",
            has_gene=True,
            metapaths="test"
        )

        assert filter_func(path) is False

    def test_min_ic_50_threshold(self, sample_ic_file):
        """Test IC filter with threshold of 50."""
        ic_data = load_information_content(sample_ic_file)
        filter_func = create_min_ic_filter(ic_data, min_ic=50.0)

        # All nodes >= 50
        path_pass = Path(
            path_labels="test",
            path_curies=["MONDO:0004979", "CHEBI:31690", "UniProtKB:P12345"],
            num_paths=1,
            categories="test",
            first_hop_predicates="test",
            second_hop_predicates="test",
            third_hop_predicates="test",
            has_gene=True,
            metapaths="test"
        )
        assert filter_func(path_pass) is True

        # NCBIGene:7124 has IC=45.2, below threshold
        path_fail = Path(
            path_labels="test",
            path_curies=["MONDO:0004979", "NCBIGene:7124", "CHEBI:31690"],
            num_paths=1,
            categories="test",
            first_hop_predicates="test",
            second_hop_predicates="test",
            third_hop_predicates="test",
            has_gene=True,
            metapaths="test"
        )
        assert filter_func(path_fail) is False

    def test_min_ic_70_threshold(self, sample_ic_file):
        """Test IC filter with threshold of 70."""
        ic_data = load_information_content(sample_ic_file)
        filter_func = create_min_ic_filter(ic_data, min_ic=70.0)

        # Only MONDO:0004979 (75.5) and empty IC nodes pass
        path_pass = Path(
            path_labels="test",
            path_curies=["MONDO:0004979", "MONDO:0005148", "UniProtKB:P12345"],
            num_paths=1,
            categories="test",
            first_hop_predicates="test",
            second_hop_predicates="test",
            third_hop_predicates="test",
            has_gene=True,
            metapaths="test"
        )
        assert filter_func(path_pass) is True

        # CHEBI:31690 has IC=60.0, below threshold
        path_fail = Path(
            path_labels="test",
            path_curies=["MONDO:0004979", "CHEBI:31690", "UniProtKB:P12345"],
            num_paths=1,
            categories="test",
            first_hop_predicates="test",
            second_hop_predicates="test",
            third_hop_predicates="test",
            has_gene=True,
            metapaths="test"
        )
        assert filter_func(path_fail) is False

    def test_filter_function_name(self, sample_ic_file):
        """Test that created filter has descriptive name."""
        ic_data = load_information_content(sample_ic_file)
        filter_30 = create_min_ic_filter(ic_data, min_ic=30.0)
        filter_50 = create_min_ic_filter(ic_data, min_ic=50.0)
        filter_70 = create_min_ic_filter(ic_data, min_ic=70.0)

        assert filter_30.__name__ == "min_ic_30"
        assert filter_50.__name__ == "min_ic_50"
        assert filter_70.__name__ == "min_ic_70"
