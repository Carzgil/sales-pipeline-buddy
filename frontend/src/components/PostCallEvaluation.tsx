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
      <div className="flex flex-col items-center justify-center min-h-[480px] gap-5">
        <div className="text-center space-y-4 animate-fade-up">
          <p className="font-mono text-xs tracking-[0.18em] text-ink-dim uppercase">
            Scoring your call...
          </p>
          <div className="flex gap-2 justify-center">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-2 h-2 rounded-full bg-flame animate-dot-pulse"
                style={{ animationDelay: `${i * 220}ms` }}
              />
            ))}
          </div>
          <p className="font-mono text-[10px] tracking-[0.15em] text-ink-faint uppercase">
            Evaluating 5 behavioral dimensions
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-up">
      <div>
        <p className="font-mono text-[10px] tracking-[0.2em] text-flame uppercase mb-1 font-medium">
          Post-Call Evaluation
        </p>
        <h2 className="font-serif text-3xl text-ink" style={{ fontWeight: 600 }}>
          {restaurant.name}
        </h2>
        <p className="font-mono text-[10px] tracking-[0.15em] text-ink-dim uppercase mt-1">
          {restaurant.city}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="bg-white rounded-xl border border-edge p-4 shadow-sm">
          <label className="block font-mono text-[10px] tracking-[0.18em] text-ink-dim uppercase mb-2 font-medium">
            Paste transcript
          </label>
          <textarea
            value={text}
            onChange={(e) => { setText(e.target.value); setFile(null); }}
            placeholder="Paste your call transcript here..."
            rows={10}
            className="w-full px-3 py-2.5 text-sm bg-paper border border-edge rounded-lg text-ink placeholder-ink-faint resize-y focus:outline-none focus:ring-2 focus:ring-flame/25 focus:border-flame/50 transition-colors leading-relaxed"
          />
        </div>

        <div className="flex items-center gap-3">
          <div className="flex-1 border-t border-edge" />
          <span className="text-xs text-ink-faint font-semibold uppercase tracking-wide">or</span>
          <div className="flex-1 border-t border-edge" />
        </div>

        <div
          onClick={() => fileRef.current?.click()}
          className="bg-white rounded-xl border-2 border-dashed border-edge p-6 text-center cursor-pointer hover:border-flame/40 hover:bg-flame-dim transition-colors shadow-sm"
        >
          <input ref={fileRef} type="file" accept=".txt,.pdf" onChange={handleFileChange} className="hidden" />
          {file ? (
            <div className="space-y-0.5">
              <p className="text-sm font-semibold text-ink">{file.name}</p>
              <p className="font-mono text-[10px] tracking-wider text-ink-dim uppercase">
                {(file.size / 1024).toFixed(1)} KB · Click to change
              </p>
            </div>
          ) : (
            <div className="space-y-0.5">
              <p className="text-sm font-semibold text-ink-dim">Upload transcript file</p>
              <p className="font-mono text-[10px] tracking-wider text-ink-faint uppercase">.txt or .pdf · click to browse</p>
            </div>
          )}
        </div>

        {error && (
          <div className="p-3 bg-ash-dim border border-ash/30 rounded-lg text-sm text-ash">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={!text.trim() && !file}
          style={{ backgroundColor: "#e87020" }}
          className="w-full hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed text-white py-3 px-6 rounded-xl font-semibold text-sm transition-opacity shadow-sm"
        >
          Score Call
        </button>
      </form>
    </div>
  );
}
