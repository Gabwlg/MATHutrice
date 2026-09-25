import uuid

from sqlmodel import Session, SQLModel, create_engine, select

from mathutrice import models
from mathutrice.fonctions_python.seed import NOTIONS, seed_notions


def _seeded_session() -> Session:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    seed_notions(session)
    return session


def test_seed_notions_assigns_a_uuid_primary_key_to_each_notion():
    session = _seeded_session()

    notions = session.exec(select(models.Notion)).all()

    assert len(notions) == len(NOTIONS)
    for notion in notions:
        assert isinstance(notion.notion_id, uuid.UUID)


def test_seed_notions_is_findable_by_its_referentiel_key():
    session = _seeded_session()

    notion = session.exec(
        select(models.Notion).where(
            models.Notion.referentiel_key == "trigonometrie"
        )
    ).first()

    assert notion is not None
    assert notion.title == "Trigonométrie"


def test_seed_notions_does_not_duplicate_rows_when_run_twice():
    session = _seeded_session()

    seed_notions(session)

    notions = session.exec(select(models.Notion)).all()
    assert len(notions) == len(NOTIONS)
