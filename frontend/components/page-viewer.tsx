"use client";

import { useEffect, useMemo, useState } from "react";

import { absoluteApiUrl } from "@/lib/api";
import { listPageTables, listPageTextBlocks } from "@/lib/api";
import type { Citation, DocumentRecord, EvidenceNode, PageRecord } from "@/types/api";

function bboxStyle(page: PageRecord, bbox: [number, number, number, number]) {
  const [x0, y0, x1, y1] = bbox;
  return {
    left: `${(x0 / page.width) * 100}%`,
    top: `${(y0 / page.height) * 100}%`,
    width: `${((x1 - x0) / page.width) * 100}%`,
    height: `${((y1 - y0) / page.height) * 100}%`,
  };
}

function overlayStyle(page: PageRecord, node: EvidenceNode) {
  return bboxStyle(page, node.bbox);
}

export function PageViewer({
  document,
  pages,
  textBlocks,
  tables,
  selectedCitation,
}: {
  document: DocumentRecord | null;
  pages: PageRecord[];
  textBlocks: EvidenceNode[];
  tables: EvidenceNode[];
  selectedCitation?: Citation | null;
}) {
  const initialPageNumber = selectedCitation?.page_number ?? pages[0]?.page_number ?? 1;
  const [activePageNumber, setActivePageNumber] = useState(initialPageNumber);
  const [activeTextBlocks, setActiveTextBlocks] = useState(textBlocks);
  const [activeTables, setActiveTables] = useState(tables);

  useEffect(() => {
    if (selectedCitation) {
      setActivePageNumber(selectedCitation.page_number);
    }
  }, [selectedCitation]);

  useEffect(() => {
    setActiveTextBlocks(textBlocks);
    setActiveTables(tables);
  }, [textBlocks, tables]);

  useEffect(() => {
    if (!document) {
      return;
    }
    const documentId = document.id;
    let cancelled = false;
    async function loadPageEvidence() {
      const [nextTextBlocks, nextTables] = await Promise.all([
        listPageTextBlocks(documentId, activePageNumber).catch(() => []),
        listPageTables(documentId, activePageNumber).catch(() => []),
      ]);
      if (!cancelled) {
        setActiveTextBlocks(nextTextBlocks);
        setActiveTables(nextTables);
      }
    }
    loadPageEvidence();
    return () => {
      cancelled = true;
    };
  }, [activePageNumber, document]);

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

  const page = useMemo(
    () => pages.find((item) => item.page_number === activePageNumber) ?? pages[0],
    [activePageNumber, pages],
  );

  return (
    <div className="page-viewer">
      <div className="page-viewer-toolbar">
        <div>
          <p className="eyebrow">Page Viewer</p>
          <h3>
            {document.filename} · page {page.page_number} of {pages.length}
          </h3>
          {selectedCitation ? (
            <p className="selected-citation-banner">
              Selected {selectedCitation.node_type} citation on page{" "}
              {selectedCitation.page_number}
            </p>
          ) : null}
        </div>
        <div className="page-metrics">
          <span>
            PDF {Math.round(page.width)} x {Math.round(page.height)} pt
          </span>
          <span>
            PNG {page.image_width} x {page.image_height}px
          </span>
          <span>{activeTextBlocks.length} text blocks</span>
          <span>{activeTables.length} tables</span>
        </div>
      </div>

      <div className="page-canvas">
        <img alt={`Page ${page.page_number}`} src={absoluteApiUrl(page.image_url)} />
        {activeTextBlocks.map((node) => (
          <div
            className="text-bbox"
            key={node.id}
            style={overlayStyle(page, node)}
            title={`#${node.reading_order}: ${node.text}`}
          >
            <span>{node.reading_order}</span>
          </div>
        ))}
        {activeTables.map((table) => (
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
        {selectedCitation && selectedCitation.page_number === page.page_number ? (
          <div
            className="selected-citation-bbox"
            style={bboxStyle(page, selectedCitation.bbox)}
            title={`Selected citation: ${selectedCitation.snippet}`}
          >
            <span>citation</span>
          </div>
        ) : null}
      </div>
      <p className="page-note">
        Text and table boxes come from PyMuPDF evidence nodes. Click an answer
        citation to jump to its page and highlight the cited bbox.
      </p>
    </div>
  );
}
