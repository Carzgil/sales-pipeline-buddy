import { useEffect, useRef, useState } from "react";
import { ApiError, generateBrief } from "../api";
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
  const [notRestaurant, setNotRestaurant] = useState(false);

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
      { placeId: prediction.place_id, fields: ["name", "address_components", "website"], sessionToken: sessionTokenRef.current },
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (place: any, status: string) => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const g = (window as any).google;
        sessionTokenRef.current = new g.maps.places.AutocompleteSessionToken();
        if (status !== "OK" || !place) {
          setError("Could not load place details — try again or enter manually.");
          return;
        }
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const comps: any[] = place.address_components ?? [];
        const cityComp = comps.find((c) => c.types.includes("locality"));
        const stateComp = comps.find((c) => c.types.includes("administrative_area_level_1"));
        const resolvedCity = [cityComp?.long_name, stateComp?.short_name].filter(Boolean).join(", ");
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
    setNotRestaurant(false);
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
      const isNotRestaurant = err instanceof ApiError && err.status === 422;
      setNotRestaurant(isNotRestaurant);
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
      <div className="flex flex-col items-center justify-center min-h-[480px] gap-5">
        <div className="text-center space-y-4 animate-fade-up">
          <p className="font-mono text-xs tracking-[0.18em] text-ink-dim uppercase">
            {loadingMsg}
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
        </div>
      </div>
    );
  }

  const inputClass =
    "w-full px-4 py-3 bg-white border border-edge rounded-lg text-ink text-sm placeholder-ink-faint focus:outline-none focus:ring-2 focus:ring-flame/25 focus:border-flame/50 transition-colors";

  const labelClass =
    "block font-mono text-[10px] tracking-[0.18em] text-ink-dim uppercase mb-1.5";

  return (
    <div className="flex flex-col items-center justify-center min-h-[480px]">
      <div className="w-full max-w-lg">
        {/* Eyebrow */}
        <p className="font-mono text-[10px] tracking-[0.25em] text-flame uppercase text-center mb-2 animate-fade-up">
          Intelligence Brief
        </p>

        {/* Hero heading */}
        <h2
          className="font-serif italic text-5xl text-ink text-center mb-10 animate-fade-up"
          style={{ animationDelay: "60ms", fontWeight: 300 }}
        >
          Prepare for your call
        </h2>

        {/* Search / manual */}
        <div className="animate-fade-up" style={{ animationDelay: "120ms" }}>
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
                  className={inputClass}
                />
                {showDropdown && predictions.length > 0 && (
                  <ul className="absolute z-50 w-full mt-1 bg-white border border-edge rounded-lg shadow-lg overflow-hidden">
                    {predictions.map((p) => (
                      <li
                        key={p.place_id}
                        onMouseDown={() => handleSelectPrediction(p)}
                        className="px-4 py-3 hover:bg-paper cursor-pointer text-sm border-b border-edge last:border-0 transition-colors"
                      >
                        <span className="font-medium text-ink">
                          {p.structured_formatting?.main_text}
                        </span>
                        <span className="text-ink-dim ml-1 text-xs">
                          {p.structured_formatting?.secondary_text}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <button
                onClick={() => setShowManual(true)}
                className="w-full text-sm text-ink-dim hover:text-ink py-1 transition-colors"
              >
                Can't find it? Enter manually →
              </button>
            </div>
          ) : (
            <form onSubmit={handleManualSubmit} className="space-y-4">
              <div>
                <label className={labelClass}>Restaurant name</label>
                <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Tony's Pizza" required className={inputClass} />
              </div>
              <div>
                <label className={labelClass}>City</label>
                <input type="text" value={city} onChange={(e) => setCity(e.target.value)} placeholder="e.g. Austin, TX" required className={inputClass} />
              </div>
              <div>
                <label className={labelClass}>
                  Website URL{" "}
                  <span className="text-ink-faint normal-case tracking-normal font-sans" style={{ fontSize: "0.7rem" }}>
                    (optional — improves delivery detection)
                  </span>
                </label>
                <input type="url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://..." className={inputClass} />
              </div>
              <button
                type="submit"
                className="w-full bg-flame hover:bg-flame/90 text-white py-3 px-6 rounded-lg font-semibold text-sm transition-colors shadow-sm"
              >
                Generate Pre-Call Brief
              </button>
              {PLACES_KEY && (
                <button type="button" onClick={() => setShowManual(false)} className="w-full text-sm text-ink-dim hover:text-ink py-1 transition-colors">
                  ← Back to search
                </button>
              )}
            </form>
          )}
        </div>

        {/* Error */}
        {error && (
          <div
            className={`mt-5 p-3 border rounded-lg text-sm animate-fade-up ${
              notRestaurant
                ? "bg-sand-dim border-sand/30 text-sand"
                : "bg-ash-dim border-ash/30 text-ash"
            }`}
          >
            <span className="font-mono text-[10px] tracking-wider uppercase mr-2">
              {notRestaurant ? "Not found" : "Error"}
            </span>
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
