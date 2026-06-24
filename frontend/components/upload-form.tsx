"use client";

import { useFormState, useFormStatus } from "react-dom";

import { uploadDocumentAction } from "@/app/actions";
import type { UploadState } from "@/types/api";

const initialState: UploadState = {
  ok: true,
  message: "Upload a PDF to start the V0 document workflow.",
};

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button className="primary-button" disabled={pending} type="submit">
      {pending ? "Uploading..." : "Upload PDF"}
    </button>
  );
}

export function UploadForm() {
  const [state, formAction] = useFormState(uploadDocumentAction, initialState);

  return (
    <form action={formAction} className="upload-form">
      <label htmlFor="file">PDF document</label>
      <input accept="application/pdf,.pdf" id="file" name="file" type="file" />
      <SubmitButton />
      <p className={state.ok ? "form-message" : "form-message form-message-error"}>
        {state.message}
      </p>
    </form>
  );
}

