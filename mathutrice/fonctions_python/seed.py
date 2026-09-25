import uuid
from datetime import datetime, UTC

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, select

from mathutrice import models
from mathutrice.referentiel import REFERENTIEL

# `referentiel_key` is the stable slug the rest of the app looks notions up
# by (see session_generator.get_notion_by_referentiel_key and its callers in
# app.py). `notion_id` is a surrogate UUID primary key, generated here and
# never derived from the slug.
NOTIONS = [
    (
        "trigonometrie",
        "Trigonométrie",
        "Étude des fonctions trigonométriques, des angles et du cercle trigonométrique.",
    ),
    (
        "fractions_puissances_radicaux",
        "Fractions – Puissances – Radicaux",
        "Manipulation des fractions, puissances et radicaux.",
    ),
    (
        "logarithme_exponentielle",
        "Logarithme et exponentielle",
        "Étude des fonctions logarithme et exponentielle.",
    ),
    (
        "manipulation_expressions_litterales",
        "Manipulation d'expressions littérales",
        "Isolement et manipulation de variables dans des expressions algébriques.",
    ),
    (
        "equations_inequations",
        "Équations – Inéquations",
        "Résolution d'équations et d'inéquations du premier et second degré.",
    ),
    (
        "polynomes_factorisation",
        "Polynômes – Factorisation",
        "Étude des polynômes, factorisation et identités remarquables.",
    ),
    (
        "analyse_dimensionnelle",
        "Analyse dimensionnelle",
        "Dimensions, unités et homogénéité des formules physiques.",
    ),
]

# One demo account per role, so a fresh clone has someone to sign in as on
# `/dev/login` (AUTH_MODE=dev) without hand-editing the database. Domains
# match is_allowed_email() in app.py: students at @epfedu.fr, staff at @epf.fr.
USERS = [
    ("etudiant.demo@epfedu.fr", "Étudiant Démo", "Student"),
    ("professeur.demo@epf.fr", "Professeur Démo", "Teacher"),
    ("admin.demo@epf.fr", "Admin Démo", "Admin"),
]


def _commit_tolerating_concurrent_seed(session: Session) -> None:
    """
    Commits pending inserts, tolerating a unique-constraint violation raised
    by another process seeding the same rows concurrently at startup (e.g.
    two workers booting against the same empty database). That just means
    the data is already there by the time this commit lands, so roll back
    and move on instead of crashing this process's startup.
    """
    try:
        session.commit()
    except IntegrityError:
        session.rollback()


def seed_notions(session: Session) -> None:
    existing_keys = set(session.exec(select(models.Notion.referentiel_key)).all())

    for referentiel_key, title, description in NOTIONS:
        if referentiel_key in existing_keys:
            continue
        session.add(
            models.Notion(
                notion_id=uuid.uuid4(),
                referentiel_key=referentiel_key,
                title=title,
                description=description,
            )
        )

    _commit_tolerating_concurrent_seed(session)


def seed_competences(session: Session) -> None:
    """
    Insère une ligne Competence par entrée du REFERENTIEL, rattachée à sa
    Notion via notion_id. Sans ces lignes, tout le code qui résout un code
    métier ("tr01") en compétence BDD (session_generator.py) ne trouve
    jamais rien : positionnement, entraînement et progressions restent
    vides silencieusement.

    Suppose que seed_notions() a déjà tourné ; une notion introuvable est
    simplement sautée plutôt que de planter le démarrage.
    """
    notion_by_key = {
        notion.referentiel_key: notion
        for notion in session.exec(select(models.Notion)).all()
    }
    existing_codes = set(
        session.exec(select(models.Competence.referentiel_code)).all()
    )

    for referentiel_key, notion_data in REFERENTIEL.items():
        notion = notion_by_key.get(referentiel_key)
        if not notion:
            continue

        for competence in notion_data["competences"]:
            if competence["code"] in existing_codes:
                continue
            session.add(
                models.Competence(
                    competence_id=uuid.uuid4(),
                    referentiel_code=competence["code"],
                    title=competence["nom"],
                    level=competence["niveau"],
                    notion_id=notion.notion_id,
                )
            )

    _commit_tolerating_concurrent_seed(session)


def seed_users(session: Session) -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    existing_emails = set(session.exec(select(models.User.email)).all())

    for email, name, role in USERS:
        if email in existing_emails:
            continue
        session.add(
            models.User(
                sso_id=uuid.uuid4(),
                email=email,
                name=name,
                role=role,
                created_at=now,
            )
        )

    _commit_tolerating_concurrent_seed(session)


def seed_database(session: Session) -> None:
    """
    Seeds reference data (notions, competences) and one demo user per role.
    Each seed step checks for its own rows before inserting, so this is
    a no-op on a database that already has data, and safe to call on
    every startup.

    The demo users are only appropriate for AUTH_MODE=dev (see app.py,
    which calls seed_notions/seed_competences/seed_users directly rather
    than this function, so it can skip seed_users in production); this
    function seeds all three and is meant for local/manual use
    (`python -m mathutrice.fonctions_python.seed`).
    """
    seed_notions(session)
    seed_competences(session)
    seed_users(session)


if __name__ == "__main__":
    from mathutrice.database import engine

    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_database(session)
    print("Base de données initialisée.")
