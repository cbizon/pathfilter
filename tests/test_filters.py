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
    no_dupe_but_gene,
    no_nonconsecutive_dupe,
    all_paths,
    apply_filters,
    load_node_characteristics,
    create_min_ic_filter,
    create_max_degree_filter,
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


class TestNoDupeButGene:
    """Tests for no_dupe_but_gene filter."""

    def test_gene_duplicates_pass(self):
        """Gene/Protein duplicates should be allowed."""
        path = make_path("biolink:Disease --> biolink:Gene --> biolink:Gene --> biolink:SmallMolecule")
        assert no_dupe_but_gene(path) is True

    def test_nonconsecutive_gene_duplicates_pass(self):
        """Non-consecutive Gene duplicates should be allowed."""
        path = make_path("biolink:Disease --> biolink:Gene --> biolink:SmallMolecule --> biolink:Gene")
        assert no_dupe_but_gene(path) is True

    def test_protein_gene_duplicates_pass(self):
        """Protein and Gene should be treated as equivalent (both allowed to repeat)."""
        path = make_path("biolink:Disease --> biolink:Protein --> biolink:SmallMolecule --> biolink:Gene")
        assert no_dupe_but_gene(path) is True

    def test_all_genes_pass(self):
        """Path with all Gene/Protein types should pass."""
        path = make_path("biolink:Gene --> biolink:Gene --> biolink:Protein --> biolink:Gene")
        assert no_dupe_but_gene(path) is True

    def test_non_gene_duplicates_fail(self):
        """Non-Gene duplicate types should fail."""
        path = make_path("biolink:Disease --> biolink:Gene --> biolink:Disease --> biolink:SmallMolecule")
        assert no_dupe_but_gene(path) is False

    def test_chemical_duplicates_fail(self):
        """Chemical type duplicates should fail."""
        path = make_path("biolink:Disease --> biolink:ChemicalEntity --> biolink:Gene --> biolink:SmallMolecule")
        assert no_dupe_but_gene(path) is False

    def test_all_different_types_pass(self):
        """Path with all different types should pass."""
        path = make_path("biolink:Disease --> biolink:SmallMolecule --> biolink:Gene --> biolink:AnatomicalEntity")
        assert no_dupe_but_gene(path) is True

    def test_disease_duplicates_fail(self):
        """Disease duplicates should fail."""
        path = make_path("biolink:Disease --> biolink:Disease --> biolink:Gene --> biolink:SmallMolecule")
        assert no_dupe_but_gene(path) is False

    def test_mixed_gene_with_unique_others_pass(self):
        """Multiple genes with unique other types should pass."""
        path = make_path("biolink:Disease --> biolink:Gene --> biolink:Protein --> biolink:AnatomicalEntity")
        assert no_dupe_but_gene(path) is True


class TestNoNonconsecutiveDupe:
    """Tests for no_nonconsecutive_dupe filter."""

    def test_nonconsecutive_duplicates_fail(self):
        """Non-consecutive duplicate types should fail."""
        path = make_path("biolink:Disease --> biolink:Gene --> biolink:Disease --> biolink:SmallMolecule")
        assert no_nonconsecutive_dupe(path) is False

    def test_consecutive_duplicates_pass(self):
        """Consecutive duplicate types should pass."""
        path = make_path("biolink:Disease --> biolink:Disease --> biolink:Gene --> biolink:SmallMolecule")
        assert no_nonconsecutive_dupe(path) is True

    def test_all_different_types_pass(self):
        """Path with all different types should pass."""
        path = make_path("biolink:Disease --> biolink:SmallMolecule --> biolink:Gene --> biolink:AnatomicalEntity")
        assert no_nonconsecutive_dupe(path) is True

    def test_nonconsecutive_chemical_types_fail(self):
        """Non-consecutive chemical types should fail (SmallMolecule and ChemicalEntity are equivalent)."""
        path = make_path("biolink:SmallMolecule --> biolink:Gene --> biolink:Disease --> biolink:ChemicalEntity")
        assert no_nonconsecutive_dupe(path) is False

    def test_consecutive_chemical_types_pass(self):
        """Consecutive chemical types should pass."""
        path = make_path("biolink:SmallMolecule --> biolink:ChemicalEntity --> biolink:Gene --> biolink:Disease")
        assert no_nonconsecutive_dupe(path) is True

    def test_nonconsecutive_gene_protein_fail(self):
        """Non-consecutive Gene and Protein should fail (equivalent types)."""
        path = make_path("biolink:Gene --> biolink:Disease --> biolink:SmallMolecule --> biolink:Protein")
        assert no_nonconsecutive_dupe(path) is False

    def test_consecutive_gene_protein_pass(self):
        """Consecutive Gene and Protein should pass."""
        path = make_path("biolink:Gene --> biolink:Protein --> biolink:Disease --> biolink:SmallMolecule")
        assert no_nonconsecutive_dupe(path) is True

    def test_all_same_type_pass(self):
        """All same type (consecutive) should pass."""
        path = make_path("biolink:Disease --> biolink:Disease --> biolink:Disease --> biolink:Disease")
        assert no_nonconsecutive_dupe(path) is True

    def test_triple_nonconsecutive_fail(self):
        """Type appearing at positions 0 and 2 should fail (non-consecutive)."""
        path = make_path("biolink:Gene --> biolink:Disease --> biolink:Gene --> biolink:SmallMolecule")
        assert no_nonconsecutive_dupe(path) is False

    def test_triple_consecutive_pass(self):
        """Three consecutive instances of same type should pass."""
        path = make_path("biolink:Gene --> biolink:Gene --> biolink:Gene --> biolink:SmallMolecule")
        assert no_nonconsecutive_dupe(path) is True


class TestInformationContentFilters:
    """Tests for information content-based filters."""

    @pytest.fixture
    def sample_ic_file(self):
        """Create a temporary node_degrees file for testing."""
        content = """Query\tCURIE\tName\tPath_Count\tHit_Path_Count\tHit_Path_Fraction\tNode_degree\tInformation_content\tIs_Expected
PFTQ-1\tMONDO:0004979\tAsthma\t100\t10\t0.1\t100\t75.5\tFalse
PFTQ-1\tNCBIGene:7124\tTNF\t500\t50\t0.1\t500\t45.2\tFalse
PFTQ-1\tCHEBI:31690\tImatinib\t50\t5\t0.1\t50\t60.0\tFalse
PFTQ-1\tMONDO:0005148\tType 2 diabetes\t200\t20\t0.1\t200\t\tFalse
PFTQ-1\tUniProtKB:P12345\tSomeProtein\t10\t1\t0.1\t10\t100.0\tFalse
PFTQ-1\tPUBCHEM:12345\tGenericCompound\t5\t1\t0.2\t5\t20.5\tFalse"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tsv') as f:
            f.write(content)
            temp_path = f.name

        yield temp_path

        # Cleanup
        os.unlink(temp_path)

    def test_load_information_content(self, sample_ic_file):
        """Test loading IC data from TSV file."""
        ic_data, _, _ = load_node_characteristics(sample_ic_file)

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
        ic_data, _, _ = load_node_characteristics(sample_ic_file)
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
        ic_data, _, _ = load_node_characteristics(sample_ic_file)
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
        ic_data, _, _ = load_node_characteristics(sample_ic_file)
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
        ic_data, _, _ = load_node_characteristics(sample_ic_file)
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
        ic_data, _, _ = load_node_characteristics(sample_ic_file)
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
        ic_data, _, _ = load_node_characteristics(sample_ic_file)
        filter_func = create_min_ic_filter(ic_data, min_ic=50.0)

        # Intermediate nodes (pos 1, 2) have IC >= 50
        # CHEBI:31690=60.0, UniProtKB:P12345=100.0 (missing)
        path_pass = Path(
            path_labels="test",
            path_curies=["MONDO:0004979", "CHEBI:31690", "UniProtKB:P12345", "NCBIGene:7124"],
            num_paths=1,
            categories="test",
            first_hop_predicates="test",
            second_hop_predicates="test",
            third_hop_predicates="test",
            has_gene=True,
            metapaths="test"
        )
        assert filter_func(path_pass) is True

        # Intermediate node (pos 1): NCBIGene:7124 has IC=45.2, below threshold
        path_fail = Path(
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
        assert filter_func(path_fail) is False

    def test_min_ic_70_threshold(self, sample_ic_file):
        """Test IC filter with threshold of 70."""
        ic_data, _, _ = load_node_characteristics(sample_ic_file)
        filter_func = create_min_ic_filter(ic_data, min_ic=70.0)

        # Intermediate nodes (pos 1, 2): MONDO:0005148=82.1, UniProtKB:P12345=100.0 (missing)
        path_pass = Path(
            path_labels="test",
            path_curies=["PUBCHEM:12345", "MONDO:0005148", "UniProtKB:P12345", "CHEBI:31690"],
            num_paths=1,
            categories="test",
            first_hop_predicates="test",
            second_hop_predicates="test",
            third_hop_predicates="test",
            has_gene=True,
            metapaths="test"
        )
        assert filter_func(path_pass) is True

        # Intermediate node (pos 2): CHEBI:31690 has IC=60.0, below threshold
        path_fail = Path(
            path_labels="test",
            path_curies=["MONDO:0004979", "MONDO:0005148", "CHEBI:31690", "UniProtKB:P12345"],
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
        ic_data, _, _ = load_node_characteristics(sample_ic_file)
        filter_30 = create_min_ic_filter(ic_data, min_ic=30.0)
        filter_50 = create_min_ic_filter(ic_data, min_ic=50.0)
        filter_70 = create_min_ic_filter(ic_data, min_ic=70.0)

        assert filter_30.__name__ == "min_ic_30"
        assert filter_50.__name__ == "min_ic_50"
        assert filter_70.__name__ == "min_ic_70"

    def test_ic_filter_ignores_start_and_end_nodes(self, sample_ic_file):
        """Test that IC filter only checks intermediate nodes, not start/end."""
        ic_data, _, _ = load_node_characteristics(sample_ic_file)
        filter_func = create_min_ic_filter(ic_data, min_ic=70.0)

        # Start node (pos 0) has IC=20.5 (low), end node (pos 3) has IC=45.2 (low)
        # But intermediate nodes (pos 1, 2) have IC=75.5 and 100.0 (high)
        # Should PASS because only intermediate nodes are checked
        path = Path(
            path_labels="test",
            path_curies=["PUBCHEM:12345", "MONDO:0004979", "UniProtKB:P12345", "NCBIGene:7124"],
            num_paths=1,
            categories="test",
            first_hop_predicates="test",
            second_hop_predicates="test",
            third_hop_predicates="test",
            has_gene=True,
            metapaths="test"
        )
        assert filter_func(path) is True  # Passes despite low IC at start/end


class TestNodeDegreeFilters:
    """Tests for node degree-based filters."""

    @pytest.fixture
    def sample_degree_file(self):
        """Create a temporary TSV file with node degree and IC data."""
        content = """Query\tCURIE\tName\tPath_Count\tHit_Path_Count\tHit_Path_Fraction\tNode_degree\tInformation_content\tIs_Expected
PFTQ-1\tNODE1\tGene1\t100\t10\t0.1\t50\t60.0\tFalse
PFTQ-1\tNODE2\tGene2\t200\t20\t0.1\t200\t45.0\tFalse
PFTQ-1\tNODE3\tGene3\t600\t60\t0.1\t600\t30.0\tFalse
PFTQ-1\tNODE4\tDisease1\t1200\t120\t0.1\t1200\t80.0\tFalse
PFTQ-1\tNODE5\tChemical1\t50\t5\t0.1\t\t70.0\tFalse
PFTQ-1\tNODE6\tGene4\t10\t1\t0.1\t10\t\tFalse"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tsv') as f:
            f.write(content)
            temp_path = f.name

        yield temp_path
        os.unlink(temp_path)

    def test_load_node_degrees(self, sample_degree_file):
        """Test loading node degrees from file."""
        _, degree_data, _ = load_node_characteristics(sample_degree_file)

        assert degree_data["NODE1"] == 50
        assert degree_data["NODE2"] == 200
        assert degree_data["NODE3"] == 600
        assert degree_data["NODE4"] == 1200
        # Missing degree should be 0
        assert degree_data["NODE5"] == 0

    def test_load_node_characteristics(self, sample_degree_file):
        """Test loading both IC and degree data together."""
        ic_data, degree_data, path_count_data = load_node_characteristics(sample_degree_file)

        # Check IC data
        assert ic_data["NODE1"] == 60.0
        assert ic_data["NODE2"] == 45.0
        assert ic_data["NODE6"] == 100.0  # Missing IC → 100.0

        # Check degree data
        assert degree_data["NODE1"] == 50
        assert degree_data["NODE2"] == 200
        assert degree_data["NODE5"] == 0  # Missing degree → 0

        # Path count data may be empty for test file without Path_count column
        assert isinstance(path_count_data, dict)

    def test_max_degree_100_filter_accepts_low_degree(self, sample_degree_file):
        """Test max_degree_100 accepts paths with all nodes having degree <= 100."""
        _, degree_data, _ = load_node_characteristics(sample_degree_file)
        filter_func = create_max_degree_filter(degree_data, max_degree=100)

        # Path with degrees: 50, 10, 0 (missing), and unknown node (treated as 0)
        path_pass = make_path()
        path_pass.path_curies = ["NODE1", "NODE6", "NODE5", "UNKNOWN"]

        assert filter_func(path_pass) is True

    def test_max_degree_100_filter_rejects_high_degree(self, sample_degree_file):
        """Test max_degree_100 rejects paths with any node having degree > 100."""
        _, degree_data, _ = load_node_characteristics(sample_degree_file)
        filter_func = create_max_degree_filter(degree_data, max_degree=100)

        # Path with degrees: 50, 200 (> 100), 10, 0
        path_fail = make_path()
        path_fail.path_curies = ["NODE1", "NODE2", "NODE6", "NODE5"]

        assert filter_func(path_fail) is False

    def test_max_degree_500_filter(self, sample_degree_file):
        """Test max_degree_500 filter with appropriate thresholds."""
        _, degree_data, _ = load_node_characteristics(sample_degree_file)
        filter_func = create_max_degree_filter(degree_data, max_degree=500)

        # Path with degrees: 50, 200, 10 (all <= 500)
        path_pass = make_path()
        path_pass.path_curies = ["NODE1", "NODE2", "NODE6", "NODE5"]
        assert filter_func(path_pass) is True

        # Path with degrees: 200, 600 (> 500), 50
        path_fail = make_path()
        path_fail.path_curies = ["NODE2", "NODE3", "NODE1", "NODE5"]
        assert filter_func(path_fail) is False

    def test_max_degree_1000_filter(self, sample_degree_file):
        """Test max_degree_1000 filter with high threshold."""
        _, degree_data, _ = load_node_characteristics(sample_degree_file)
        filter_func = create_max_degree_filter(degree_data, max_degree=1000)

        # Path with degrees: 50, 200, 600 (all <= 1000)
        path_pass = make_path()
        path_pass.path_curies = ["NODE1", "NODE2", "NODE3", "NODE5"]
        assert filter_func(path_pass) is True

        # Path with degrees: 50, 1200 (> 1000), 200
        path_fail = make_path()
        path_fail.path_curies = ["NODE1", "NODE4", "NODE2", "NODE5"]
        assert filter_func(path_fail) is False

    def test_missing_degree_treated_as_zero(self, sample_degree_file):
        """Test that nodes with missing degree data are treated as degree=0."""
        _, degree_data, _ = load_node_characteristics(sample_degree_file)
        filter_func = create_max_degree_filter(degree_data, max_degree=100)

        # Path with missing degree (NODE5) and unknown node
        path_pass = make_path()
        path_pass.path_curies = ["NODE5", "UNKNOWN_NODE", "NODE1", "NODE6"]

        # Should pass because missing/unknown degrees are treated as 0
        assert filter_func(path_pass) is True

    def test_degree_filter_function_names(self, sample_degree_file):
        """Test that created filters have descriptive names."""
        _, degree_data, _ = load_node_characteristics(sample_degree_file)
        filter_100 = create_max_degree_filter(degree_data, max_degree=100)
        filter_500 = create_max_degree_filter(degree_data, max_degree=500)
        filter_1000 = create_max_degree_filter(degree_data, max_degree=1000)

        assert filter_100.__name__ == "max_degree_100"
        assert filter_500.__name__ == "max_degree_500"
        assert filter_1000.__name__ == "max_degree_1000"

    def test_ic_and_degree_filters_together(self, sample_degree_file):
        """Test that IC and degree filters can work together on the same path."""
        ic_data, degree_data, _ = load_node_characteristics(sample_degree_file)
        ic_filter = create_min_ic_filter(ic_data, min_ic=50.0)
        degree_filter = create_max_degree_filter(degree_data, max_degree=100)

        # Path that passes both filters
        # Intermediate nodes: NODE1 (IC=60, degree=50), NODE6 (IC=100, degree=10)
        path_pass = make_path()
        path_pass.path_curies = ["UNKNOWN", "NODE1", "NODE6", "NODE5"]
        assert ic_filter(path_pass) is True
        assert degree_filter(path_pass) is True

        # Path that fails IC filter (intermediate node has IC < 50)
        # Intermediate node NODE2: IC=45 (<50), degree=200
        path_fail_ic = make_path()
        path_fail_ic.path_curies = ["NODE1", "NODE2", "NODE6", "NODE5"]
        assert ic_filter(path_fail_ic) is False

        # Path that fails degree filter (intermediate node has degree > 100)
        # Intermediate node NODE2: IC=45, degree=200 (>100)
        path_fail_degree = make_path()
        path_fail_degree.path_curies = ["NODE1", "NODE2", "NODE6", "NODE5"]
        assert degree_filter(path_fail_degree) is False

    def test_degree_filter_ignores_start_and_end_nodes(self, sample_degree_file):
        """Test that degree filter only checks intermediate nodes, not start/end."""
        _, degree_data, _ = load_node_characteristics(sample_degree_file)
        filter_func = create_max_degree_filter(degree_data, max_degree=100)

        # Start node (pos 0) has degree=1200 (high), end node (pos 3) has degree=600 (high)
        # But intermediate nodes (pos 1, 2) have degree=50 and 10 (low)
        # Should PASS because only intermediate nodes are checked
        path = make_path()
        path.path_curies = ["NODE4", "NODE1", "NODE6", "NODE3"]
        assert filter_func(path) is True  # Passes despite high degree at start/end
