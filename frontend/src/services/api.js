const BASE = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? "http://127.0.0.1:5000/api" : "");

export async function api(path, options = {}) {
  if (!BASE) {
    throw new Error("APMS backend is not connected yet. Configure VITE_API_BASE_URL after the Flask API is deployed.");
  }
  const response = await fetch(BASE + path, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}
