"""Tests for alert records and stores."""

from controllers.service_api.budget_watchdog.alert import AlertLevel, AlertRecord, AlertStore


class TestAlertStore:
    def test_push_and_retrieve(self):
        store = AlertStore(10)
        alert = AlertRecord("wf1", AlertLevel.WARNING, "budget at 70%")
        store.push(alert)
        assert len(store) == 1

    def test_max_records(self):
        store = AlertStore(3)
        for i in range(5):
            store.push(AlertRecord(f"wf{i}", AlertLevel.INFO, f"alert {i}"))

        assert len(store) == 3
        all_alerts = store.all()
        # Most recent should be wf4
        assert all_alerts[-1].workflow == "wf4"

    def test_filter_by_level(self):
        store = AlertStore(10)
        store.push(AlertRecord("wf1", AlertLevel.INFO, "info"))
        store.push(AlertRecord("wf2", AlertLevel.WARNING, "warn"))
        store.push(AlertRecord("wf3", AlertLevel.CRITICAL, "crit"))

        crits = store.filter_by_level(AlertLevel.CRITICAL)
        assert len(crits) == 1
        assert crits[0].workflow == "wf3"

        warns_and_up = store.filter_by_level(AlertLevel.WARNING)
        assert len(warns_and_up) == 2

    def test_json_roundtrip(self):
        store = AlertStore(5)
        store.push(AlertRecord("wf1", AlertLevel.WARNING, "test msg"))

        json_data = store.to_json()
        restored = AlertStore.from_json(json_data)

        assert len(restored) == 1
        all_restored = restored.all()
        assert all_restored[0].workflow == "wf1"
        assert all_restored[0].level == AlertLevel.WARNING

    def test_clear(self):
        store = AlertStore(10)
        store.push(AlertRecord("wf1", AlertLevel.INFO, "msg"))
        assert not store.is_empty()
        store.clear()
        assert store.is_empty()

    def test_level_ordering(self):
        assert AlertLevel.INFO < AlertLevel.WARNING
        assert AlertLevel.WARNING < AlertLevel.CRITICAL
