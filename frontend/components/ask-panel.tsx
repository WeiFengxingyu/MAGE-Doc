"use client";

import { useFormState, useFormStatus } from "react-dom";

import { askQuestionAction } from "@/app/actions";
import type { AskState, Citation, DocumentRecord } from "@/types/api";

const initialState: AskState = {
  ok: false,
  message: "Ask a grounded question over parsed evidence.",
  question: "",
  response: null,
};

function AskButton({ disabled }: { disabled: boolean }) {
  const { pending } = useFormStatus();
  return (
    <button className="primary-button" disabled={pending || disabled} type="submit">
      {pending ? "Asking..." : "Ask"}
    </button>
  );
}

function formatBbox(bbox: Citation["bbox"]): string {
  return bbox.map((value) => value.toFixed(1)).join(", ");
}

export function AskPanel({
  document,
  onCitationSelect,
  selectedCitationId,
}: {
  document: DocumentRecord | null;
  onCitationSelect?: (citation: Citation) => void;
  selectedCitationId?: string | null;
}) {
  const [state, formAction] = useFormState(askQuestionAction, initialState);
  const response = state.response;

  return (
    <section className="ask-panel">
      <div className="ask-header">
        <div>
          <p className="eyebrow">Agentic RAG</p>
          <h3>Ask with citations.</h3>
        </div>
        <span>{response?.question_type ?? "V0 workflow"}</span>
      </div>

      <form action={formAction} className="ask-form">
        <input name="document_id" type="hidden" value={document?.id ?? ""} />
        <textarea
          aria-label="Question"
          defaultValue={state.question}
          name="question"
          placeholder="What was revenue in 2026?"
          rows={3}
        />
        <AskButton disabled={!document} />
      </form>

      <p className={state.ok ? "form-message" : "form-message form-message-error"}>
        {document ? state.message : "Upload and parse a document before asking."}
      </p>

      {response ? (
        <div className="answer-box">
          <div className="answer-main">
            <p className="eyebrow">Answer</p>
            <p>{response.answer}</p>
          </div>

          <div className="citation-list">
            <p className="eyebrow">Citations</p>
            {response.citations.length === 0 ? (
              <span className="muted-line">No verified citations.</span>
            ) : (
              response.citations.map((citation) => (
                <button
                  className={
                    citation.node_id === selectedCitationId
                      ? "citation-item citation-button citation-button-active"
                      : "citation-item citation-button"
                  }
                  key={citation.node_id}
                  onClick={() => onCitationSelect?.(citation)}
                  type="button"
                >
                  <div>
                    <strong>{citation.node_type}</strong>
                    <span>page {citation.page_number}</span>
                  </div>
                  <p>{citation.snippet}</p>
                  <code>bbox [{formatBbox(citation.bbox)}]</code>
                </button>
              ))
            )}
          </div>

          <div className="trace-list">
            <p className="eyebrow">Trace</p>
            {response.trace.map((trace, index) => (
              <div className="trace-item" key={`${trace.tool_name}-${index}`}>
                <strong>{trace.tool_name}</strong>
                <span>{trace.output_summary}</span>
                <span>{trace.latency_ms}ms</span>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
