"use client";

import { useState } from "react";

import { AskPanel } from "@/components/ask-panel";
import { PageViewer } from "@/components/page-viewer";
import { RetrievalPanel } from "@/components/retrieval-panel";
import type { Citation, DocumentRecord, EvidenceNode, PageRecord } from "@/types/api";

export function DocumentWorkbench({
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
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);

  return (
    <>
      {document?.status === "demo_ready" ? (
        <div className="demo-ready-panel">
          <div>
            <p className="eyebrow">Demo Ready</p>
            <strong>Ask a question, inspect citations, then click a citation to highlight evidence.</strong>
          </div>
          <span>{pages.length} rendered pages</span>
        </div>
      ) : null}
      <PageViewer
        document={document}
        pages={pages}
        selectedCitation={selectedCitation}
        tables={tables}
        textBlocks={textBlocks}
      />
      <AskPanel
        document={document}
        onCitationSelect={setSelectedCitation}
        selectedCitationId={selectedCitation?.node_id ?? null}
      />
      <RetrievalPanel document={document} />
    </>
  );
}
