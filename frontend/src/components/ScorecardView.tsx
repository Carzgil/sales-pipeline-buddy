import type { RestaurantInfo, ScorecardData } from "../types";

interface Props {
  restaurant: RestaurantInfo;
  scorecard: ScorecardData;
  onNewCall: () => void;
}

export default function ScorecardView({ restaurant, scorecard, onNewCall }: Props) {
  const passCount = scorecard.dimensions.filter((d) => d.passed).length;
  const total = scorecard.dimensions.length;
  const pct = Math.round((passCount / total) * 100);

  const scoreColor =
    passCount >= 4 ? "bg-green-500" : passCount >= 2 ? "bg-yellow-400" : "bg-red-500";

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Call Scorecard</h2>
          <p className="text-slate-400 text-sm mt-0.5">
            {restaurant.name} · {restaurant.city}
          </p>
        </div>
        <div className="text-right flex-shrink-0">
          <div className="text-3xl font-bold text-[#1e3a5f]">
            {passCount}/{total}
          </div>
          <div className="text-xs text-slate-400">dimensions passed</div>
        </div>
      </div>

      {/* Score bar */}
      <div className="h-2.5 bg-slate-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${scoreColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Dimensions */}
      <div className="space-y-3">
        {scorecard.dimensions.map((dim, i) => (
          <div key={i} className="bg-white rounded-xl border border-slate-200 p-4">
            <div className="flex items-start gap-3">
              <div
                className={`mt-0.5 w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold ${
                  dim.passed
                    ? "bg-green-100 text-green-700"
                    : "bg-red-100 text-red-600"
                }`}
              >
                {dim.passed ? "✓" : "✗"}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-semibold text-slate-700">{dim.name}</span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                      dim.passed
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-600"
                    }`}
                  >
                    {dim.passed ? "Pass" : "Fail"}
                  </span>
                </div>
                {dim.evidence && dim.evidence !== "Not found in transcript" ? (
                  <blockquote className="mt-2 pl-3 border-l-2 border-slate-200 text-xs text-slate-500 italic leading-relaxed">
                    "{dim.evidence}"
                  </blockquote>
                ) : !dim.passed ? (
                  <p className="mt-1 text-xs text-slate-400 italic">
                    Not found in transcript
                  </p>
                ) : null}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Coaching note */}
      <div className="bg-[#1e3a5f] rounded-xl p-5 text-white">
        <div className="flex items-start gap-3">
          <span className="text-xl flex-shrink-0">💡</span>
          <div>
            <p className="text-xs font-semibold text-blue-200 uppercase tracking-widest mb-2">
              Most important thing to do differently next time
            </p>
            <p className="text-sm leading-relaxed">{scorecard.coaching_note}</p>
          </div>
        </div>
      </div>

      {/* Actions */}
      <button
        onClick={onNewCall}
        className="w-full bg-orange-500 hover:bg-orange-600 text-white py-3 px-6 rounded-xl font-semibold transition-colors"
      >
        New Call
      </button>
    </div>
  );
}
