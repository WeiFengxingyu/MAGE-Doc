import { absoluteApiUrl } from "@/lib/api";
import type { DocumentRecord, EvidenceNode, PageRecord } from "@/types/api";

function overlayStyle(page: PageRecord, node: EvidenceNode) {
  const [x0, y0, x1, y1] = node.bbox;
  return {
    left: `${(x0 / page.width) * 100}%`,
    top: `${(y0 / page.height) * 100}%`,
    width: `${((x1 - x0) / page.width) * 100}%`,
    height: `${((y1 - y0) / page.height) * 100}%`,
  };
}

export function PageViewer({
  document,
  pages,
  textBlocks,
  tables,
}: {
  document: DocumentRecord | null;
  pages: PageRecord[];
  textBlocks: EvidenceNode[];
  tables: EvidenceNode[];
}) {
  if (!document) {
    return (
      <div className="page-viewer-empty">
        <p>No active document.</p>
        <span>Upload a PDF to create a document record.</span>
      </div>
    );
  }

  if (pages.length === 0) {
    return (
      <div className="page-viewer-empty">
        <p>{document.filename}</p>
        <span>Render this document to inspect page images and coordinate metadata.</span>
      </div>
    );
  }

  const page = pages[0];

  return (
    <div className="page-viewer">
      <div className="page-viewer-toolbar">
        <div>
          <p className="eyebrow">Page Viewer</p>
          <h3>
            {document.filename} · page {page.page_number} of {pages.length}
          </h3>
        </div>
        <div className="page-metrics">
          <span>
            PDF {Math.round(page.width)} x {Math.round(page.height)} pt
          </span>
          <span>
            PNG {page.image_width} x {page.image_height}px
          </span>
          <span>{textBlocks.length} text blocks</span>
          <span>{tables.length} tables</span>
        </div>
      </div>

      <div className="page-canvas">
        <img alt={`Page ${page.page_number}`} src={absoluteApiUrl(page.image_url)} />
        {textBlocks.map((node) => (
          <div
            className="text-bbox"
            key={node.id}
            style={overlayStyle(page, node)}
            title={`#${node.reading_order}: ${node.text}`}
          >
            <span>{node.reading_order}</span>
          </div>
        ))}
        {tables.map((table) => (
          <div
            className="table-bbox"
            key={table.id}
            style={overlayStyle(page, table)}
            title={`Table #${table.reading_order}: ${table.text}`}
          >
            <span>
              T{table.reading_order} · {String(table.metadata.row_count ?? "?")}x
              {String(table.metadata.col_count ?? "?")}
            </span>
          </div>
        ))}
      </div>
      <p className="page-note">
        Text and table boxes come from PyMuPDF evidence nodes and use the same PDF
        point coordinate system as the rendered page.
      </p>
    </div>
  );
}
