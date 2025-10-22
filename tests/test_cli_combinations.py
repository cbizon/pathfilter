"""Tests for CLI filter combination logic."""
import pytest
from pathfilter.cli import generate_all_filter_combinations


def dummy_filter_a(path):
    """Dummy path-based filter A."""
    return True


def dummy_filter_b(path):
    """Dummy path-based filter B."""
    return True


def dummy_filter_c(path):
    """Dummy path-based filter C."""
    return True


def dummy_ic_30(path):
    """Dummy IC filter 30."""
    return True


def dummy_ic_50(path):
    """Dummy IC filter 50."""
    return True


class TestFilterCombinations:
    """Tests for generate_all_filter_combinations with IC filters."""

    def test_no_ic_filters_combined_together(self):
        """IC filters should never be combined with each other."""
        filters = {
            "filter_a": dummy_filter_a,
            "filter_b": dummy_filter_b,
            "min_ic_30": dummy_ic_30,
            "min_ic_50": dummy_ic_50,
        }

        strategies = generate_all_filter_combinations(filters)

        # Check that no strategy contains multiple IC filters
        for strategy_name, filter_list in strategies.items():
            ic_count = sum(1 for f in filter_list if f.__name__.startswith("dummy_ic"))
            assert ic_count <= 1, f"Strategy '{strategy_name}' has {ic_count} IC filters (should be 0 or 1)"

    def test_ic_filters_combined_with_path_filters(self):
        """IC filters should be combined with path filters."""
        filters = {
            "filter_a": dummy_filter_a,
            "filter_b": dummy_filter_b,
            "min_ic_30": dummy_ic_30,
        }

        strategies = generate_all_filter_combinations(filters)

        # Should have combinations like "filter_a+min_ic_30"
        assert "filter_a+min_ic_30" in strategies
        assert "filter_b+min_ic_30" in strategies
        assert "filter_a+filter_b+min_ic_30" in strategies

    def test_correct_combination_count(self):
        """Test that the number of combinations is correct.

        Formula with P path filters and I IC filters:
        - Baseline: 1
        - Individual filters: P + I
        - Path-only combinations (2+): 2^P - P - 1
        - Path combinations (all sizes) with each IC: (2^P - 1) * I

        Total = 1 + P + I + (2^P - P - 1) + (2^P - 1) * I
              = 2^P + I + (2^P - 1) * I
              = 2^P * (1 + I)
        """
        filters = {
            "filter_a": dummy_filter_a,
            "filter_b": dummy_filter_b,
            "filter_c": dummy_filter_c,
            "min_ic_30": dummy_ic_30,
            "min_ic_50": dummy_ic_50,
        }

        strategies = generate_all_filter_combinations(filters)

        # P=3, I=2
        # Expected: 2^3 * (1 + 2) = 8 * 3 = 24
        assert len(strategies) == 24

    def test_no_redundant_ic_combinations(self):
        """Ensure no combinations like 'min_ic_30+min_ic_50'."""
        filters = {
            "filter_a": dummy_filter_a,
            "min_ic_30": dummy_ic_30,
            "min_ic_50": dummy_ic_50,
        }

        strategies = generate_all_filter_combinations(filters)

        # Check strategy names don't contain multiple IC filters
        for strategy_name in strategies.keys():
            ic_count = strategy_name.count("min_ic_")
            assert ic_count <= 1, f"Strategy name '{strategy_name}' contains {ic_count} IC filters"

    def test_six_path_three_ic_filters(self):
        """Test with realistic 6 path + 3 IC filters (like actual CLI)."""
        filters = {
            "no_dupe_types": dummy_filter_a,
            "no_expression": dummy_filter_a,
            "no_related_to": dummy_filter_a,
            "no_end_pheno": dummy_filter_a,
            "no_repeat_predicates": dummy_filter_a,
            "no_abab": dummy_filter_a,
            "min_ic_30": dummy_ic_30,
            "min_ic_50": dummy_ic_50,
            "min_ic_70": dummy_ic_30,
        }

        strategies = generate_all_filter_combinations(filters)

        # P=6, I=3
        # Expected: 2^6 * (1 + 3) = 64 * 4 = 256
        assert len(strategies) == 256

    def test_individual_filters_included(self):
        """All individual filters should be included as strategies."""
        filters = {
            "filter_a": dummy_filter_a,
            "filter_b": dummy_filter_b,
            "min_ic_30": dummy_ic_30,
        }

        strategies = generate_all_filter_combinations(filters)

        # Check all individual filters are present
        assert "filter_a" in strategies
        assert "filter_b" in strategies
        assert "min_ic_30" in strategies

    def test_baseline_none_included(self):
        """Baseline 'none' strategy should always be included."""
        filters = {
            "filter_a": dummy_filter_a,
        }

        strategies = generate_all_filter_combinations(filters)

        assert "none" in strategies
        assert len(strategies["none"]) == 1  # Should contain all_paths filter

    def test_path_only_combinations(self):
        """Path filters should be combined without IC filters."""
        filters = {
            "filter_a": dummy_filter_a,
            "filter_b": dummy_filter_b,
            "filter_c": dummy_filter_c,
            "min_ic_30": dummy_ic_30,
        }

        strategies = generate_all_filter_combinations(filters)

        # Path-only combinations should exist
        assert "filter_a+filter_b" in strategies
        assert "filter_a+filter_c" in strategies
        assert "filter_b+filter_c" in strategies
        assert "filter_a+filter_b+filter_c" in strategies

        # Verify they don't contain IC filters
        for combo in ["filter_a+filter_b", "filter_a+filter_b+filter_c"]:
            filter_list = strategies[combo]
            assert all(not f.__name__.startswith("dummy_ic") for f in filter_list)
