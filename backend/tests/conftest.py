from collections.abc import Generator

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.core.vector_store import vector_store
from app.db_rel.base import Base
from app.db_rel.session import get_db
from app.main import app


class FakeEmbeddingModel:
    KEYWORDS = [
        "split squat",
        "squat",
        "glute bridge",
        "glute",
        "pushup",
        "pushups",
        "row",
        "crunch",
        "plank",
        "hamstring stretch",
        "stretch",
        "dumbbell shoulder",
        "shoulder",
        "hamstring",
        "sprint",
        "jump",
        "hop",
        "bound",
        "groin",
        "calf",
        "side bridge",
    ]

    def encode(self, inputs, convert_to_numpy=False):
        if isinstance(inputs, str):
            values = [self._encode_one(inputs)]
        else:
            values = [self._encode_one(item) for item in inputs]

        matrix = np.asarray(values, dtype="float32")
        if convert_to_numpy:
            return matrix
        if isinstance(inputs, str):
            return matrix[0]
        return matrix

    def _encode_one(self, text):
        normalized = str(text).lower()
        vector = []
        for keyword in self.KEYWORDS:
            vector.append(float(keyword in normalized))
        return vector


@pytest.fixture()
def client(tmp_path, monkeypatch) -> Generator[TestClient, None, None]:
    database_path = tmp_path / "test_smoke.db"
    engine = create_engine(
        f"sqlite:///{database_path}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def fake_bootstrap_vector_store():
        vector_store.reset(dim=len(FakeEmbeddingModel.KEYWORDS))
        model = FakeEmbeddingModel()
        sample_exercises = [
            {
                "id": "ex-split-squat",
                "name": "Split Squat with Dumbbells",
                "primary_muscles": ["quadriceps"],
                "secondary_muscles": ["glutes", "hamstrings"],
                "equipment": "dumbbell",
                "instructions": ["Keep torso tall and control the descent."],
            },
            {
                "id": "ex-body-squat",
                "name": "Bodyweight Squat",
                "primary_muscles": ["quadriceps"],
                "secondary_muscles": ["glutes", "hamstrings"],
                "equipment": "body only",
                "instructions": ["Sit back and keep your chest up."],
            },
            {
                "id": "ex-glute-bridge",
                "name": "Single Leg Glute Bridge",
                "primary_muscles": ["glutes"],
                "secondary_muscles": ["hamstrings"],
                "equipment": "body only",
                "instructions": ["Drive through the heel."],
            },
            {
                "id": "ex-leg-lift",
                "name": "Leg Lift",
                "primary_muscles": ["glutes"],
                "secondary_muscles": ["hamstrings"],
                "equipment": "body only",
                "instructions": ["Move with control."],
            },
            {
                "id": "ex-pushups",
                "name": "Pushups",
                "primary_muscles": ["chest"],
                "secondary_muscles": ["shoulders", "triceps"],
                "equipment": "body only",
                "instructions": ["Keep a straight line from head to heel."],
            },
            {
                "id": "ex-row",
                "name": "Inverted Row",
                "primary_muscles": ["middle back"],
                "secondary_muscles": ["biceps", "lats"],
                "equipment": None,
                "instructions": ["Pull your chest to the bar."],
            },
            {
                "id": "ex-shoulder-press",
                "name": "Dumbbell Shoulder Press",
                "primary_muscles": ["shoulders"],
                "secondary_muscles": ["triceps"],
                "equipment": "dumbbell",
                "instructions": ["Press with control."],
            },
            {
                "id": "ex-single-raise",
                "name": "Single Dumbbell Raise",
                "primary_muscles": ["shoulders"],
                "secondary_muscles": ["traps"],
                "equipment": "dumbbell",
                "instructions": ["Avoid shrugging the shoulders."],
            },
            {
                "id": "ex-reverse-crunch",
                "name": "Reverse Crunch",
                "primary_muscles": ["abdominals"],
                "secondary_muscles": [],
                "equipment": "body only",
                "instructions": ["Posteriorly tilt the pelvis."],
            },
            {
                "id": "ex-plank",
                "name": "Plank",
                "primary_muscles": ["abdominals"],
                "secondary_muscles": [],
                "equipment": "body only",
                "instructions": ["Brace your core."],
            },
            {
                "id": "ex-hamstring-stretch",
                "name": "Hamstring Stretch",
                "primary_muscles": ["hamstrings"],
                "secondary_muscles": ["calves"],
                "equipment": None,
                "instructions": ["Breathe and relax into the stretch."],
            },
            {
                "id": "ex-sprint-drill",
                "name": "Single-Cone Sprint Drill",
                "primary_muscles": ["quadriceps"],
                "secondary_muscles": ["hamstrings", "calves"],
                "equipment": "body only",
                "instructions": ["Stay tall and punch the ground quickly."],
            },
            {
                "id": "ex-wind-sprints",
                "name": "Wind Sprints",
                "primary_muscles": ["quadriceps"],
                "secondary_muscles": ["hamstrings", "calves"],
                "equipment": "body only",
                "instructions": ["Run each effort with clean mechanics."],
            },
            {
                "id": "ex-jump-squat",
                "name": "Freehand Jump Squat",
                "primary_muscles": ["quadriceps"],
                "secondary_muscles": ["glutes", "calves"],
                "equipment": "body only",
                "instructions": ["Land softly and reset posture every rep."],
            },
            {
                "id": "ex-hurdle-hops",
                "name": "Hurdle Hops",
                "primary_muscles": ["quadriceps"],
                "secondary_muscles": ["calves", "glutes"],
                "equipment": "body only",
                "instructions": ["Keep contacts short and springy."],
            },
            {
                "id": "ex-standing-long-jump",
                "name": "Standing Long Jump",
                "primary_muscles": ["quadriceps"],
                "secondary_muscles": ["glutes", "hamstrings"],
                "equipment": "body only",
                "instructions": ["Project forward and stick the landing."],
            },
            {
                "id": "ex-groin-stretch",
                "name": "Side Lying Groin Stretch",
                "primary_muscles": ["adductors"],
                "secondary_muscles": ["hamstrings"],
                "equipment": None,
                "instructions": ["Control the range and avoid pinching."],
            },
            {
                "id": "ex-calf-raise",
                "name": "Standing Dumbbell Calf Raise",
                "primary_muscles": ["calves"],
                "secondary_muscles": ["hamstrings"],
                "equipment": "dumbbell",
                "instructions": ["Pause at the top and lower slowly."],
            },
            {
                "id": "ex-side-bridge",
                "name": "Side Bridge",
                "primary_muscles": ["abdominals"],
                "secondary_muscles": ["obliques"],
                "equipment": "body only",
                "instructions": ["Keep the body in one straight line."],
            },
        ]
        texts = [
            " ".join(
                [
                    exercise["name"],
                    " ".join(exercise.get("primary_muscles", [])),
                    " ".join(exercise.get("secondary_muscles", [])),
                    exercise.get("equipment") or "",
                ]
            )
            for exercise in sample_exercises
        ]
        embeddings = model.encode(texts, convert_to_numpy=True)
        vector_store.add_many(embeddings, sample_exercises)
        return {"ready": True, "count": vector_store.count, "source": "test"}

    monkeypatch.setattr("app.main.bootstrap_vector_store", fake_bootstrap_vector_store)
    monkeypatch.setattr("app.core.exercise_index.get_embedding_model", lambda: FakeEmbeddingModel())
    monkeypatch.setattr("app.api.routes.exercises.get_embedding_model", lambda: FakeEmbeddingModel())
    monkeypatch.setattr("app.services.exercise_lookup.get_embedding_model", lambda: FakeEmbeddingModel())

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    vector_store.reset()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
