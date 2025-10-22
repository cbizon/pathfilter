"""Tests for evaluation metrics."""
import pytest
from pathfilter.evaluation import (
    FilterMetrics,
    evaluate_filter_strategy,
    evaluate_multiple_strategies,
    format_metrics_table
)
from pathfilter.filters import no_dupe_types, all_paths
from pathfilter.path_loader import Path
from pathfilter.normalization import normalize_curies


def make_path(categories="A --> B --> C --> D", curies=None,
              first_hop_predicates="{'biolink:affects'}",
              second_hop_predicates="{'biolink:affects'}",
              third_hop_predicates="{'biolink:affects'}"):
    """Helper to create test paths."""
    if curies is None:
        curies = ["ID1", "ID2", "ID3", "ID4"]
    return Path(
        path_labels="A -> B -> C -> D",
        path_curies=curies,
        num_paths=1,
        categories=categories,
        first_hop_predicates=first_hop_predicates,
        second_hop_predicates=second_hop_predicates,
        third_hop_predicates=third_hop_predicates,
        has_gene=True,
        metapaths="['test']"
    )


class TestFilterMetrics:
    """Tests for FilterMetrics calculations."""

    def test_recall_calculation(self):
        """Test recall calculation."""
        metrics = FilterMetrics(
            filter_name="test",
            total_paths_before=100,
            total_paths_after=50,
            expected_paths_before=20,
            expected_paths_after=15,
            expected_nodes_found_before=5,
            expected_nodes_found_after=4
        )

        assert metrics.recall == 15 / 20

    def test_precision_calculation(self):
        """Test precision calculation."""
        metrics = FilterMetrics(
            filter_name="test",
            total_paths_before=100,
            total_paths_after=50,
            expected_paths_before=20,
            expected_paths_after=15,
            expected_nodes_found_before=5,
            expected_nodes_found_after=4
        )

        assert metrics.precision_before == 20 / 100
        assert metrics.precision_after == 15 / 50

    def test_enrichment_calculation(self):
        """Test enrichment calculation."""
        metrics = FilterMetrics(
            filter_name="test",
            total_paths_before=100,
            total_paths_after=50,
            expected_paths_before=20,
            expected_paths_after=15,
            expected_nodes_found_before=5,
            expected_nodes_found_after=4
        )

        # precision_before = 20/100 = 0.2
        # precision_after = 15/50 = 0.3
        # enrichment = 0.3/0.2 = 1.5
        assert metrics.enrichment == pytest.approx(1.5)

    def test_retention_rate(self):
        """Test retention rate calculation."""
        metrics = FilterMetrics(
            filter_name="test",
            total_paths_before=100,
            total_paths_after=25,
            expected_paths_before=20,
            expected_paths_after=15,
            expected_nodes_found_before=5,
            expected_nodes_found_after=4
        )

        assert metrics.retention_rate == 0.25

    def test_expected_nodes_recall(self):
        """Test expected nodes recall."""
        metrics = FilterMetrics(
            filter_name="test",
            total_paths_before=100,
            total_paths_after=50,
            expected_paths_before=20,
            expected_paths_after=15,
            expected_nodes_found_before=5,
            expected_nodes_found_after=4
        )

        assert metrics.expected_nodes_recall == 4 / 5

    def test_zero_division_handling(self):
        """Test that zero divisions return 0.0."""
        metrics = FilterMetrics(
            filter_name="test",
            total_paths_before=0,
            total_paths_after=0,
            expected_paths_before=0,
            expected_paths_after=0,
            expected_nodes_found_before=0,
            expected_nodes_found_after=0
        )

        assert metrics.recall == 0.0
        assert metrics.precision_before == 0.0
        assert metrics.precision_after == 0.0
        assert metrics.enrichment == 0.0
        assert metrics.retention_rate == 0.0
        assert metrics.expected_nodes_recall == 0.0


class TestEvaluateFilterStrategy:
    """Tests for evaluating filter strategies."""

    def test_no_filter_evaluation(self):
        """Test evaluation with no filtering."""
        paths = [
            make_path(curies=["MONDO:0001", "NCBIGene:3815", "ID3", "ID4"]),
            make_path(curies=["ID1", "ID2", "ID3", "ID4"]),
            make_path(curies=["MONDO:0001", "ID2", "NCBIGene:3815", "ID4"]),
        ]

        # Create expected nodes set
        expected_norm = normalize_curies(["NCBIGene:3815"])
        expected_set = {expected_norm["NCBIGene:3815"]}

        metrics = evaluate_filter_strategy(
            paths, expected_set, [all_paths], "no_filter"
        )

        assert metrics.filter_name == "no_filter"
        assert metrics.total_paths_before == 3
        assert metrics.total_paths_after == 3
        assert metrics.retention_rate == 1.0

    def test_filter_removes_paths(self):
        """Test that filtering reduces path count."""
        paths = [
            # Passes filter
            make_path(
                categories="biolink:Disease --> biolink:SmallMolecule --> biolink:Gene --> biolink:AnatomicalEntity"
            ),
            # Fails filter (duplicate types)
            make_path(
                categories="biolink:Disease --> biolink:Disease --> biolink:Gene --> biolink:SmallMolecule"
            ),
        ]

        expected_set = set()  # No expected nodes for this test

        metrics = evaluate_filter_strategy(
            paths, expected_set, [no_dupe_types], "no_dupe_types"
        )

        assert metrics.total_paths_before == 2
        assert metrics.total_paths_after == 1
        assert metrics.retention_rate == 0.5


class TestEvaluateMultipleStrategies:
    """Tests for evaluating multiple strategies with optimized caching."""

    def test_multiple_strategies_optimized(self):
        """Test optimized evaluation with caching generates all combinations."""
        paths = [
            make_path(
                categories="biolink:Disease --> biolink:SmallMolecule --> biolink:Gene --> biolink:AnatomicalEntity"
            ),
            make_path(
                categories="biolink:Disease --> biolink:Disease --> biolink:Gene --> biolink:SmallMolecule"
            ),
        ]

        individual_filters = {
            "no_dupe_types": no_dupe_types
        }

        expected_set = set()

        results = evaluate_multiple_strategies(paths, expected_set, individual_filters)

        # Should generate: none (baseline), no_dupe_types (single)
        assert len(results) == 2

        # Find results by name
        none_result = next(r for r in results if r.filter_name == "none")
        dupe_result = next(r for r in results if r.filter_name == "no_dupe_types")

        assert none_result.total_paths_after == 2
        assert dupe_result.total_paths_after == 1

    def test_combinations_generated(self):
        """Test that all combinations are generated."""
        from pathfilter.filters import no_expression

        paths = [
            make_path(
                categories="biolink:Disease --> biolink:SmallMolecule --> biolink:Gene --> biolink:AnatomicalEntity",
                first_hop_predicates="{'biolink:treats'}"
            ),
            make_path(
                categories="biolink:Disease --> biolink:Disease --> biolink:Gene --> biolink:SmallMolecule",
                first_hop_predicates="{'biolink:treats'}"
            ),
            make_path(
                categories="biolink:Disease --> biolink:SmallMolecule --> biolink:Gene --> biolink:AnatomicalEntity",
                first_hop_predicates="{'biolink:expressed_in'}"
            ),
        ]

        individual_filters = {
            "no_dupe_types": no_dupe_types,
            "no_expression": no_expression
        }

        expected_set = set()

        results = evaluate_multiple_strategies(paths, expected_set, individual_filters)

        # Should generate: none, no_dupe_types, no_expression, no_dupe_types+no_expression
        assert len(results) == 4

        filter_names = {r.filter_name for r in results}
        assert "none" in filter_names
        assert "no_dupe_types" in filter_names
        assert "no_expression" in filter_names
        assert "no_dupe_types+no_expression" in filter_names


class TestFormatMetricsTable:
    """Tests for formatting metrics."""

    def test_format_table(self):
        """Test formatting metrics as table."""
        metrics_list = [
            FilterMetrics(
                filter_name="strategy1",
                total_paths_before=100,
                total_paths_after=50,
                expected_paths_before=20,
                expected_paths_after=15,
                expected_nodes_found_before=5,
                expected_nodes_found_after=4
            ),
            FilterMetrics(
                filter_name="strategy2",
                total_paths_before=100,
                total_paths_after=25,
                expected_paths_before=20,
                expected_paths_after=18,
                expected_nodes_found_before=5,
                expected_nodes_found_after=5
            ),
        ]

        table = format_metrics_table(metrics_list)

        assert "strategy1" in table
        assert "strategy2" in table
        assert "Recall" in table
        assert "Precision" in table
        assert "Enrichment" in table

    def test_empty_metrics_list(self):
        """Test formatting empty list."""
        table = format_metrics_table([])
        assert "Strategy" in table  # Should have header
