"use client";

import { useState } from "react";

import { AskPanel } from "@/components/ask-panel";
import { PageViewer } from "@/components/page-viewer";
import { ProductDemoPanel } from "@/components/product-demo-panel";
import { RepairTracePanel } from "@/components/repair-trace-panel";
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
      <ProductDemoPanel
        document={document}
        pages={pages}
        tables={tables}
        textBlocks={textBlocks}
      />
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
      <RepairTracePanel document={document} />
      <RetrievalPanel document={document} />
    </>
  );
}
