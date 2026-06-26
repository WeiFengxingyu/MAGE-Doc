"use client";

import { useFormState, useFormStatus } from "react-dom";

import { askSelfCorrectingQuestionAction } from "@/app/actions";
import type { DocumentRecord, RepairTraceState, SufficiencyScore } from "@/types/api";

const initialState: RepairTraceState = {
  ok: false,
  message: "Run V3 self-correction to inspect repair decisions.",
  question: "What was revenue in 2026?",
  response: null,
};

function RepairButton({ disabled }: { disabled: boolean }) {
  const { pending } = useFormStatus();
  return (
    <button className="primary-button" disabled={pending || disabled} type="submit">
      {pending ? "Repairing..." : "Run V3"}
    </button>
  );
}

function ScorePill({ label, score }: SufficiencyScore) {
  return (
    <span className={`sufficiency-pill sufficiency-${label}`}>
      {label} {score.toFixed(2)}
    </span>
  );
}

export function RepairTracePanel({ document }: { document: DocumentRecord | null }) {
  const [state, formAction] = useFormState(askSelfCorrectingQuestionAction, initialState);
  const response = state.response;

  return (
    <section className="repair-panel">
      <div className="repair-header">
        <div>
          <p className="eyebrow">V3 Reliability</p>
          <h3>Repair trace.</h3>
        </div>
        <span>{response?.stop_reason ?? "self-correcting"}</span>
      </div>

      <form action={formAction} className="repair-form">
        <input name="document_id" type="hidden" value={document?.id ?? ""} />
        <input
          aria-label="V3 question"
          defaultValue={state.question}
          name="question"
          placeholder="What was revenue in 2026?"
        />
        <RepairButton disabled={!document} />
      </form>

      <p className={state.ok ? "form-message" : "form-message form-message-error"}>
        {document ? state.message : "Upload and prepare a document before running V3 repair."}
      </p>

      {response ? (
        <div className="repair-results">
          <div className="repair-score-row">
            <div>
              <p className="eyebrow">Initial</p>
              <ScorePill {...response.initial_sufficiency} />
            </div>
            <div>
              <p className="eyebrow">Final</p>
              <ScorePill {...response.final_sufficiency} />
            </div>
          </div>

          <div className="repair-answer">
            <strong>{response.final_diagnosis.reason}</strong>
            <p>{response.final_diagnosis.message}</p>
          </div>

          <div className="repair-rounds">
            <p className="eyebrow">Repair Rounds</p>
            {response.repair_rounds.length === 0 ? (
              <span className="muted-line">No repair was required.</span>
            ) : (
              response.repair_rounds.map((round) => (
                <article className="repair-round" key={round.round_index}>
                  <div className="repair-round-topline">
                    <strong>Round {round.round_index}</strong>
                    <span>{String(round.selected_action.action ?? "repair")}</span>
                  </div>
                  <p>{round.diagnosis.message}</p>
                  <div className="repair-score-row">
                    <ScorePill {...round.before_sufficiency} />
                    <ScorePill {...round.after_sufficiency} />
                  </div>
                </article>
              ))
            )}
          </div>
        </div>
      ) : null}
    </section>
  );
}
