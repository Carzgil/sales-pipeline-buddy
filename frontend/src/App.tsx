import { useState } from "react";
import BriefCard from "./components/BriefCard";
import PostCallEvaluation from "./components/PostCallEvaluation";
import RestaurantSearch from "./components/RestaurantSearch";
import ScorecardView from "./components/ScorecardView";
import type { AppView, BriefData, RestaurantInfo, ScorecardData } from "./types";

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

  const steps = [
    { key: "brief", label: "1. Pre-Call Brief", active: ["brief", "postcall", "scorecard"] },
    { key: "postcall", label: "2. Post-Call Evaluation", active: ["postcall", "scorecard"] },
    { key: "scorecard", label: "3. Scorecard", active: ["scorecard"] },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-[#1e3a5f] text-white shadow-md">
        <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center font-bold text-sm tracking-tight">
              O
            </div>
            <div>
              <h1 className="text-base font-semibold leading-tight">Sales Call Buddy</h1>
              <p className="text-xs text-blue-200 leading-tight">Owner.com · Internal Tool</p>
            </div>
          </div>
          {view !== "search" && (
            <button
              onClick={handleReset}
              className="text-sm text-blue-200 hover:text-white transition-colors"
            >
              ← New Search
            </button>
          )}
        </div>
      </header>

      {/* Progress bar */}
      {view !== "search" && (
        <div className="bg-white border-b border-slate-200">
          <div className="max-w-3xl mx-auto px-6 py-3 flex items-center gap-3 text-sm">
            {steps.map((step, i) => (
              <span key={step.key} className="flex items-center gap-3">
                {i > 0 && <span className="text-slate-300">→</span>}
                <span
                  className={
                    step.active.includes(view)
                      ? "font-semibold text-[#1e3a5f]"
                      : "text-slate-400"
                  }
                >
                  {step.label}
                </span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Content */}
      <main className="max-w-3xl mx-auto px-6 py-8">
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
