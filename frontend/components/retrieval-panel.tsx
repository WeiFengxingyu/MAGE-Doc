"use client";

import { useFormState, useFormStatus } from "react-dom";

import { searchEvidenceAction } from "@/app/actions";
import type { DocumentRecord, SearchState } from "@/types/api";

const initialState: SearchState = {
  ok: false,
  message: "Search parsed evidence nodes.",
  query: "",
  scope: "all",
  response: null,
};

function SearchButton({ disabled }: { disabled: boolean }) {
  const { pending } = useFormStatus();
  return (
    <button className="primary-button" disabled={pending || disabled} type="submit">
      {pending ? "Searching..." : "Search"}
    </button>
  );
}

function formatBbox(bbox: [number, number, number, number]): string {
  return bbox.map((value) => value.toFixed(1)).join(", ");
}

export function RetrievalPanel({ document }: { document: DocumentRecord | null }) {
  const [state, formAction] = useFormState(searchEvidenceAction, initialState);

  return (
    <section className="retrieval-panel">
      <div className="retrieval-header">
        <div>
          <p className="eyebrow">Retrieval Tools</p>
          <h3>Search evidence nodes.</h3>
        </div>
        <span>{state.response?.tool_trace.output_summary ?? "BM25-style"}</span>
      </div>

      <form action={formAction} className="retrieval-form">
        <input name="document_id" type="hidden" value={document?.id ?? ""} />
        <input
          aria-label="Evidence query"
          defaultValue={state.query}
          name="query"
          placeholder="Revenue 2026, risk factors, margin..."
          type="search"
        />
        <select aria-label="Evidence scope" defaultValue={state.scope} name="scope">
          <option value="all">All evidence</option>
          <option value="text">Text only</option>
          <option value="tables">Tables only</option>
        </select>
        <SearchButton disabled={!document} />
      </form>

      <p className={state.ok ? "form-message" : "form-message form-message-error"}>
        {document ? state.message : "Upload and parse a document before searching."}
      </p>

      {state.response ? (
        <div className="search-results">
          {state.response.results.map((result) => (
            <article className="search-result" key={result.node.id}>
              <div className="result-topline">
                <strong>#{result.rank}</strong>
                <span>{result.node.node_type}</span>
                <span>page {result.node.page_number}</span>
                <span>score {result.score.toFixed(3)}</span>
              </div>
              <p>{result.snippet}</p>
              <div className="result-tags">
                {result.matched_terms.map((term) => (
                  <span key={term}>{term}</span>
                ))}
              </div>
              <code>bbox [{formatBbox(result.node.bbox)}]</code>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
