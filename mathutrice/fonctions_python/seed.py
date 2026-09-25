import uuid

from sqlmodel import Session, SQLModel, select

from mathutrice import models

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


def seed_notions(session: Session) -> None:
    for referentiel_key, title, description in NOTIONS:
        existing = session.exec(
            select(models.Notion).where(
                models.Notion.referentiel_key == referentiel_key
            )
        ).first()
        if existing:
            continue
        session.add(
            models.Notion(
                notion_id=uuid.uuid4(),
                referentiel_key=referentiel_key,
                title=title,
                description=description,
            )
        )
    session.commit()


if __name__ == "__main__":
    from mathutrice.database import engine

    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_notions(session)
    print("Notions insérées.")
