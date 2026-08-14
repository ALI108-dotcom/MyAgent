export interface DocumentChunk {
  chunk_id: string;
  file_path: string;
  start_line: number;
  end_line: number;
  content: string;
  metadata: Record<string, unknown>;
}

export interface SearchResult {
  chunk: DocumentChunk;
  score: number;
}

export interface RAGQueryRequest {
  query: string;
  top_k?: number;
  file_extension?: string;
}

export interface RAGQueryResponse {
  query: string;
  results: SearchResult[];
  total_chunks_indexed: number;
  execution_time_ms: number;
  timestamp: string;
}

export interface IndexWorkspaceResponse {
  total_files_scanned: number;
  total_chunks_created: number;
  duration_ms: number;
  timestamp: string;
}
