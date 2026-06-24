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
    | "preparing_demo"
    | "demo_ready"
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
  node_type: "text_block" | "table" | "section" | "table_cell" | "caption";
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

export type EvidenceEdge = {
  id: string;
  document_id: string;
  source_node_id: string | null;
  target_node_id: string;
  edge_type: "contains" | "next" | "part_of" | "caption_of" | "near" | string;
  weight: number;
  source: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type SearchResult = {
  rank: number;
  score: number;
  matched_terms: string[];
  snippet: string;
  node: EvidenceNode;
  retrieval_source: string;
  candidate_sources: string[];
  score_breakdown: Record<string, number>;
};

export type SearchResponse = {
  query: string;
  document_id: string;
  results: SearchResult[];
  tool_trace: ToolTrace;
};

export type EvidencePackItem = {
  node: EvidenceNode;
  source_candidate_node_id: string;
  source_candidate_rank: number;
  graph_distance: number;
  inclusion_reason: string;
  path: EvidenceEdge[];
  score_breakdown: Record<string, number>;
  metadata: Record<string, unknown>;
};

export type EvidencePackResponse = {
  query: string;
  document_id: string;
  source_candidates: SearchResult[];
  nodes: EvidenceNode[];
  edges: EvidenceEdge[];
  items: EvidencePackItem[];
  summary: {
    source_candidate_count: number;
    expanded_node_count: number;
    edge_count: number;
    item_count: number;
    max_graph_distance: number;
    edge_type_counts: Record<string, number>;
    node_type_counts: Record<string, number>;
  };
  tool_trace: ToolTrace;
};

export type SearchState = {
  ok: boolean;
  message: string;
  query: string;
  scope: "all" | "text" | "tables";
  response: SearchResponse | null;
};

export type Citation = {
  node_id: string;
  node_type: "text_block" | "table";
  page_number: number;
  bbox: [number, number, number, number];
  snippet: string;
};

export type Verification = {
  document_id: string;
  passed: boolean;
  answer_present: boolean;
  citation_count: number;
  covered_citation_node_ids: string[];
  missing_citation_node_ids: string[];
  tool_trace: ToolTrace;
};

export type ClaimVerificationItem = {
  claim: string;
  status: string;
  citation_node_ids: string[];
  reason: string;
  matched_terms: string[];
  missing_terms: string[];
  required_node_types: string[];
};

export type ClaimVerification = {
  status: string;
  claim_count: number;
  supported_count: number;
  partial_count: number;
  unsupported_count: number;
  insufficient_evidence_count: number;
  claims: ClaimVerificationItem[];
  tool_trace: ToolTrace;
};

export type QuestionAnswerResponse = {
  trace_id: string | null;
  document_id: string;
  question: string;
  question_type: "table_lookup" | "text_lookup";
  answer: string;
  citations: Citation[];
  trace: ToolTrace[];
  verification: Verification;
  claim_verification: ClaimVerification | null;
};

export type ToolDefinition = {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
  phase: string;
};

export type AgentToolCall = {
  id: string;
  trace_run_id: string;
  document_id: string;
  step_index: number;
  tool_name: string;
  input: Record<string, unknown>;
  output_summary: string;
  latency_ms: number;
  status: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type AgentTraceRunSummary = {
  id: string;
  document_id: string;
  question: string;
  question_type: string;
  status: string;
  answer_preview: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  tool_call_count: number;
};

export type AgentTraceRunDetail = AgentTraceRunSummary & {
  tool_calls: AgentToolCall[];
};

export type AskState = {
  ok: boolean;
  message: string;
  question: string;
  response: QuestionAnswerResponse | null;
};

export type PrepareDemoResponse = {
  document_id: string;
  status: "demo_ready";
  page_count: number;
  text_block_count: number;
  table_count: number;
  steps: Array<{
    name: string;
    status: string;
    output_summary: string;
  }>;
};
