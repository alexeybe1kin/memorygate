import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.db import Base
from app.models.agent_access_key import AgentAccessKey
from app.services.auth_settings_service import (
    _hash_key,
    ensure_bootstrap_agent_access_key,
    verify_agent_access_key,
)

RAW = "mg_read_bootstrap_never_resurrect_1234"
NEW = "mg_read_replacement_owner_changed_5678"


@pytest.fixture
def database(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'memory.db'}")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def test_restart_preserves_revocation_and_scope(database):
    with Session(database) as db:
        row = ensure_bootstrap_agent_access_key(db, RAW, "original")
        identity, digest = row.id, row.key_hash
        row.revoked = True
        row.agent_id = "owner-changed-scope"
        db.commit()
    with Session(database) as db:
        seeded = ensure_bootstrap_agent_access_key(db, RAW, "broader-scope")
        assert (seeded.id, seeded.key_hash, seeded.agent_id, seeded.revoked) == (
            identity, digest, "owner-changed-scope", True,
        )
        assert not verify_agent_access_key(db, RAW, "broader-scope")
        assert not verify_agent_access_key(db, RAW, "owner-changed-scope")


def test_configuration_cannot_replace_owner_rotated_credential(database):
    with Session(database) as db:
        row = ensure_bootstrap_agent_access_key(db, RAW, "original")
        row.key_hash = _hash_key(NEW)
        row.agent_id = "owner-selected"
        db.commit()
    with Session(database) as db:
        seeded = ensure_bootstrap_agent_access_key(db, RAW, "original")
        assert seeded.agent_id == "owner-selected"
        assert not verify_agent_access_key(db, RAW, "original")
        assert verify_agent_access_key(db, NEW, "owner-selected")


def test_renaming_revoked_key_does_not_create_active_copy(database):
    with Session(database) as db:
        row = ensure_bootstrap_agent_access_key(db, RAW, "original")
        identity = row.id
        row.label = "Owner renamed it"
        row.revoked = True
        db.commit()
    with Session(database) as db:
        seeded = ensure_bootstrap_agent_access_key(db, RAW, "different-agent")
        assert seeded.id == identity and seeded.revoked
        assert db.query(AgentAccessKey).count() == 1
        assert not verify_agent_access_key(db, RAW, "different-agent")


def test_missing_key_is_seeded_once_without_rehashing(database):
    with Session(database) as db:
        row = ensure_bootstrap_agent_access_key(db, RAW, "original")
        identity, digest = row.id, row.key_hash
        assert verify_agent_access_key(db, RAW, "original")
    with Session(database) as db:
        row = ensure_bootstrap_agent_access_key(db, RAW, "original")
        assert (row.id, row.key_hash) == (identity, digest)
        assert db.query(AgentAccessKey).count() == 1
