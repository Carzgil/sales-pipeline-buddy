import { useState } from "react";
import BriefCard from "./components/BriefCard";
import PostCallEvaluation from "./components/PostCallEvaluation";
import RestaurantSearch from "./components/RestaurantSearch";
import ScorecardView from "./components/ScorecardView";
import type { AppView, BriefData, RestaurantInfo, ScorecardData } from "./types";

const STEPS = [
  { key: "brief", label: "Pre-Call Brief", active: ["brief", "postcall", "scorecard"] },
  { key: "postcall", label: "Post-Call Eval", active: ["postcall", "scorecard"] },
  { key: "scorecard", label: "Scorecard", active: ["scorecard"] },
];

export default function App() {
  const [view, setView] = useState<AppView>("search");
  const [restaurant, setRestaurant] = useState<RestaurantInfo | null>(null);
  const [brief, setBrief] = useState<BriefData | null>(null);
  const [scorecard, setScorecard] = useState<ScorecardData | null>(null);

  const handleBriefGenerated = (info: RestaurantInfo, data: BriefData) => {
    setRestaurant(info);
    setBrief(data);
    setView("brief");
  };

  const handleScorecardGenerated = (data: ScorecardData) => {
    setScorecard(data);
    setView("scorecard");
  };

  const handleReset = () => {
    setView("search");
    setRestaurant(null);
    setBrief(null);
    setScorecard(null);
  };

  return (
    <div className="min-h-screen bg-paper text-ink">
      {/* Header — navy, same familiar Owner brand */}
      <header className="bg-navy shadow-sm">
        <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 bg-flame rounded-sm flex items-center justify-center font-bold text-sm text-white font-mono">
              O
            </div>
            <div>
              <h1 className="text-sm font-semibold text-white leading-tight tracking-wide">
                Sales Call Buddy
              </h1>
              <p className="font-mono text-[10px] tracking-[0.15em] text-white/50 uppercase leading-tight">
                Owner.com · Internal Tool
              </p>
            </div>
          </div>
          {view !== "search" && (
            <button
              onClick={handleReset}
              className="text-sm text-white hover:text-white/80 transition-colors font-semibold"
            >
              ← New Search
            </button>
          )}
        </div>
      </header>

      {/* Step progress */}
      {view !== "search" && (
        <div className="bg-white border-b border-edge">
          <div className="max-w-3xl mx-auto px-6 py-3 flex items-center gap-3">
            {STEPS.map((step, i) => (
              <div key={step.key} className="flex items-center gap-3">
                {i > 0 && <span className="text-edge font-mono text-xs">→</span>}
                <span
                  className={`font-mono text-[10px] tracking-[0.15em] uppercase font-medium transition-colors ${
                    step.active.includes(view) ? "text-flame" : "text-ink-faint"
                  }`}
                >
                  {i + 1}. {step.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Content */}
      <main className="max-w-3xl mx-auto px-6 py-10">
        {view === "search" && (
          <RestaurantSearch onBriefGenerated={handleBriefGenerated} />
        )}
        {view === "brief" && brief && restaurant && (
          <BriefCard
            restaurant={restaurant}
            brief={brief}
            onProceedToPostCall={() => setView("postcall")}
          />
        )}
        {view === "postcall" && restaurant && (
          <PostCallEvaluation
            restaurant={restaurant}
            onScorecardGenerated={handleScorecardGenerated}
          />
        )}
        {view === "scorecard" && scorecard && restaurant && (
          <ScorecardView
            restaurant={restaurant}
            scorecard={scorecard}
            onNewCall={handleReset}
          />
        )}
      </main>
    </div>
  );
}
