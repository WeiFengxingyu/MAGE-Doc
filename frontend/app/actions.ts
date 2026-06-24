"use server";

import { revalidatePath } from "next/cache";

import {
  parseTables,
  parseTextBlocks,
  renderDocument,
  searchEvidence,
  uploadDocument,
} from "@/lib/api";
import type { SearchState, UploadState } from "@/types/api";

export async function uploadDocumentAction(
  _previousState: UploadState,
  formData: FormData,
): Promise<UploadState> {
  const value = formData.get("file");
  if (!(value instanceof File) || value.size === 0) {
    return {
      ok: false,
      message: "Choose a non-empty PDF before uploading.",
    };
  }

  try {
    const document = await uploadDocument(value);
    revalidatePath("/");
    return {
      ok: true,
      message: `${document.filename} uploaded successfully.`,
    };
  } catch (error) {
    return {
      ok: false,
      message: error instanceof Error ? error.message : "Upload failed.",
    };
  }
}

export async function renderDocumentAction(formData: FormData): Promise<void> {
  const documentId = formData.get("document_id");
  if (typeof documentId !== "string" || documentId.length === 0) {
    return;
  }

  await renderDocument(documentId);
  revalidatePath("/");
}

export async function parseTextBlocksAction(formData: FormData): Promise<void> {
  const documentId = formData.get("document_id");
  if (typeof documentId !== "string" || documentId.length === 0) {
    return;
  }

  await parseTextBlocks(documentId);
  revalidatePath("/");
}

export async function parseTablesAction(formData: FormData): Promise<void> {
  const documentId = formData.get("document_id");
  if (typeof documentId !== "string" || documentId.length === 0) {
    return;
  }

  await parseTables(documentId);
  revalidatePath("/");
}

export async function searchEvidenceAction(
  _previousState: SearchState,
  formData: FormData,
): Promise<SearchState> {
  const documentId = formData.get("document_id");
  const query = formData.get("query");
  const scopeValue = formData.get("scope");
  const scope = scopeValue === "text" || scopeValue === "tables" ? scopeValue : "all";

  if (typeof documentId !== "string" || documentId.length === 0) {
    return {
      ok: false,
      message: "Upload a document before searching.",
      query: "",
      scope,
      response: null,
    };
  }
  if (typeof query !== "string" || query.trim().length === 0) {
    return {
      ok: false,
      message: "Enter a search query.",
      query: "",
      scope,
      response: null,
    };
  }

  try {
    const response = await searchEvidence({
      documentId,
      query: query.trim(),
      scope,
    });
    return {
      ok: true,
      message: `${response.results.length} evidence results.`,
      query: query.trim(),
      scope,
      response,
    };
  } catch (error) {
    return {
      ok: false,
      message: error instanceof Error ? error.message : "Evidence search failed.",
      query: query.trim(),
      scope,
      response: null,
    };
  }
}
