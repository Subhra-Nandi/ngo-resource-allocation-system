"use client";
import { useState, useEffect } from "react";
import { submitRequest, getRequestStatus } from "@/lib/api";

const NEED_TYPES = ["FOOD", "MEDICAL", "SHELTER", "WASH", "OTHER"];

export default function RequestPage() {
  const [form, setForm] = useState({ description: "", need_type: "FOOD" });
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [gpsError, setGpsError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [requestId, setRequestId] = useState<string | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [error, setError] = useState("");

  const getLocation = () => {
    if (!navigator.geolocation) {
      setGpsError("GPS not supported on this device");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setGpsError("");
      },
      () => setGpsError("Could not get location. Please allow GPS access.")
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const data = await submitRequest({
        ...form,
        lat: coords?.lat,
        lng: coords?.lng,
        source: "affected_user",
      });
      setRequestId(data.request_id);
    } catch {
      setError("Failed to submit. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  useEffect(() => {
    if (!requestId) return;
    const interval = setInterval(async () => {
      try {
        const s = await getRequestStatus(requestId);
        setStatus(s);
        if (["matched", "waitlist", "flagged", "dispatched"].includes(s.status)) {
          clearInterval(interval);
        }
      } catch {}
    }, 3000);
    return () => clearInterval(interval);
  }, [requestId]);

  const reset = () => {
    setRequestId(null);
    setStatus(null);
    setForm({ description: "", need_type: "FOOD" });
    setCoords(null);
  };

  if (requestId) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="bg-white rounded-2xl border border-gray-200 p-8 w-full max-w-md">
          <h2 className="text-xl font-bold text-gray-900 mb-6 text-center">
            Request Submitted
          </h2>

          {!status && (
            <div className="flex items-center justify-center gap-3 text-gray-500 py-8">
              <div className="w-5 h-5 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
              <span className="text-sm">Processing your request...</span>
            </div>
          )}

          {status && (
            <div className="space-y-4">
              <div
                className={`rounded-xl p-4 ${
                  status.status === "matched" || status.status === "dispatched"
                    ? "bg-green-50 border border-green-200"
                    : status.status === "waitlist"
                    ? "bg-amber-50 border border-amber-200"
                    : "bg-gray-50 border border-gray-200"
                }`}
              >
                <p className="font-semibold text-gray-900 capitalize">
                  {status.status}
                </p>
                <p className="text-sm text-gray-600 mt-1">{status.message}</p>
              </div>

              {status.matched_ngo && (
                <div className="bg-green-50 rounded-xl p-4 border border-green-200">
                  <p className="font-semibold text-green-800 mb-3">
                    NGO Matched!
                  </p>
                  <div className="space-y-2 text-sm">
                    {[
                      ["NGO", status.matched_ngo.ngo_name],
                      ["Resource", status.matched_ngo.resource_name],
                      ["ETA", `${status.matched_ngo.eta_minutes} minutes`],
                      ["Distance", `${status.matched_ngo.distance_km} km`],
                      ["From", status.matched_ngo.depot_address],
                      ["Phone", status.matched_ngo.contact_phone],
                    ]
                      .filter(([, v]) => v)
                      .map(([label, value]) => (
                        <div key={label} className="flex justify-between">
                          <span className="text-gray-500">{label}</span>
                          <span className="font-medium text-right">
                            {value}
                          </span>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              <button
                onClick={reset}
                className="w-full border border-gray-300 text-gray-700 py-3 rounded-xl text-sm hover:bg-gray-50 transition"
              >
                Submit Another Request
              </button>
            </div>
          )}
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div className="bg-white rounded-2xl border border-gray-200 p-8 w-full max-w-md">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center text-xl">
            🆘
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Request Help</h1>
            <p className="text-xs text-gray-500">
              We will find the nearest NGO for you
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              What do you need?
            </label>
            <select
              value={form.need_type}
              onChange={(e) => setForm({ ...form, need_type: e.target.value })}
              className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-red-400"
            >
              {NEED_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Describe your situation
            </label>
            <textarea
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
              rows={4}
              className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-red-400 resize-none"
              placeholder="e.g. 50 families need food, no water since 2 days..."
              required
              minLength={10}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your Location
            </label>
            {coords ? (
              <div className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-xl px-4 py-3">
                <span className="text-green-500">📍</span>
                <span className="text-sm text-green-700">
                  {coords.lat.toFixed(4)}, {coords.lng.toFixed(4)}
                </span>
              </div>
            ) : (
              <button
                type="button"
                onClick={getLocation}
                className="w-full border-2 border-dashed border-gray-300 rounded-xl py-3 text-sm text-gray-500 hover:border-red-300 hover:text-red-500 transition"
              >
                📍 Allow GPS Location Access
              </button>
            )}
            {gpsError && (
              <p className="text-red-500 text-xs mt-1">{gpsError}</p>
            )}
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-red-500 text-white py-3 rounded-xl font-medium hover:bg-red-600 transition disabled:opacity-50"
          >
            {submitting ? "Submitting..." : "Submit Request"}
          </button>
        </form>
      </div>
    </main>
  );
}