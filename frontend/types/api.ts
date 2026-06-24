export type HealthResponse = {
  status: string;
  service: string;
  version: string;
};

export type ApiStatusResponse = HealthResponse & {
  environment: string;
};

export type DocumentRecord = {
  id: string;
  filename: string;
  content_type: string;
  file_size: number;
  page_count: number | null;
  status:
    | "uploaded"
    | "rendering"
    | "rendered"
    | "parsing"
    | "parsed"
    | "parsing_tables"
    | "tables_parsed"
    | "failed";
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type UploadState = {
  ok: boolean;
  message: string;
};

export type PageRecord = {
  id: string;
  document_id: string;
  page_number: number;
  width: number;
  height: number;
  image_width: number;
  image_height: number;
  image_url: string;
  created_at: string;
};

export type EvidenceNode = {
  id: string;
  document_id: string;
  page_id: string;
  page_number: number;
  node_type: "text_block" | "table";
  text: string;
  bbox: [number, number, number, number];
  reading_order: number;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type ToolTrace = {
  tool_name: string;
  input: Record<string, unknown>;
  output_summary: string;
  latency_ms: number;
};

export type SearchResult = {
  rank: number;
  score: number;
  matched_terms: string[];
  snippet: string;
  node: EvidenceNode;
};

export type SearchResponse = {
  query: string;
  document_id: string;
  results: SearchResult[];
  tool_trace: ToolTrace;
};

export type SearchState = {
  ok: boolean;
  message: string;
  query: string;
  scope: "all" | "text" | "tables";
  response: SearchResponse | null;
};
