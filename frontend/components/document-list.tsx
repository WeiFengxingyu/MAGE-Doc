import { parseTablesAction, parseTextBlocksAction, renderDocumentAction } from "@/app/actions";
import type { DocumentRecord } from "@/types/api";

function formatBytes(value: number): string {
  if (value < 1024) {
    return `${value} B`;
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function DocumentList({ documents }: { documents: DocumentRecord[] }) {
  if (documents.length === 0) {
    return (
      <div className="empty-list">
        <p>No documents yet.</p>
        <span>Upload a PDF to create the first document record.</span>
      </div>
    );
  }

  return (
    <div className="document-list">
      {documents.map((document) => (
        <article className="document-item" key={document.id}>
          <div>
            <h3>{document.filename}</h3>
            <p>
              {formatBytes(document.file_size)} ·{" "}
              {document.page_count === null ? "pages pending" : `${document.page_count} pages`}
            </p>
          </div>
          <div className="document-meta">
            <span className={`status-pill status-${document.status}`}>
              {document.status}
            </span>
            <time dateTime={document.created_at}>{formatDate(document.created_at)}</time>
            <form action={renderDocumentAction}>
              <input name="document_id" type="hidden" value={document.id} />
              <button className="mini-button" type="submit">
                Render pages
              </button>
            </form>
            <form action={parseTextBlocksAction}>
              <input name="document_id" type="hidden" value={document.id} />
              <button className="mini-button" type="submit">
                Parse text
              </button>
            </form>
            <form action={parseTablesAction}>
              <input name="document_id" type="hidden" value={document.id} />
              <button className="mini-button" type="submit">
                Parse tables
              </button>
            </form>
          </div>
        </article>
      ))}
    </div>
  );
}
