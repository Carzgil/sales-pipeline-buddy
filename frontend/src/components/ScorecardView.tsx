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

  const barColor = passCount >= 4 ? "bg-ember" : passCount >= 2 ? "bg-sand" : "bg-ash";
  const scoreTextColor = passCount >= 4 ? "text-ember" : passCount >= 2 ? "text-sand" : "text-ash";

  return (
    <div className="space-y-5 animate-fade-up">
      {/* Header */}
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="font-mono text-[10px] tracking-[0.2em] text-flame uppercase mb-1 font-medium">
            Call Scorecard
          </p>
          <h2 className="font-serif text-3xl text-ink" style={{ fontWeight: 600 }}>
            {restaurant.name}
          </h2>
          <p className="font-mono text-[10px] tracking-[0.15em] text-ink-dim uppercase mt-1">
            {restaurant.city}
          </p>
        </div>
        <div className="text-right flex-shrink-0">
          <div className={`font-serif text-5xl font-semibold ${scoreTextColor}`} style={{ lineHeight: 1 }}>
            {passCount}<span className="text-ink-faint text-4xl">/</span>{total}
          </div>
          <p className="font-mono text-[10px] tracking-[0.12em] text-ink-dim uppercase mt-1">
            dimensions passed
          </p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-edge rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Dimensions */}
      <div className="space-y-2.5">
        {scorecard.dimensions.map((dim, i) => (
          <div
            key={i}
            className={`bg-white border border-edge border-l-4 rounded-xl p-4 shadow-sm ${
              dim.passed ? "border-l-ember" : "border-l-ash"
            }`}
          >
            <div className="flex items-start gap-3">
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold mt-0.5 text-white ${
                  dim.passed ? "bg-green-600" : "bg-red-600"
                }`}
              >
                {dim.passed ? "✓" : "✗"}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-semibold text-ink">{dim.name}</span>
                  <span
                    className={`font-mono text-[9px] tracking-[0.15em] uppercase px-2 py-0.5 rounded-full border font-medium ${
                      dim.passed
                        ? "bg-green-100 text-green-800 border-green-200"
                        : "bg-red-100 text-red-700 border-red-200"
                    }`}
                  >
                    {dim.passed ? "Pass" : "Fail"}
                  </span>
                </div>
                {dim.evidence && dim.evidence !== "Not found in transcript" ? (
                  <blockquote className="mt-2 pl-3 border-l-2 border-edge text-xs text-ink-dim italic leading-relaxed">
                    "{dim.evidence}"
                  </blockquote>
                ) : !dim.passed ? (
                  <p className="mt-1 text-xs text-ink-faint italic">Not found in transcript</p>
                ) : null}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Coaching note */}
      <div className="bg-flame-dim border-2 border-flame/30 rounded-xl p-6">
        <p className="font-mono text-[10px] tracking-[0.2em] text-flame uppercase mb-3 font-semibold">
          Most important thing to do differently next time
        </p>
        <p className="text-base font-semibold text-ink leading-relaxed">{scorecard.coaching_note}</p>
      </div>

      <button
        onClick={onNewCall}
        style={{ backgroundColor: "#e87020" }}
        className="w-full hover:opacity-90 text-white py-3 px-6 rounded-xl font-semibold text-sm transition-opacity shadow-sm"
      >
        Start New Call
      </button>

      {/* AI disclaimer */}
      <p className="text-center font-mono text-[9px] tracking-[0.12em] text-ink-faint uppercase">
        AI-generated — verify all information before use
      </p>
    </div>
  );
}
