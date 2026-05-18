export interface RestaurantInfo {
  name: string;
  city: string;
  website_url?: string;
}

export interface BriefData {
  online_visibility: string;
  delivery_setup: string;
  fit_signal: "green" | "yellow" | "red";
  fit_reason: string;
  opening_suggestion: string;
}

export interface ScorecardDimension {
  name: string;
  passed: boolean;
  evidence: string;
}

export interface ScorecardData {
  dimensions: ScorecardDimension[];
  coaching_note: string;
}

export type AppView = "search" | "brief" | "postcall" | "scorecard";
