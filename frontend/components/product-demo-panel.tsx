"use client";

import type { DocumentRecord, EvidenceNode, PageRecord } from "@/types/api";

function ReadinessBadge({ document }: { document: DocumentRecord | null }) {
  if (!document) {
    return <span className="product-demo-badge product-demo-badge-idle">No document</span>;
  }
  if (document.status === "demo_ready") {
    return <span className="product-demo-badge product-demo-badge-ready">Demo ready</span>;
  }
  if (document.status === "failed") {
    return <span className="product-demo-badge product-demo-badge-warn">Needs review</span>;
  }
  return <span className="product-demo-badge product-demo-badge-idle">Prepare demo</span>;
}

export function ProductDemoPanel({
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
  const capabilities = [
    {
      label: "Evidence preview",
      value: `${textBlocks.length + tables.length} nodes`,
    },
    {
      label: "Citation grounding",
      value: `${pages.length} pages`,
    },
    {
      label: "Self-correction",
      value: "V3 repair trace",
    },
    {
      label: "Report export",
      value: "Markdown deliverable",
    },
  ];

  return (
    <section className="product-demo-panel">
      <div className="product-demo-main">
        <div>
          <p className="eyebrow">Product Demo</p>
          <h3>Trusted long-document QA.</h3>
          <p>
            A cited QA workflow for long PDFs with visible repair decisions and a
            reviewer-ready answer report.
          </p>
        </div>
        <ReadinessBadge document={document} />
      </div>

      <div className="product-demo-flow">
        <span>Prepare</span>
        <span>Ask</span>
        <span>Repair</span>
        <span>Export</span>
      </div>

      <div className="product-demo-metrics">
        {capabilities.map((capability) => (
          <div key={capability.label}>
            <strong>{capability.value}</strong>
            <span>{capability.label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
