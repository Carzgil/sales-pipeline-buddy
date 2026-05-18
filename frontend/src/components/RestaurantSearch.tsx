import { useEffect, useRef, useState } from "react";
import { generateBrief } from "../api";
import type { BriefData, RestaurantInfo } from "../types";

interface Props {
  onBriefGenerated: (restaurant: RestaurantInfo, brief: BriefData) => void;
}

const LOADING_MESSAGES = [
  "Checking search rankings...",
  "Looking for delivery platform presence...",
  "Researching local competitors...",
  "Generating your pre-call brief...",
];

export default function RestaurantSearch({ onBriefGenerated }: Props) {
  const [showManual, setShowManual] = useState(false);
  const [query, setQuery] = useState("");
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [predictions, setPredictions] = useState<any[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [name, setName] = useState("");
  const [city, setCity] = useState("");
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState(LOADING_MESSAGES[0]);
  const [error, setError] = useState<string | null>(null);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const autocompleteServiceRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const placesServiceRef = useRef<any>(null);
  const sessionTokenRef = useRef<unknown>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const PLACES_KEY = import.meta.env.VITE_GOOGLE_PLACES_API_KEY;

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
    if (!PLACES_KEY || showManual) return;

    const poll = setInterval(() => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const g = (window as any).google;
      if (!g?.maps?.places?.AutocompleteService) return;
      clearInterval(poll);
      autocompleteServiceRef.current = new g.maps.places.AutocompleteService();
      const div = document.createElement("div");
      placesServiceRef.current = new g.maps.places.PlacesService(div);
      sessionTokenRef.current = new g.maps.places.AutocompleteSessionToken();
    }, 200);

    return () => clearInterval(poll);
  }, [PLACES_KEY, showManual]);

  const handleQueryChange = (value: string) => {
    setQuery(value);
    setError(null);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (value.length < 2) {
      setPredictions([]);
      setShowDropdown(false);
      return;
    }
    debounceRef.current = setTimeout(() => {
      autocompleteServiceRef.current?.getPlacePredictions(
        { input: value, types: ["establishment"], sessionToken: sessionTokenRef.current },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (results: any[], status: string) => {
          if (status === "OK" && results) {
            setPredictions(results.slice(0, 5));
            setShowDropdown(true);
          } else {
            setPredictions([]);
          }
        }
      );
    }, 300);
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleSelectPrediction = (prediction: any) => {
    setQuery(prediction.description);
    setPredictions([]);
    setShowDropdown(false);

    placesServiceRef.current?.getDetails(
      {
        placeId: prediction.place_id,
        fields: ["name", "address_components", "website"],
        sessionToken: sessionTokenRef.current,
      },
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (place: any, status: string) => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const g = (window as any).google;
        // Reset session token after getDetails closes the session
        sessionTokenRef.current = new g.maps.places.AutocompleteSessionToken();

        if (status !== "OK" || !place) {
          setError("Could not load place details — try again or enter manually.");
          return;
        }
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const comps: any[] = place.address_components ?? [];
        const cityComp = comps.find((c) => c.types.includes("locality"));
        const stateComp = comps.find((c) => c.types.includes("administrative_area_level_1"));
        const resolvedCity = [cityComp?.long_name, stateComp?.short_name]
          .filter(Boolean)
          .join(", ");
        submitBrief({ name: place.name, city: resolvedCity, website_url: place.website });
      }
    );
  };

  const submitBrief = async (info: RestaurantInfo) => {
    if (!info.name || !info.city) {
      setError("Please enter both restaurant name and city.");
      return;
    }
    setLoading(true);
    setError(null);
    setPredictions([]);
    setShowDropdown(false);

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
          <div className="space-y-3">
            <div className="relative">
              <input
                type="text"
                value={query}
                onChange={(e) => handleQueryChange(e.target.value)}
                onBlur={() => setTimeout(() => setShowDropdown(false), 150)}
                onFocus={() => predictions.length > 0 && setShowDropdown(true)}
                autoComplete="off"
                placeholder="Search for a restaurant..."
                className="w-full px-4 py-3 text-base border border-slate-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-[#1e3a5f] focus:border-transparent bg-white"
              />
              {showDropdown && predictions.length > 0 && (
                <ul className="absolute z-50 w-full mt-1 bg-white border border-slate-200 rounded-xl shadow-lg overflow-hidden">
                  {predictions.map((p) => (
                    <li
                      key={p.place_id}
                      onMouseDown={() => handleSelectPrediction(p)}
                      className="px-4 py-3 hover:bg-slate-50 cursor-pointer text-sm border-b border-slate-100 last:border-0"
                    >
                      <span className="font-medium text-slate-800">
                        {p.structured_formatting?.main_text}
                      </span>
                      <span className="text-slate-400 ml-1">
                        {p.structured_formatting?.secondary_text}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

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
                <span className="text-slate-400 font-normal">(optional — improves delivery detection)</span>
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
