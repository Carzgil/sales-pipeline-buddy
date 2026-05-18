const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function generateBrief(
  restaurantName: string,
  city: string,
  websiteUrl?: string
) {
  const res = await fetch(`${API_URL}/api/brief`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      restaurant_name: restaurantName,
      city: city,
      website_url: websiteUrl || null,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export async function scoreTranscript(
  transcriptText: string | null,
  file: File | null,
  restaurantName: string
) {
  const form = new FormData();
  if (transcriptText) form.append("transcript_text", transcriptText);
  if (file) form.append("file", file);
  form.append("restaurant_name", restaurantName);

  const res = await fetch(`${API_URL}/api/score`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed (${res.status})`);
  }
  return res.json();
}
