import pytest

from app.services import pipeline


class _FakeSession:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def add(self, _obj):
        pass

    def commit(self):
        pass


class _FakeAsyncResult:
    id = "task-abc"


def test_duplicate_trigger_raises(monkeypatch):
    # Lock indisponível -> não prossegue.
    monkeypatch.setattr(pipeline, "acquire_trigger_lock", lambda *a, **k: False)
    with pytest.raises(pipeline.DuplicateTrigger):
        pipeline.start_pipeline("ws", "ds", source="manual")


def test_start_pipeline_success(monkeypatch):
    monkeypatch.setattr(pipeline, "acquire_trigger_lock", lambda *a, **k: True)
    monkeypatch.setattr(pipeline, "SessionLocal", lambda: _FakeSession())
    monkeypatch.setattr(
        pipeline.refresh_dataset_task, "delay", lambda *a, **k: _FakeAsyncResult()
    )
    correlation_id, task_id = pipeline.start_pipeline("ws", "ds", source="manual")
    assert task_id == "task-abc"
    assert len(correlation_id) == 32  # uuid4().hex
