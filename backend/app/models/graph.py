from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class EvidenceEdge(Base):
    __tablename__ = "evidence_edges"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "source_node_id",
            "target_node_id",
            "edge_type",
            "source",
            name="uq_evidence_edge_identity",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_node_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("evidence_nodes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    target_node_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("evidence_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    edge_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="manual")
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    source_node = relationship(
        "EvidenceNode",
        foreign_keys=[source_node_id],
    )
    target_node = relationship(
        "EvidenceNode",
        foreign_keys=[target_node_id],
    )
