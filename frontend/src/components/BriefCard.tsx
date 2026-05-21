import type { BriefData, RestaurantInfo } from "../types";

interface Props {
  restaurant: RestaurantInfo;
  brief: BriefData;
  onProceedToPostCall: () => void;
}

const FIT_CONFIG = {
  green: {
    topBorder: "border-t-green-600",
    dot: "bg-green-600",
    badge: "bg-green-600 text-white border-green-600",
    banner: "bg-green-50 border-green-200 text-green-900",
    label: "Confirmed Fit",
  },
  yellow: {
    topBorder: "border-t-amber-400",
    dot: "bg-amber-400",
    badge: "bg-amber-400 text-amber-950 border-amber-400",
    banner: "bg-amber-50 border-amber-200 text-amber-900",
    label: "Verify in Discovery",
  },
  red: {
    topBorder: "border-t-red-600",
    dot: "bg-red-600",
    badge: "bg-red-600 text-white border-red-600",
    banner: "bg-red-50 border-red-200 text-red-900",
    label: "Likely Non-Fit",
  },
};

export default function BriefCard({ restaurant, brief, onProceedToPostCall }: Props) {
  const fit = FIT_CONFIG[brief.fit_signal] ?? FIT_CONFIG.yellow;

  return (
    <div className="space-y-4">
      {/* Restaurant header */}
      <div
        className={`bg-white border border-edge border-t-2 ${fit.topBorder} rounded-xl p-6 shadow-sm animate-fade-up`}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="font-serif text-4xl text-ink" style={{ fontWeight: 600 }}>
              {restaurant.name}
            </h2>
            <p className="font-mono text-[10px] tracking-[0.2em] text-ink-dim uppercase mt-1">
              {restaurant.city}
            </p>
          </div>
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-[10px] font-mono tracking-[0.12em] uppercase flex-shrink-0 mt-1 font-medium ${fit.badge}`}
          >
            <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${fit.dot}`} />
            {fit.label}
          </div>
        </div>

        <div className={`mt-4 px-4 py-3 rounded-lg border text-sm font-medium ${fit.banner}`}>
          {brief.fit_reason}
        </div>
      </div>

      {/* Brief sections */}
      <div
        className="bg-white border border-edge rounded-xl overflow-hidden shadow-sm animate-fade-up"
        style={{ animationDelay: "100ms" }}
      >
        <BriefSection title="Online Visibility" content={brief.online_visibility} />
        <div className="border-t border-edge" />
        <BriefSection title="Delivery Setup" content={brief.delivery_setup} />
      </div>

      {/* Opening suggestion */}
      <div
        className="bg-flame-dim border border-flame/20 rounded-xl p-5 animate-fade-up"
        style={{ animationDelay: "200ms" }}
      >
        <p className="font-mono text-[10px] tracking-[0.2em] text-flame uppercase mb-3 font-medium">
          Suggested Opening
        </p>
        <p className="font-serif italic text-xl text-ink leading-snug" style={{ fontWeight: 400 }}>
          "{brief.opening_suggestion}"
        </p>
      </div>

      {/* CTA */}
      <div className="animate-fade-up" style={{ animationDelay: "280ms" }}>
        <button
          onClick={onProceedToPostCall}
          style={{ backgroundColor: "#e87020" }}
          className="w-full hover:opacity-90 text-white py-3 px-6 rounded-xl font-semibold text-sm transition-opacity shadow-sm"
        >
          Proceed to Post-Call Evaluation →
        </button>
        <p className="text-center text-xs text-ink-faint mt-2">
          Make your call first — come back here after to score it
        </p>
      </div>

      {/* AI disclaimer */}
      <p className="text-center font-mono text-[9px] tracking-[0.12em] text-ink-faint uppercase animate-fade-up" style={{ animationDelay: "340ms" }}>
        AI-generated — verify all information before use
      </p>
    </div>
  );
}

function BriefSection({ title, content }: { title: string; content: string }) {
  return (
    <div className="px-5 py-4">
      <p className="font-mono text-[10px] tracking-[0.2em] text-ink-dim uppercase mb-2 font-medium">
        {title}
      </p>
      <p className="text-sm text-ink leading-relaxed">{content}</p>
    </div>
  );
}
