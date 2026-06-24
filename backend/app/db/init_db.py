from app.db.session import Base, engine
from app.models.document import Document
from app.models.evidence import EvidenceNode
from app.models.graph import EvidenceEdge
from app.models.page import Page


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
