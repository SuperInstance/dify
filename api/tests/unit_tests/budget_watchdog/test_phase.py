"""Tests for phase detection logic."""

import pytest

from controllers.service_api.budget_watchdog.phase import (
    BudgetPhase,
    Thresholds,
    detect_phase,
    DEFAULT_THRESHOLDS,
)


class TestDetectPhase:
    def test_normal_below_60(self):
        phase = detect_phase(300, 1000)
        assert phase == BudgetPhase.NORMAL

    def test_pretransition_at_60(self):
        phase = detect_phase(600, 1000)
        assert phase == BudgetPhase.PRE_TRANSITION

    def test_pretransition_mid(self):
        phase = detect_phase(750, 1000)
        assert phase == BudgetPhase.PRE_TRANSITION

    def test_transitioning_at_85(self):
        phase = detect_phase(850, 1000)
        assert phase == BudgetPhase.TRANSITIONING

    def test_transitioning_above(self):
        phase = detect_phase(999, 1000)
        assert phase == BudgetPhase.TRANSITIONING

    def test_limit_zero_is_post(self):
        phase = detect_phase(0, 0)
        assert phase == BudgetPhase.POST_TRANSITION

    def test_custom_thresholds(self):
        thresholds = Thresholds(pre_transition=0.50, transitioning=0.75)
        assert detect_phase(400, 1000, thresholds) == BudgetPhase.NORMAL
        assert detect_phase(600, 1000, thresholds) == BudgetPhase.PRE_TRANSITION
        assert detect_phase(800, 1000, thresholds) == BudgetPhase.TRANSITIONING

    def test_exact_boundaries(self):
        # At exactly 60% / 85%
        assert detect_phase(600, 1000) == BudgetPhase.PRE_TRANSITION
        assert detect_phase(850, 1000) == BudgetPhase.TRANSITIONING

    def test_zero_consumed(self):
        assert detect_phase(0, 1000) == BudgetPhase.NORMAL


class TestBudgetPhase:
    def test_is_restricted(self):
        assert not BudgetPhase.NORMAL.is_restricted()
        assert not BudgetPhase.PRE_TRANSITION.is_restricted()
        assert BudgetPhase.TRANSITIONING.is_restricted()
        assert BudgetPhase.POST_TRANSITION.is_restricted()

    def test_descriptions(self):
        assert "Normal" in BudgetPhase.NORMAL.description()
        assert "Pre-transition" in BudgetPhase.PRE_TRANSITION.description()
        assert "auto-downgraded" in BudgetPhase.TRANSITIONING.description()

    def test_sort_key_order(self):
        assert BudgetPhase.NORMAL.sort_key() < BudgetPhase.PRE_TRANSITION.sort_key()
        assert BudgetPhase.PRE_TRANSITION.sort_key() < BudgetPhase.TRANSITIONING.sort_key()
        assert BudgetPhase.TRANSITIONING.sort_key() < BudgetPhase.POST_TRANSITION.sort_key()
