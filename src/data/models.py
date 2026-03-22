from __future__ import annotations

"""SQLAlchemy models for pipeline data persistence."""

from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Text, JSON, Enum as SAEnum,
    ForeignKey, create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from ..utils.config import Config

Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    client = Column(String, nullable=False)
    division = Column(SAEnum("ventures", "labs", "strategy", name="division_enum"), nullable=False)
    status = Column(String, default="intake")  # intake, research, roadmap, build, qa, launch, retro, complete
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    brief = relationship("ProjectBriefRecord", back_populates="project", uselist=False)
    feasibility_report = relationship("FeasibilityReportRecord", back_populates="project", uselist=False)
    roadmap = relationship("RoadmapRecord", back_populates="project", uselist=False)
    embeddings = relationship("ProjectEmbedding", back_populates="project")


class ProjectBriefRecord(Base):
    __tablename__ = "project_briefs"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    raw_input = Column(Text)
    input_source = Column(String)  # slack, gmail, zoom, raw
    brief_data = Column(JSON, nullable=False)
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="brief")


class FeasibilityReportRecord(Base):
    __tablename__ = "feasibility_reports"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    report_data = Column(JSON, nullable=False)
    recommendation = Column(String)  # go, conditional_go, no_go
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="feasibility_report")


class RoadmapRecord(Base):
    __tablename__ = "roadmaps"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    roadmap_data = Column(JSON, nullable=False)
    milestone_count = Column(Integer)
    story_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="roadmap")


class ProjectEmbedding(Base):
    """Stores vector embeddings for RAG over project history."""
    __tablename__ = "project_embeddings"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    content_type = Column(String)  # brief, report, roadmap, retro
    content_text = Column(Text, nullable=False)
    embedding = Column(JSON)  # stored as list of floats
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="embeddings")


class RetroRecord(Base):
    __tablename__ = "retro_reports"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    retro_data = Column(JSON, nullable=False)
    average_accuracy_pct = Column(Float)
    estimation_rules = Column(JSON)  # list of updated rules
    created_at = Column(DateTime, default=datetime.utcnow)


def get_engine():
    return create_engine(Config.DATABASE_URL or "sqlite:///kisasa_pipeline.db")


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)
