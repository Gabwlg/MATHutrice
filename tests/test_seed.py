import uuid

from sqlmodel import Session, SQLModel, create_engine, select

from mathutrice import models
from mathutrice.referentiel import REFERENTIEL
from mathutrice.fonctions_python.seed import (
    NOTIONS,
    USERS,
    seed_competences,
    seed_database,
    seed_notions,
    seed_users,
)


def _empty_session() -> Session:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def _seeded_session() -> Session:
    session = _empty_session()
    seed_notions(session)
    return session


def _fully_seeded_session() -> Session:
    session = _empty_session()
    seed_database(session)
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


def test_seed_competences_creates_one_row_per_referentiel_entry():
    session = _seeded_session()

    seed_competences(session)

    competences = session.exec(select(models.Competence)).all()
    expected_count = sum(
        len(notion_data["competences"]) for notion_data in REFERENTIEL.values()
    )
    assert len(competences) == expected_count


def test_seed_competences_links_each_competence_to_its_notion():
    session = _seeded_session()

    seed_competences(session)

    notion = session.exec(
        select(models.Notion).where(
            models.Notion.referentiel_key == "trigonometrie"
        )
    ).first()

    competence = session.exec(
        select(models.Competence).where(
            models.Competence.referentiel_code == "tr01"
        )
    ).first()

    assert competence is not None
    assert competence.notion_id == notion.notion_id


def test_seed_competences_skips_notions_that_are_not_seeded_yet():
    session = _empty_session()

    seed_competences(session)

    competences = session.exec(select(models.Competence)).all()
    assert competences == []


def test_seed_competences_does_not_duplicate_rows_when_run_twice():
    session = _seeded_session()

    seed_competences(session)
    seed_competences(session)

    competences = session.exec(select(models.Competence)).all()
    expected_count = sum(
        len(notion_data["competences"]) for notion_data in REFERENTIEL.values()
    )
    assert len(competences) == expected_count


def test_seed_users_creates_one_user_per_role():
    session = _empty_session()

    seed_users(session)

    users = session.exec(select(models.User)).all()
    assert len(users) == len(USERS)
    assert {user.role for user in users} == {"Student", "Teacher", "Admin"}


def test_seed_users_respects_the_allowed_email_domains_per_role():
    session = _empty_session()

    seed_users(session)

    users_by_role = {
        user.role: user for user in session.exec(select(models.User)).all()
    }

    assert users_by_role["Student"].email.endswith("@epfedu.fr")
    assert users_by_role["Teacher"].email.endswith("@epf.fr")
    assert users_by_role["Admin"].email.endswith("@epf.fr")


def test_seed_users_does_not_duplicate_rows_when_run_twice():
    session = _empty_session()

    seed_users(session)
    seed_users(session)

    users = session.exec(select(models.User)).all()
    assert len(users) == len(USERS)


def test_seed_database_populates_notions_competences_and_users():
    session = _fully_seeded_session()

    assert len(session.exec(select(models.Notion)).all()) == len(NOTIONS)
    assert len(session.exec(select(models.Competence)).all()) == sum(
        len(notion_data["competences"]) for notion_data in REFERENTIEL.values()
    )
    assert len(session.exec(select(models.User)).all()) == len(USERS)


def test_seed_database_does_nothing_when_data_already_exists():
    session = _fully_seeded_session()

    seed_database(session)

    assert len(session.exec(select(models.Notion)).all()) == len(NOTIONS)
    assert len(session.exec(select(models.Competence)).all()) == sum(
        len(notion_data["competences"]) for notion_data in REFERENTIEL.values()
    )
    assert len(session.exec(select(models.User)).all()) == len(USERS)
