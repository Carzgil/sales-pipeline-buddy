import { useEffect, useRef, useState } from "react";
import { generateBrief } from "../api";
import type { BriefData, RestaurantInfo } from "../types";

interface Props {
  onBriefGenerated: (restaurant: RestaurantInfo, brief: BriefData) => void;
}

declare global {
  interface Window {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    google: any;
    initGooglePlaces: () => void;
  }
}

const LOADING_MESSAGES = [
  "Checking search rankings...",
  "Looking for delivery platform presence...",
  "Researching local competitors...",
  "Generating your pre-call brief...",
];

export default function RestaurantSearch({ onBriefGenerated }: Props) {
  const [showManual, setShowManual] = useState(false);
  const [name, setName] = useState("");
  const [city, setCity] = useState("");
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState(LOADING_MESSAGES[0]);
  const [error, setError] = useState<string | null>(null);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const autocompleteRef = useRef<any>(null);
  const PLACES_KEY = import.meta.env.VITE_GOOGLE_PLACES_API_KEY;

  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!PLACES_KEY || showManual) return;
    if (document.getElementById("gmaps-script")) return;

    const script = document.createElement("script");
    script.id = "gmaps-script";
    script.src = `https://maps.googleapis.com/maps/api/js?key=${PLACES_KEY}&libraries=places&loading=async`;
    script.async = true;
    script.onerror = () => setShowManual(true);
    document.head.appendChild(script);
  }, [PLACES_KEY, showManual]);

  useEffect(() => {
    if (!PLACES_KEY || showManual || !containerRef.current) return;

    const waitForGoogle = setInterval(() => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const g = (window as any).google;
      if (!g?.maps?.places?.PlaceAutocompleteElement) return;
      clearInterval(waitForGoogle);

      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const widget = new (g.maps.places.PlaceAutocompleteElement as any)({
          types: ["establishment"],
        });
        widget.style.cssText =
          "width:100%;--gmp-mat-text-field-active-indicator-color:#1e3a5f;";
        containerRef.current!.appendChild(widget);
        autocompleteRef.current = widget;

        widget.addEventListener("gmp-placeselect", async (e: CustomEvent) => {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const place = (e as any).place;
          await place.fetchFields({
            fields: ["displayName", "addressComponents", "websiteURI"],
          });
          const components: { types: string[]; longText: string; shortText: string }[] =
            place.addressComponents ?? [];
          const cityComp = components.find((c) => c.types.includes("locality"));
          const stateComp = components.find((c) =>
            c.types.includes("administrative_area_level_1")
          );
          const resolvedCity = [cityComp?.longText, stateComp?.shortText]
            .filter(Boolean)
            .join(", ");
          submitBrief({
            name: place.displayName,
            city: resolvedCity,
            website_url: place.websiteURI,
          });
        });
      } catch {
        setShowManual(true);
      }
    }, 200);

    return () => clearInterval(waitForGoogle);
  }, [PLACES_KEY, showManual]);

  const submitBrief = async (info: RestaurantInfo) => {
    if (!info.name || !info.city) {
      setError("Please enter both restaurant name and city.");
      return;
    }
    setLoading(true);
    setError(null);

    let msgIdx = 0;
    const interval = setInterval(() => {
      msgIdx = (msgIdx + 1) % LOADING_MESSAGES.length;
      setLoadingMsg(LOADING_MESSAGES[msgIdx]);
    }, 2500);

    try {
      const result = await generateBrief(info.name, info.city, info.website_url);
      clearInterval(interval);
      onBriefGenerated(info, result.brief);
    } catch (err) {
      clearInterval(interval);
      setError(err instanceof Error ? err.message : "Failed to generate brief. Please try again.");
      setLoading(false);
    }
  };

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    submitBrief({ name, city, website_url: url || undefined });
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[420px] gap-6">
        <div className="w-12 h-12 border-4 border-[#1e3a5f] border-t-transparent rounded-full animate-spin" />
        <div className="text-center">
          <p className="text-lg font-semibold text-slate-700">{loadingMsg}</p>
          <p className="text-sm text-slate-400 mt-1">Takes about 15 seconds</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[420px]">
      <div className="w-full max-w-lg">
        <div className="text-center mb-10">
          <h2 className="text-2xl font-bold text-slate-800 mb-2">Prepare for your call</h2>
          <p className="text-slate-500 text-sm">
            Search for a restaurant to generate your pre-call intelligence brief
          </p>
        </div>

        {!showManual ? (
          <div className="space-y-4">
            {PLACES_KEY ? (
              <div ref={containerRef} className="w-full" />
            ) : (
              <div className="text-sm text-amber-700 bg-amber-50 px-4 py-3 rounded-xl border border-amber-200">
                Google Places not configured — use manual entry below.
              </div>
            )}
            <button
              onClick={() => setShowManual(true)}
              className="w-full text-sm text-slate-400 hover:text-slate-600 py-1 transition-colors"
            >
              Can't find it? Enter manually →
            </button>
          </div>
        ) : (
          <form onSubmit={handleManualSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Restaurant name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Tony's Pizza"
                required
                className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1e3a5f] focus:border-transparent bg-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">City</label>
              <input
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="e.g. Austin, TX"
                required
                className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1e3a5f] focus:border-transparent bg-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Website URL{" "}
                <span className="text-slate-400 font-normal">(optional)</span>
              </label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://..."
                className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1e3a5f] focus:border-transparent bg-white"
              />
            </div>
            <button
              type="submit"
              className="w-full bg-[#1e3a5f] hover:bg-[#2d4f7a] text-white py-3 px-6 rounded-xl font-semibold transition-colors"
            >
              Generate Pre-Call Brief
            </button>
            {PLACES_KEY && (
              <button
                type="button"
                onClick={() => setShowManual(false)}
                className="w-full text-sm text-slate-400 hover:text-slate-600 py-1 transition-colors"
              >
                ← Back to search
              </button>
            )}
          </form>
        )}

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
