import type {
  ApiStatusResponse,
  DocumentRecord,
  EvidenceNode,
  PageRecord,
  PrepareDemoResponse,
  QuestionAnswerResponse,
  SearchResponse,
  SelfCorrectingQuestionResponse,
  TrustedAnswerReportResponse,
  V2StatusResponse,
} from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function getApiStatus(): Promise<ApiStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/api/status`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API status request failed: ${response.status}`);
  }

  return response.json() as Promise<ApiStatusResponse>;
}

export async function getV2Status(): Promise<V2StatusResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v2/status`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`V2 status request failed: ${response.status}`);
  }

  return response.json() as Promise<V2StatusResponse>;
}

export async function listDocuments(): Promise<DocumentRecord[]> {
  const response = await fetch(`${API_BASE_URL}/api/documents`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Document list request failed: ${response.status}`);
  }

  return response.json() as Promise<DocumentRecord[]>;
}

export async function uploadDocument(file: File): Promise<DocumentRecord> {
  const body = new FormData();
  body.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/documents`, {
    method: "POST",
    body,
  });

  if (!response.ok) {
    let detail = `Upload failed: ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // Keep the generic status-based error.
    }
    throw new Error(detail);
  }

  return response.json() as Promise<DocumentRecord>;
}

export async function renderDocument(documentId: string): Promise<PageRecord[]> {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/render`, {
    method: "POST",
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Render request failed: ${response.status}`);
  }

  return response.json() as Promise<PageRecord[]>;
}

export async function parseTextBlocks(documentId: string): Promise<EvidenceNode[]> {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/parse-text`, {
    method: "POST",
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Text parsing request failed: ${response.status}`);
  }

  return response.json() as Promise<EvidenceNode[]>;
}

export async function parseTables(documentId: string): Promise<EvidenceNode[]> {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/parse-tables`, {
    method: "POST",
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Table parsing request failed: ${response.status}`);
  }

  return response.json() as Promise<EvidenceNode[]>;
}

export async function prepareDemo(documentId: string): Promise<PrepareDemoResponse> {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/prepare-demo`, {
    method: "POST",
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Prepare demo request failed: ${response.status}`);
  }

  return response.json() as Promise<PrepareDemoResponse>;
}

export async function listPages(documentId: string): Promise<PageRecord[]> {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/pages`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Page list request failed: ${response.status}`);
  }

  return response.json() as Promise<PageRecord[]>;
}

export async function listPageTextBlocks(
  documentId: string,
  pageNumber: number,
): Promise<EvidenceNode[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/documents/${documentId}/pages/${pageNumber}/text-blocks`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(`Page text block request failed: ${response.status}`);
  }

  return response.json() as Promise<EvidenceNode[]>;
}

export async function listPageTables(
  documentId: string,
  pageNumber: number,
): Promise<EvidenceNode[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/documents/${documentId}/pages/${pageNumber}/tables`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(`Page table request failed: ${response.status}`);
  }

  return response.json() as Promise<EvidenceNode[]>;
}

export async function searchEvidence({
  documentId,
  query,
  scope,
}: {
  documentId: string;
  query: string;
  scope: "all" | "text" | "tables";
}): Promise<SearchResponse> {
  const params = new URLSearchParams({
    query,
    top_k: "5",
  });
  if (scope === "text") {
    params.set("node_types", "text_block");
  }
  if (scope === "tables") {
    params.set("node_types", "table");
  }

  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/search?${params}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Evidence search failed: ${response.status}`);
  }

  return response.json() as Promise<SearchResponse>;
}

export async function askQuestion({
  documentId,
  question,
}: {
  documentId: string;
  question: string;
}): Promise<QuestionAnswerResponse> {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/questions`, {
    method: "POST",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    let detail = `Question request failed: ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // Keep the status-based error.
    }
    throw new Error(detail);
  }

  return response.json() as Promise<QuestionAnswerResponse>;
}

export async function askSelfCorrectingQuestion({
  documentId,
  question,
  maxRepairRounds = 2,
}: {
  documentId: string;
  question: string;
  maxRepairRounds?: number;
}): Promise<SelfCorrectingQuestionResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v3/documents/${documentId}/self-correcting-questions`,
    {
      method: "POST",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question, max_repair_rounds: maxRepairRounds }),
    },
  );

  if (!response.ok) {
    throw new Error(`Self-correcting question request failed: ${response.status}`);
  }

  return response.json() as Promise<SelfCorrectingQuestionResponse>;
}

export async function exportTrustedAnswerReport({
  title,
  question,
  response: trustedAnswer,
}: {
  title: string;
  question: string;
  response: SelfCorrectingQuestionResponse;
}): Promise<TrustedAnswerReportResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v3/reports/trusted-answer`, {
    method: "POST",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      title,
      question,
      response: trustedAnswer,
    }),
  });

  if (!response.ok) {
    throw new Error(`Trusted answer report export failed: ${response.status}`);
  }

  return response.json() as Promise<TrustedAnswerReportResponse>;
}

export function absoluteApiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}
