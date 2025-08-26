from datetime import datetime, UTC, timedelta
from persistence import store_transcript, SessionLocal, transcripts
from retention import purge_once
from config import get_settings


def test_retention_purge(monkeypatch):
    settings = get_settings()
    settings.retention_days = 1
    # Clear existing rows to ensure deterministic count
    with SessionLocal() as session:
        session.execute(transcripts.delete())
        session.commit()
    # Insert two records: one old, one new
    with SessionLocal() as session:
        session.execute(transcripts.insert().values(
            filename="old.txt", text="x", summary=None, enrichment=None, source="test", fhir_document_id=None, created_at=datetime.now(UTC)-timedelta(days=2)
        ))
        session.execute(transcripts.insert().values(
            filename="new.txt", text="y", summary=None, enrichment=None, source="test", fhir_document_id=None, created_at=datetime.now(UTC)
        ))
        session.commit()
    deleted = purge_once()
    assert deleted == 1