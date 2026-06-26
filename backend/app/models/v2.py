from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class OcrRun(Base):
    __tablename__ = "ocr_runs"
    __table_args__ = (UniqueConstraint("document_id", "page_id", name="uq_ocr_run_document_page"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")
    adapter: Mapped[str] = mapped_column(String(64), nullable=False, default="mock")
    text_block_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class CollectionDocument(Base):
    __tablename__ = "collection_documents"
    __table_args__ = (
        UniqueConstraint("collection_id", "document_id", name="uq_collection_document"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    collection_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    added_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
