"use client";

import { useState } from "react";
import { indexWorkspaceCodebase, searchCodebaseRAG } from "@/lib/api";
import { IndexWorkspaceResponse, RAGQueryResponse } from "@/types/rag";

export function RAGSearch() {
  const [query, setQuery] = useState<string>("CORS middleware configuration");
  const [topK, setTopK] = useState<number>(5);
  const [fileExt, setFileExt] = useState<string>("");
  const [indexing, setIndexing] = useState<boolean>(false);
  const [searching, setSearching] = useState<boolean>(false);
  const [indexStats, setIndexStats] = useState<IndexWorkspaceResponse | null>(null);
  const [response, setResponse] = useState<RAGQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleIndex = async () => {
    setIndexing(true);
    setError(null);
    try {
      const stats = await indexWorkspaceCodebase();
      setIndexStats(stats);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Workspace indexing failed";
      setError(msg);
    } finally {
      setIndexing(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setSearching(true);
    setError(null);
    setResponse(null);

    try {
      const res = await searchCodebaseRAG({
        query,
        top_k: topK,
        file_extension: fileExt.trim() || undefined,
      });
      setResponse(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Vector search failed";
      setError(msg);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-2">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <span>🔍</span> RAG &amp; Vector Semantic Code Search
          </h2>
          <p className="text-slate-400 text-xs mt-1">
            Offline vector embeddings &amp; semantic similarity search (<code className="text-blue-400 font-mono">backend/app/agent/rag/</code>).
          </p>
        </div>

        <button
          onClick={handleIndex}
          disabled={indexing}
          className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white font-mono text-xs font-bold rounded-lg transition-all shadow-md disabled:opacity-50 flex items-center gap-2"
        >
          {indexing ? (
            <>
              <span className="animate-spin rounded-full h-3 w-3 border-2 border-white border-t-transparent" />
              Indexing Codebase...
            </>
          ) : (
            "⚡ Re-Index Workspace"
          )}
        </button>
      </div>

      {/* Index Stats Notice */}
      {indexStats && (
        <div className="mb-6 p-3 bg-teal-500/10 border border-teal-500/30 rounded-xl text-teal-400 text-xs font-mono flex justify-between items-center">
          <span>
            ✓ Indexed <strong>{indexStats.total_files_scanned}</strong> files into <strong>{indexStats.total_chunks_created}</strong> code chunks in {indexStats.duration_ms.toFixed(1)} ms.
          </span>
          <span className="text-[10px] text-teal-500">
            {new Date(indexStats.timestamp).toLocaleTimeString()}
          </span>
        </div>
      )}

      {/* Search Form */}
      <form onSubmit={handleSearch} className="space-y-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search code semantically (e.g. MongoDB connection setup or health endpoint)..."
            className="flex-1 bg-slate-950/90 border border-slate-800 rounded-lg px-3 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-blue-500 font-sans"
            required
          />

          <select
            value={fileExt}
            onChange={(e) => setFileExt(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-slate-300 text-xs rounded-lg px-3 py-2.5 font-mono focus:outline-none"
          >
            <option value="">All Extensions</option>
            <option value=".py">.py (Python)</option>
            <option value=".ts">.ts (TypeScript)</option>
            <option value=".tsx">.tsx (React Component)</option>
            <option value=".md">.md (Documentation)</option>
          </select>

          <select
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="bg-slate-950 border border-slate-800 text-slate-300 text-xs rounded-lg px-3 py-2.5 font-mono focus:outline-none"
          >
            <option value={3}>Top 3</option>
            <option value={5}>Top 5</option>
            <option value={10}>Top 10</option>
          </select>

          <button
            type="submit"
            disabled={searching || !query.trim()}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-mono font-bold rounded-lg transition-all shadow-md disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {searching ? (
              <>
                <span className="animate-spin rounded-full h-3 w-3 border-2 border-white border-t-transparent" />
                Searching...
              </>
            ) : (
              "Vector Search"
            )}
          </button>
        </div>
      </form>

      {/* Error display */}
      {error && (
        <div className="mt-5 p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs font-mono">
          <div className="font-bold mb-1">⚠️ Search Error:</div>
          <div>{error}</div>
        </div>
      )}

      {/* Search Results Display */}
      {response && (
        <div className="mt-6 pt-6 border-t border-slate-800 space-y-4">
          <div className="flex flex-wrap justify-between items-center gap-2 text-xs font-mono text-slate-400">
            <span className="text-emerald-400 font-bold">
              ✓ Found {response.results.length} code matches
            </span>
            <span className="text-slate-500">
              Total Chunks Indexed: {response.total_chunks_indexed} | Search Latency: {response.execution_time_ms.toFixed(1)} ms
            </span>
          </div>

          {response.results.length > 0 ? (
            <div className="space-y-4">
              {response.results.map((res, idx) => (
                <div
                  key={res.chunk.chunk_id || idx}
                  className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2 font-mono text-xs"
                >
                  <div className="flex justify-between items-center pb-2 border-b border-slate-800/80">
                    <span className="text-blue-400 font-semibold flex items-center gap-2">
                      <span>📄</span> {res.chunk.file_path}
                      <span className="text-slate-500 text-[11px]">
                        (Lines {res.chunk.start_line}–{res.chunk.end_line})
                      </span>
                    </span>
                    <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-teal-500/10 text-teal-400 border border-teal-500/30">
                      Score: {(res.score * 100).toFixed(1)}%
                    </span>
                  </div>

                  <pre className="text-slate-200 whitespace-pre-wrap leading-relaxed overflow-x-auto max-h-60 pt-1 text-[11px]">
                    {res.chunk.content}
                  </pre>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-slate-500 text-xs font-mono py-4 text-center">
              No matching code chunks found for &quot;{response.query}&quot;. Try re-indexing or broadening your query.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
