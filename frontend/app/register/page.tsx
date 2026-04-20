"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { registerNgo } from "@/lib/api";
import { saveToken } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    ngo_name: "",
    email: "",
    password: "",
    contact_phone: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (!form.contact_phone.trim()) {
      setError("Phone number is required for NGO registration");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await registerNgo(form);
      saveToken(data.access_token, form.ngo_name);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const strength =
    form.password.length === 0 ? 0
    : form.password.length < 6 ? 1
    : form.password.length < 8 ? 2
    : form.password.length < 12 ? 3
    : 4;

  const strengthLabel = ["", "Too short", "Weak", "Good", "Strong"];
  const strengthColor = ["", "bg-red-400", "bg-amber-400", "bg-amber-400", "bg-green-500"];

  return (
    <main className="min-h-screen bg-gradient-to-br from-green-50 to-gray-100 flex items-center justify-center p-6">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 w-full max-w-md">

        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl">🌿</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Register your NGO</h1>
          <p className="text-gray-500 text-sm mt-1">
            Join the platform to manage resources and respond to requests
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">

          {/* NGO Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              NGO Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={form.ngo_name}
              onChange={(e) => setForm({ ...form, ngo_name: e.target.value })}
              className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm text-gray-900 bg-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="e.g. Sundarban Relief NGO"
              required
            />
          </div>

          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email address <span className="text-red-500">*</span>
            </label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm text-gray-900 bg-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="admin@ngo.org"
              required
              autoComplete="email"
            />
          </div>

          {/* Phone — now mandatory */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contact Phone <span className="text-red-500">*</span>
            </label>
            <div className="flex gap-2">
              <div className="flex items-center border border-gray-300 rounded-xl px-3 bg-gray-50">
                <span className="text-sm text-gray-500 whitespace-nowrap">🇮🇳 +91</span>
              </div>
              <input
                type="tel"
                value={form.contact_phone}
                onChange={(e) => setForm({ ...form, contact_phone: e.target.value })}
                className="flex-1 border border-gray-300 rounded-xl px-4 py-3 text-sm text-gray-900 bg-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                placeholder="98765 43210"
                required
              />
            </div>
            <p className="text-xs text-gray-400 mt-1">
              Shown to users when NGO is matched to their request
            </p>
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full border border-gray-300 rounded-xl px-4 py-3 pr-16 text-sm text-gray-900 bg-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                placeholder="Min 8 characters"
                required
                minLength={8}
                autoComplete="new-password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-xs text-gray-400 hover:text-gray-700 font-medium transition"
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>

            {/* Strength bar */}
            {form.password.length > 0 && (
              <div className="mt-2 space-y-1">
                <div className="flex gap-1">
                  {[1, 2, 3, 4].map((l) => (
                    <div
                      key={l}
                      className={`h-1 flex-1 rounded-full transition-all ${
                        strength >= l ? strengthColor[strength] : "bg-gray-200"
                      }`}
                    />
                  ))}
                </div>
                <p className="text-xs text-gray-400">{strengthLabel[strength]}</p>
              </div>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 flex gap-2 items-start">
              <span className="text-red-500 mt-0.5">⚠</span>
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 text-white py-3.5 rounded-xl font-semibold hover:bg-green-700 active:scale-95 transition disabled:opacity-50 mt-2"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Creating account...
              </span>
            ) : (
              "Create Account"
            )}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-6">
          Already registered?{" "}
          <Link href="/login" className="text-green-600 hover:underline font-medium">
            Login here
          </Link>
        </p>
      </div>
    </main>
  );
}