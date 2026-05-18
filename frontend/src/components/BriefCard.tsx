import type { BriefData, RestaurantInfo } from "../types";

interface Props {
  restaurant: RestaurantInfo;
  brief: BriefData;
  onProceedToPostCall: () => void;
}

const FIT_CONFIG = {
  green: {
    badge: "bg-green-100 text-green-800 border-green-200",
    dot: "bg-green-500",
    banner: "bg-green-50 border-green-200 text-green-800",
    label: "Strong Fit",
  },
  yellow: {
    badge: "bg-yellow-100 text-yellow-800 border-yellow-200",
    dot: "bg-yellow-400",
    banner: "bg-yellow-50 border-yellow-200 text-yellow-800",
    label: "Proceed — Verify",
  },
  red: {
    badge: "bg-red-100 text-red-800 border-red-200",
    dot: "bg-red-500",
    banner: "bg-red-50 border-red-200 text-red-800",
    label: "Likely Non-Fit",
  },
};

export default function BriefCard({ restaurant, brief, onProceedToPostCall }: Props) {
  const fit = FIT_CONFIG[brief.fit_signal] ?? FIT_CONFIG.yellow;

  return (
    <div className="space-y-4">
      {/* Restaurant header + fit badge */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800">{restaurant.name}</h2>
          <p className="text-slate-400 text-sm">{restaurant.city}</p>
        </div>
        <div
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-semibold border flex-shrink-0 ${fit.badge}`}
        >
          <div className={`w-2 h-2 rounded-full ${fit.dot}`} />
          {fit.label}
        </div>
      </div>

      {/* Fit reason banner */}
      <div className={`px-4 py-3 rounded-xl border text-sm font-medium ${fit.banner}`}>
        {brief.fit_reason}
      </div>

      {/* Brief sections */}
      <div className="grid gap-3">
        <BriefSection
          icon="🔍"
          title="Online Visibility"
          content={brief.online_visibility}
        />
        <BriefSection
          icon="🛵"
          title="Delivery Setup"
          content={brief.delivery_setup}
        />
        <BriefSection
          icon="💬"
          title="Suggested Opening"
          content={brief.opening_suggestion}
          highlight
        />
      </div>

      {/* CTA */}
      <div className="pt-2">
        <button
          onClick={onProceedToPostCall}
          className="w-full bg-orange-500 hover:bg-orange-600 text-white py-3 px-6 rounded-xl font-semibold transition-colors"
        >
          Proceed to Post-Call Evaluation →
        </button>
        <p className="text-center text-xs text-slate-400 mt-2">
          Make your call first — come back here after to score it
        </p>
      </div>
    </div>
  );
}

function BriefSection({
  icon,
  title,
  content,
  highlight = false,
}: {
  icon: string;
  title: string;
  content: string;
  highlight?: boolean;
}) {
  return (
    <div
      className={`rounded-xl p-4 border ${
        highlight
          ? "bg-orange-50 border-orange-200"
          : "bg-white border-slate-200"
      }`}
    >
      <div className="flex items-center gap-2 mb-1.5">
        <span>{icon}</span>
        <h3
          className={`text-sm font-semibold ${
            highlight ? "text-orange-800" : "text-slate-700"
          }`}
        >
          {title}
        </h3>
      </div>
      <p
        className={`text-sm leading-relaxed ${
          highlight ? "text-orange-900 italic font-medium" : "text-slate-600"
        }`}
      >
        {content}
      </p>
    </div>
  );
}
