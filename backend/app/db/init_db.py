from app.db.session import Base, engine
from app.models.document import Document
from app.models.evidence import EvidenceNode
from app.models.graph import EvidenceEdge
from app.models.page import Page
from app.models.trace import AgentToolCall, AgentTraceRun
from app.models.v2 import Collection, CollectionDocument, OcrRun


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
