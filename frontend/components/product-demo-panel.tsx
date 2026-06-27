"use client";

import { useState } from "react";

import { prepareDemo, runTrustedDemo } from "@/lib/api";
import type {
  DocumentRecord,
  EvidenceNode,
  PageRecord,
  TrustedDemoResponse,
} from "@/types/api";

const DEFAULT_INTERVIEW_QUESTION = "What was revenue in 2026?";

function downloadMarkdown(filename: string, markdown: string) {
  const blob = new Blob([markdown], {
    type: "text/markdown;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const anchor = window.document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

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
  const [question, setQuestion] = useState(DEFAULT_INTERVIEW_QUESTION);
  const [status, setStatus] = useState("Ready to run the full interview demo.");
  const [isRunning, setIsRunning] = useState(false);
  const [demo, setDemo] = useState<TrustedDemoResponse | null>(null);

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

  async function handleRunInterviewDemo() {
    if (!document) {
      setStatus("Upload or select a PDF before running the demo.");
      return;
    }

    const cleanQuestion = question.trim() || DEFAULT_INTERVIEW_QUESTION;
    setIsRunning(true);
    setDemo(null);
    try {
      if (document.status !== "demo_ready") {
        setStatus("Preparing PDF evidence...");
        await prepareDemo(document.id);
      }

      setStatus("Running self-correcting trusted QA...");
      const result = await runTrustedDemo({
        documentId: document.id,
        question: cleanQuestion,
        reportTitle: `${document.filename} Interview Demo Report`,
      });
      setDemo(result);
      setStatus(
        `${result.qa.repair_round_count} repair rounds, ${result.report.summary.citation_count} citations, ${result.qa.stop_reason}.`,
      );
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Interview demo failed.");
    } finally {
      setIsRunning(false);
    }
  }

  function handleDownloadReport() {
    if (!demo) {
      return;
    }
    downloadMarkdown(demo.report.filename, demo.report.markdown);
  }

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

      <div className="interview-demo-runner">
        <div className="interview-demo-controls">
          <input
            aria-label="Interview demo question"
            onChange={(event) => setQuestion(event.target.value)}
            value={question}
          />
          <button
            className="primary-button"
            disabled={!document || isRunning}
            onClick={handleRunInterviewDemo}
            type="button"
          >
            {isRunning ? "Running demo..." : "Run interview demo"}
          </button>
        </div>
        <div className="interview-demo-status">
          <span>{status}</span>
          {demo ? (
            <button className="mini-button" onClick={handleDownloadReport} type="button">
              Download report
            </button>
          ) : null}
        </div>
      </div>

      {demo ? (
        <div className="interview-demo-result">
          <div className="interview-demo-result-header">
            <div>
              <p className="eyebrow">One-click Result</p>
              <strong>{demo.qa.final_sufficiency.label}</strong>
            </div>
            <span>{demo.report.filename}</span>
          </div>
          <p>{demo.qa.answer}</p>
          <div className="interview-demo-result-metrics">
            <span>score {demo.qa.final_sufficiency.score.toFixed(2)}</span>
            <span>{demo.qa.repair_round_count} repairs</span>
            <span>{demo.qa.citations.length} citations</span>
            <span>{demo.qa.stop_reason}</span>
          </div>
          <pre>{demo.report.markdown.slice(0, 700)}</pre>
        </div>
      ) : null}

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
