"""Tests for filter functions."""
import pytest
from pathfilter.filters import (
    no_dupe_types,
    no_expression,
    no_related_to,
    no_end_pheno,
    no_chemical_start,
    all_paths,
    apply_filters,
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
