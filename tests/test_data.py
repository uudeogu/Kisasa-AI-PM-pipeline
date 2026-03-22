"""Tests for data persistence layer."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data.models import Base, Project, ProjectBriefRecord, init_db
from src.data.repository import ProjectRepository, EmbeddingRepository


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestProjectRepository:
    def test_create_project(self, db_session):
        repo = ProjectRepository(session=db_session)
        project = repo.create_project("Test Project", "Acme Corp", "labs")

        assert project.id is not None
        assert project.title == "Test Project"
        assert project.client == "Acme Corp"
        assert project.division == "labs"
        assert project.status == "intake"

    def test_get_project(self, db_session):
        repo = ProjectRepository(session=db_session)
        created = repo.create_project("Test", "Client", "ventures")

        found = repo.get_project(created.id)
        assert found is not None
        assert found.title == "Test"

    def test_get_project_not_found(self, db_session):
        repo = ProjectRepository(session=db_session)
        assert repo.get_project("nonexistent") is None

    def test_list_projects(self, db_session):
        repo = ProjectRepository(session=db_session)
        repo.create_project("Project 1", "Client A", "labs")
        repo.create_project("Project 2", "Client B", "ventures")

        projects = repo.list_projects()
        assert len(projects) == 2

    def test_list_projects_by_status(self, db_session):
        repo = ProjectRepository(session=db_session)
        p1 = repo.create_project("Project 1", "Client A", "labs")
        repo.create_project("Project 2", "Client B", "ventures")
        repo.update_project_status(p1.id, "build")

        intake_projects = repo.list_projects(status="intake")
        assert len(intake_projects) == 1

        build_projects = repo.list_projects(status="build")
        assert len(build_projects) == 1

    def test_update_project_status(self, db_session):
        repo = ProjectRepository(session=db_session)
        project = repo.create_project("Test", "Client", "labs")

        updated = repo.update_project_status(project.id, "research")
        assert updated.status == "research"

    def test_save_brief(self, db_session):
        repo = ProjectRepository(session=db_session)
        project = repo.create_project("Test", "Client", "labs")

        brief = repo.save_brief(
            project_id=project.id,
            raw_input="Client email content",
            input_source="gmail",
            brief_data={"title": "Test", "goals": ["Goal 1"]},
            confidence_score=0.85,
        )

        assert brief.id is not None
        assert brief.input_source == "gmail"
        assert brief.confidence_score == 0.85
        assert brief.brief_data["goals"] == ["Goal 1"]

    def test_save_feasibility_report(self, db_session):
        repo = ProjectRepository(session=db_session)
        project = repo.create_project("Test", "Client", "labs")

        report = repo.save_feasibility_report(
            project_id=project.id,
            report_data={"recommendation": "go", "complexity": "high"},
            recommendation="go",
        )

        assert report.recommendation == "go"

    def test_save_roadmap(self, db_session):
        repo = ProjectRepository(session=db_session)
        project = repo.create_project("Test", "Client", "labs")

        roadmap = repo.save_roadmap(
            project_id=project.id,
            roadmap_data={"milestones": []},
            milestone_count=3,
            story_count=12,
        )

        assert roadmap.milestone_count == 3
        assert roadmap.story_count == 12

    def test_save_retro(self, db_session):
        repo = ProjectRepository(session=db_session)
        project = repo.create_project("Test", "Client", "labs")

        retro = repo.save_retro(
            project_id=project.id,
            retro_data={"what_went_well": ["Good collab"]},
            average_accuracy_pct=112.5,
            estimation_rules=["Add 20% buffer for infra"],
        )

        assert retro.average_accuracy_pct == 112.5
        assert len(retro.estimation_rules) == 1


class TestEmbeddingRepository:
    def test_store_embedding(self, db_session):
        project_repo = ProjectRepository(session=db_session)
        project = project_repo.create_project("Test", "Client", "labs")

        embed_repo = EmbeddingRepository(session=db_session)
        record = embed_repo.store_embedding(
            project_id=project.id,
            content_type="brief",
            content_text="Project about modernization",
            embedding=[0.1, 0.2, 0.3, 0.4],
        )

        assert record.id is not None
        assert record.content_type == "brief"
        assert len(record.embedding) == 4

    def test_cosine_similarity(self):
        sim = EmbeddingRepository._cosine_similarity(
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        )
        assert sim == pytest.approx(1.0)

    def test_cosine_similarity_orthogonal(self):
        sim = EmbeddingRepository._cosine_similarity(
            [1.0, 0.0],
            [0.0, 1.0],
        )
        assert sim == pytest.approx(0.0)

    def test_cosine_similarity_different_lengths(self):
        sim = EmbeddingRepository._cosine_similarity(
            [1.0, 0.0],
            [1.0, 0.0, 0.0],
        )
        assert sim == 0.0

    def test_search_similar(self, db_session):
        project_repo = ProjectRepository(session=db_session)
        project = project_repo.create_project("Test", "Client", "labs")

        embed_repo = EmbeddingRepository(session=db_session)
        embed_repo.store_embedding(project.id, "brief", "Modernization project", [1.0, 0.0, 0.0])
        embed_repo.store_embedding(project.id, "brief", "New product build", [0.0, 1.0, 0.0])
        embed_repo.store_embedding(project.id, "brief", "Similar to modernization", [0.9, 0.1, 0.0])

        results = embed_repo.search_similar([1.0, 0.0, 0.0], limit=2)
        assert len(results) == 2
        assert results[0].content_text == "Modernization project"
        assert results[1].content_text == "Similar to modernization"

    def test_search_similar_empty(self, db_session):
        embed_repo = EmbeddingRepository(session=db_session)
        results = embed_repo.search_similar([1.0, 0.0], limit=5)
        assert results == []
