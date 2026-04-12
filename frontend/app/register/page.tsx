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
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await registerNgo(form);
      saveToken(data.access_token, form.ngo_name);
      router.push("/dashboard");
    } catch (err) {
      setError("Registration failed. Email may already be registered.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div className="bg-white rounded-2xl border border-gray-200 p-8 w-full max-w-md">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Register NGO</h1>
        <p className="text-gray-500 text-sm mb-8">
          Create your organization account
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {[
            { key: "ngo_name", label: "NGO Name", type: "text", placeholder: "Sundarban Relief NGO" },
            { key: "email", label: "Email", type: "email", placeholder: "admin@ngo.org" },
            { key: "password", label: "Password", type: "password", placeholder: "••••••••" },
            { key: "contact_phone", label: "Contact Phone (optional)", type: "tel", placeholder: "+91 98765 43210" },
          ].map((field) => (
            <div key={field.key}>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {field.label}
              </label>
              <input
                type={field.type}
                value={form[field.key as keyof typeof form]}
                onChange={(e) => setForm({ ...form, [field.key]: e.target.value })}
                className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder={field.placeholder}
                required={field.key !== "contact_phone"}
              />
            </div>
          ))}

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 text-white py-3 rounded-xl font-medium hover:bg-green-700 transition disabled:opacity-50"
          >
            {loading ? "Registering..." : "Create Account"}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-6">
          Already registered?{" "}
          <Link href="/login" className="text-green-600 hover:underline">
            Login here
          </Link>
        </p>
      </div>
    </main>
  );
}