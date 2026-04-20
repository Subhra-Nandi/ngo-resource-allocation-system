"use client";
import { useState, useEffect, useRef } from "react";
import { submitRequest, getRequestStatus } from "@/lib/api";

const NEED_TYPES = ["FOOD", "MEDICAL", "SHELTER", "WASH", "OTHER"];
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type InputMode = "text" | "voice" | "photo";

export default function RequestPage() {
  const [mode, setMode] = useState<InputMode>("text");
  const [form, setForm] = useState({ description: "", need_type: "FOOD" });
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [gpsError, setGpsError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [requestId, setRequestId] = useState<string | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [error, setError] = useState("");

  const [recording, setRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach((t) => t.stop());
      };
      mediaRecorder.start();
      setRecording(true);
    } catch {
      setError("Microphone access denied. Please allow microphone access.");
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
      setError("Image too large. Max 10MB.");
      return;
    }
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      let data: any;
      if (mode === "voice" && audioBlob) {
        const formData = new FormData();
        formData.append("audio", audioBlob, "voice_note.webm");
        formData.append("need_type", form.need_type);
        formData.append("source", "affected_user");
        if (coords) {
          formData.append("lat", String(coords.lat));
          formData.append("lng", String(coords.lng));
        }
        const res = await fetch(`${API_URL}/requests/submit-audio`, {
          method: "POST",
          body: formData,
        });
        if (!res.ok) throw new Error("Failed to submit voice request");
        data = await res.json();
      } else if (mode === "photo" && imageFile) {
        const formData = new FormData();
        formData.append("image", imageFile);
        formData.append("need_type", form.need_type);
        formData.append("source", "affected_user");
        if (coords) {
          formData.append("lat", String(coords.lat));
          formData.append("lng", String(coords.lng));
        }
        const res = await fetch(`${API_URL}/requests/submit-image`, {
          method: "POST",
          body: formData,
        });
        if (!res.ok) throw new Error("Failed to submit photo request");
        data = await res.json();
      } else {
        if (!form.description || form.description.length < 10) {
          setError("Please describe your situation (at least 10 characters)");
          setSubmitting(false);
          return;
        }
        data = await submitRequest({
          ...form,
          lat: coords?.lat,
          lng: coords?.lng,
          source: "affected_user",
        });
      }
      setRequestId(data.request_id);
    } catch (err: any) {
      setError(err.message || "Failed to submit. Please try again.");
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
    setAudioBlob(null);
    setAudioUrl(null);
    setImageFile(null);
    setImagePreview(null);
    setMode("text");
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
              <span className="text-sm">AI is processing your request...</span>
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
                <div className="rounded-2xl overflow-hidden border border-green-200">
                  <div className="bg-green-600 px-5 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                        <span className="text-xl">🏥</span>
                      </div>
                      <div>
                        <p className="text-xs text-green-100 font-medium uppercase tracking-wide">
                          NGO Matched
                        </p>
                        <p className="text-white font-bold text-lg leading-tight">
                          {status.matched_ngo.ngo_name}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 divide-x divide-green-100 bg-green-50">
                    <div className="px-5 py-4 text-center">
                      <p className="text-3xl font-bold text-green-700">
                        {status.matched_ngo.eta_minutes}
                      </p>
                      <p className="text-xs text-green-600 font-medium mt-0.5">
                        minutes ETA
                      </p>
                    </div>
                    <div className="px-5 py-4 text-center">
                      <p className="text-3xl font-bold text-green-700">
                        {status.matched_ngo.distance_km}
                      </p>
                      <p className="text-xs text-green-600 font-medium mt-0.5">
                        km away
                      </p>
                    </div>
                  </div>

                  <div className="bg-white px-5 py-4 space-y-3">
                    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                      <span className="text-2xl">📦</span>
                      <div>
                        <p className="text-xs text-gray-400 font-medium">
                          Resource being sent
                        </p>
                        <p className="text-sm font-semibold text-gray-900">
                          {status.matched_ngo.resource_name}
                        </p>
                      </div>
                    </div>

                    {status.matched_ngo.depot_address && (
                      <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                        <span className="text-2xl">📍</span>
                        <div>
                          <p className="text-xs text-gray-400 font-medium">
                            Dispatching from
                          </p>
                          <p className="text-sm font-semibold text-gray-900">
                            {status.matched_ngo.depot_address}
                          </p>
                        </div>
                      </div>
                    )}

                    {status.matched_ngo.contact_phone && (
                      <a
                        href={`tel:${status.matched_ngo.contact_phone}`}
                        className="flex items-center gap-3 p-3 bg-green-50 rounded-xl border border-green-200 hover:bg-green-100 transition"
                      >
                        <span className="text-2xl">📞</span>
                        <div className="flex-1">
                          <p className="text-xs text-green-600 font-medium">
                            Call NGO directly
                          </p>
                          <p className="text-sm font-bold text-green-700">
                            {status.matched_ngo.contact_phone}
                          </p>
                        </div>
                        <span className="text-green-500 text-lg">→</span>
                      </a>
                    )}
                  </div>

                  <div className="bg-green-50 px-5 py-3 border-t border-green-100">
                    <p className="text-xs text-green-600 text-center">
                      Help is on the way. Stay at your location.
                    </p>
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
              className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-red-400"
            >
              {NEED_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              How do you want to describe your situation?
            </label>
            <div className="grid grid-cols-3 gap-2">
              {(
                [
                  { mode: "text", icon: "✍️", label: "Type" },
                  { mode: "voice", icon: "🎙️", label: "Voice" },
                  { mode: "photo", icon: "📷", label: "Photo" },
                ] as { mode: InputMode; icon: string; label: string }[]
              ).map((m) => (
                <button
                  key={m.mode}
                  type="button"
                  onClick={() => {
                    setMode(m.mode);
                    setError("");
                  }}
                  className={`flex flex-col items-center gap-1 py-3 rounded-xl border text-xs font-medium transition ${
                    mode === m.mode
                      ? "border-red-400 bg-red-50 text-red-600"
                      : "border-gray-200 text-gray-500 hover:border-gray-300"
                  }`}
                >
                  <span className="text-xl">{m.icon}</span>
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          {mode === "text" && (
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
                className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-red-400 resize-none"
                placeholder="e.g. 50 families need food, no water since 2 days..."
                required={mode === "text"}
                minLength={10}
              />
            </div>
          )}

          {mode === "voice" && (
            <div className="space-y-3">
              <label className="block text-sm font-medium text-gray-700">
                Record your voice note
              </label>
              {!audioUrl ? (
                <button
                  type="button"
                  onClick={recording ? stopRecording : startRecording}
                  className={`w-full py-8 rounded-xl border-2 border-dashed flex flex-col items-center gap-2 transition ${
                    recording
                      ? "border-red-400 bg-red-50 text-red-600"
                      : "border-gray-300 text-gray-500 hover:border-red-300 hover:text-red-500"
                  }`}
                >
                  <span className="text-4xl">
                    {recording ? "⏹️" : "🎙️"}
                  </span>
                  <span className="text-sm font-medium">
                    {recording
                      ? "Tap to stop recording"
                      : "Tap to start recording"}
                  </span>
                  {recording && (
                    <span className="flex items-center gap-1 text-xs">
                      <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                      Recording...
                    </span>
                  )}
                </button>
              ) : (
                <div className="border border-gray-200 rounded-xl p-4 space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="text-green-500">✓</span>
                    <span className="text-sm text-gray-700 font-medium">
                      Voice note recorded
                    </span>
                  </div>
                  <audio controls src={audioUrl} className="w-full h-10" />
                  <button
                    type="button"
                    onClick={() => {
                      setAudioBlob(null);
                      setAudioUrl(null);
                    }}
                    className="text-xs text-red-500 hover:underline"
                  >
                    Record again
                  </button>
                </div>
              )}
            </div>
          )}

          {mode === "photo" && (
            <div className="space-y-3">
              <label className="block text-sm font-medium text-gray-700">
                Upload a photo
              </label>
              {!imagePreview ? (
                <div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    capture="environment"
                    onChange={handleImageChange}
                    className="hidden"
                    id="photo-input"
                  />
                  <label
                    htmlFor="photo-input"
                    className="w-full py-8 rounded-xl border-2 border-dashed border-gray-300 flex flex-col items-center gap-2 cursor-pointer hover:border-red-300 hover:text-red-500 text-gray-500 transition"
                  >
                    <span className="text-4xl">📷</span>
                    <span className="text-sm font-medium">
                      Tap to take photo or upload
                    </span>
                    <span className="text-xs text-gray-400">
                      Max 10MB · JPG, PNG
                    </span>
                  </label>
                </div>
              ) : (
                <div className="border border-gray-200 rounded-xl p-3 space-y-2">
                  <img
                    src={imagePreview}
                    alt="Preview"
                    className="w-full rounded-lg object-cover max-h-48"
                  />
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500 truncate">
                      {imageFile?.name}
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        setImageFile(null);
                        setImagePreview(null);
                        if (fileInputRef.current)
                          fileInputRef.current.value = "";
                      }}
                      className="text-xs text-red-500 hover:underline ml-2 shrink-0"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              )}
              <div>
                <label className="block text-xs text-gray-500 mb-1">
                  Add description (optional)
                </label>
                <input
                  type="text"
                  value={form.description}
                  onChange={(e) =>
                    setForm({ ...form, description: e.target.value })
                  }
                  className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-sm text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-red-400"
                  placeholder="Any additional context..."
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your Location
            </label>
            {coords ? (
              <div className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-xl px-4 py-3">
                <span className="text-green-500">📍</span>
                <span className="text-sm text-green-700 font-medium">
                  {coords.lat.toFixed(5)}, {coords.lng.toFixed(5)}
                </span>
                <button
                  type="button"
                  onClick={() => setCoords(null)}
                  className="ml-auto text-xs text-gray-400 hover:text-red-500"
                >
                  ✕
                </button>
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

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={
              submitting ||
              (mode === "text" && form.description.length < 10) ||
              (mode === "voice" && !audioBlob) ||
              (mode === "photo" && !imageFile)
            }
            className="w-full bg-red-500 text-white py-3 rounded-xl font-medium hover:bg-red-600 transition disabled:opacity-40"
          >
            {submitting ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Submitting...
              </span>
            ) : (
              "Submit Request"
            )}
          </button>
        </form>
      </div>
    </main>
  );
}