import type { ApiStatusResponse, DocumentRecord, EvidenceNode, PageRecord } from "@/types/api";

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

export function absoluteApiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}
