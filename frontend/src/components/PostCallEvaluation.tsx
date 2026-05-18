import { useRef, useState } from "react";
import { scoreTranscript } from "../api";
import type { RestaurantInfo, ScorecardData } from "../types";

interface Props {
  restaurant: RestaurantInfo;
  onScorecardGenerated: (scorecard: ScorecardData) => void;
}

export default function PostCallEvaluation({ restaurant, onScorecardGenerated }: Props) {
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
    if (f) setText("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() && !file) {
      setError("Please paste a transcript or upload a file.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await scoreTranscript(text || null, file, restaurant.name);
      onScorecardGenerated(result.scorecard);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to score call. Please try again.");
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[420px] gap-6">
        <div className="w-12 h-12 border-4 border-[#1e3a5f] border-t-transparent rounded-full animate-spin" />
        <div className="text-center">
          <p className="text-lg font-semibold text-slate-700">Scoring your call...</p>
          <p className="text-sm text-slate-400 mt-1">Evaluating 5 behavioral dimensions</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-800">Post-Call Evaluation</h2>
        <p className="text-slate-400 text-sm mt-0.5">
          Call with{" "}
          <span className="font-medium text-slate-600">{restaurant.name}</span> ·{" "}
          {restaurant.city}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Paste area */}
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Paste transcript
          </label>
          <textarea
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              setFile(null);
            }}
            placeholder="Paste your call transcript here..."
            rows={10}
            className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg resize-y focus:outline-none focus:ring-2 focus:ring-[#1e3a5f] focus:border-transparent text-slate-700 placeholder-slate-400"
          />
        </div>

        {/* Divider */}
        <div className="flex items-center gap-3">
          <div className="flex-1 border-t border-slate-200" />
          <span className="text-xs text-slate-400 font-semibold uppercase tracking-wide">or</span>
          <div className="flex-1 border-t border-slate-200" />
        </div>

        {/* File upload */}
        <div
          onClick={() => fileRef.current?.click()}
          className="bg-white rounded-xl border-2 border-dashed border-slate-200 p-6 text-center cursor-pointer hover:border-[#1e3a5f] hover:bg-slate-50 transition-colors"
        >
          <input
            ref={fileRef}
            type="file"
            accept=".txt,.pdf"
            onChange={handleFileChange}
            className="hidden"
          />
          {file ? (
            <div className="space-y-0.5">
              <p className="text-sm font-semibold text-[#1e3a5f]">{file.name}</p>
              <p className="text-xs text-slate-400">
                {(file.size / 1024).toFixed(1)} KB · Click to change
              </p>
            </div>
          ) : (
            <div className="space-y-0.5">
              <p className="text-sm font-semibold text-slate-600">Upload transcript file</p>
              <p className="text-xs text-slate-400">.txt or .pdf · click to browse</p>
            </div>
          )}
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={!text.trim() && !file}
          className="w-full bg-[#1e3a5f] hover:bg-[#2d4f7a] disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed text-white py-3 px-6 rounded-xl font-semibold transition-colors"
        >
          Score Call
        </button>
      </form>
    </div>
  );
}
