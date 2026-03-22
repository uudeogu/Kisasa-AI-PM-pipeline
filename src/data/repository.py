from __future__ import annotations

"""Data access layer for pipeline persistence."""

import uuid
import json
from typing import Optional
from .models import (
    Project, ProjectBriefRecord, FeasibilityReportRecord,
    RoadmapRecord, ProjectEmbedding, RetroRecord, get_session,
)


class ProjectRepository:
    """CRUD operations for pipeline data."""

    def __init__(self, session=None):
        self.session = session or get_session()

    def create_project(self, title: str, client: str, division: str) -> Project:
        project = Project(
            id=str(uuid.uuid4()),
            title=title,
            client=client,
            division=division,
        )
        self.session.add(project)
        self.session.commit()
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        return self.session.query(Project).filter_by(id=project_id).first()

    def list_projects(self, status: Optional[str] = None) -> list[Project]:
        query = self.session.query(Project)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Project.created_at.desc()).all()

    def update_project_status(self, project_id: str, status: str) -> Project:
        project = self.get_project(project_id)
        if project:
            project.status = status
            self.session.commit()
        return project

    def save_brief(
        self, project_id: str, raw_input: str, input_source: str,
        brief_data: dict, confidence_score: float,
    ) -> ProjectBriefRecord:
        record = ProjectBriefRecord(
            id=str(uuid.uuid4()),
            project_id=project_id,
            raw_input=raw_input,
            input_source=input_source,
            brief_data=brief_data,
            confidence_score=confidence_score,
        )
        self.session.add(record)
        self.session.commit()
        return record

    def save_feasibility_report(
        self, project_id: str, report_data: dict, recommendation: str,
    ) -> FeasibilityReportRecord:
        record = FeasibilityReportRecord(
            id=str(uuid.uuid4()),
            project_id=project_id,
            report_data=report_data,
            recommendation=recommendation,
        )
        self.session.add(record)
        self.session.commit()
        return record

    def save_roadmap(
        self, project_id: str, roadmap_data: dict,
        milestone_count: int, story_count: int,
    ) -> RoadmapRecord:
        record = RoadmapRecord(
            id=str(uuid.uuid4()),
            project_id=project_id,
            roadmap_data=roadmap_data,
            milestone_count=milestone_count,
            story_count=story_count,
        )
        self.session.add(record)
        self.session.commit()
        return record

    def save_retro(
        self, project_id: str, retro_data: dict,
        average_accuracy_pct: float, estimation_rules: list[str],
    ) -> RetroRecord:
        record = RetroRecord(
            id=str(uuid.uuid4()),
            project_id=project_id,
            retro_data=retro_data,
            average_accuracy_pct=average_accuracy_pct,
            estimation_rules=estimation_rules,
        )
        self.session.add(record)
        self.session.commit()
        return record


class EmbeddingRepository:
    """Operations for vector embeddings (RAG over project history)."""

    def __init__(self, session=None):
        self.session = session or get_session()

    def store_embedding(
        self, project_id: str, content_type: str,
        content_text: str, embedding: list[float],
    ) -> ProjectEmbedding:
        record = ProjectEmbedding(
            id=str(uuid.uuid4()),
            project_id=project_id,
            content_type=content_type,
            content_text=content_text,
            embedding=embedding,
        )
        self.session.add(record)
        self.session.commit()
        return record

    def search_similar(
        self, query_embedding: list[float], limit: int = 5,
    ) -> list[ProjectEmbedding]:
        """Search for similar embeddings using cosine similarity.

        Note: For production, use pgvector extension or a dedicated vector DB.
        This implementation loads embeddings into memory for comparison.
        """
        all_embeddings = self.session.query(ProjectEmbedding).all()
        if not all_embeddings:
            return []

        scored = []
        for record in all_embeddings:
            if record.embedding:
                similarity = self._cosine_similarity(query_embedding, record.embedding)
                scored.append((similarity, record))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [record for _, record in scored[:limit]]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
