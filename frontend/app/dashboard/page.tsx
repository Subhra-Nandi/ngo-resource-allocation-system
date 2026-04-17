"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import {
  getDashboardSummary,
  getPendingTasks,
  getInventory,
  acceptTask,
  declineTask,
  completeTask,
  addResource,
} from "@/lib/api";
import { getToken, getNgoName, clearToken } from "@/lib/auth";

const DashboardMap = dynamic(() => import("@/components/DashboardMap"), {
  ssr: false,
  loading: () => (
    <div className="h-64 bg-gray-100 rounded-xl flex items-center justify-center">
      <p className="text-gray-400 text-sm">Loading map...</p>
    </div>
  ),
});

const CATEGORIES = ["FOOD", "MEDICAL", "SHELTER", "WASH", "OTHER"];

export default function DashboardPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [ngoName, setNgoName] = useState<string | null>(null);
  const [summary, setSummary] = useState<any>(null);
  const [tasks, setTasks] = useState<any[]>([]);
  const [inventory, setInventory] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<"tasks" | "inventory" | "add">("tasks");
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState("");

  const [resForm, setResForm] = useState({
    category: "FOOD",
    name: "",
    quantity: 100,
    unit: "packs",
    depot_lat: "" as any,
    depot_lng: "" as any,
    depot_name: "",
    depot_address: "",
  });

  useEffect(() => {
    const t = getToken();
    const n = getNgoName();
    if (!t) { router.push("/login"); return; }
    setToken(t);
    setNgoName(n);
    loadData(t);
  }, []);

  const loadData = async (t: string) => {
    try {
      const [s, tk, inv] = await Promise.all([
        getDashboardSummary(t),
        getPendingTasks(t),
        getInventory(t),
      ]);
      setSummary(s);
      setTasks(tk);
      setInventory(inv);
    } catch {
      router.push("/login");
    } finally {
      setLoading(false);
    }
  };

  const showMsg = (m: string) => {
    setMsg(m);
    setTimeout(() => setMsg(""), 4000);
  };

  const handleAccept = async (id: string) => {
    if (!token) return;
    try {
      const res = await acceptTask(token, id);
      showMsg(`Dispatched ${res.units_dispatched} units. Stock left: ${res.remaining_stock}`);
      loadData(token);
    } catch (e: any) { showMsg(e.message); }
  };

  const handleDecline = async (id: string) => {
    if (!token) return;
    try {
      await declineTask(token, id);
      showMsg("Task declined.");
      loadData(token);
    } catch (e: any) { showMsg(e.message); }
  };

  const handleComplete = async (id: string) => {
    if (!token) return;
    try {
      await completeTask(token, id);
      showMsg("Task marked complete!");
      loadData(token);
    } catch (e: any) { showMsg(e.message); }
  };

  const handleAddResource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    try {
      await addResource(token, resForm);
      showMsg("Resource added successfully!");
      loadData(token);
      setActiveTab("inventory");
    } catch {
      showMsg("Failed to add resource.");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-gray-500 text-sm">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const severityColor = (s: number) =>
    s >= 4 ? "bg-red-100 text-red-700" :
    s >= 3 ? "bg-amber-100 text-amber-700" :
    "bg-green-100 text-green-700";

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-gray-900">NGO Dashboard</h1>
            <p className="text-xs text-gray-500">{summary?.ngo_name || ngoName}</p>
          </div>
          <button
            onClick={() => { clearToken(); router.push("/login"); }}
            className="text-sm text-gray-400 hover:text-red-500 transition"
          >
            Logout
          </button>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-6 py-6 space-y-5">

        {/* Add Resource */}
        {activeTab === "add" && (
          <form onSubmit={handleAddResource} className="space-y-4">

            <div className="grid grid-cols-2 gap-4">

              {/* Depot location with GPS */}
              <div className="col-span-2">
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Depot Location
                </label>

                <button
                  type="button"
                  onClick={() => {
                    navigator.geolocation.getCurrentPosition(
                      (pos) => setResForm({
                        ...resForm,
                        depot_lat: parseFloat(pos.coords.latitude.toFixed(6)),
                        depot_lng: parseFloat(pos.coords.longitude.toFixed(6)),
                      }),
                      () => alert("Could not get location")
                    );
                  }}
                  className="w-full border-2 border-dashed border-gray-300 rounded-xl py-2.5 text-sm text-gray-500 hover:border-green-400 hover:text-green-600 transition mb-2"
                >
                  📍 Use My Current Location
                </button>

                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="number"
                    step="any"
                    value={resForm.depot_lat}
                    onChange={(e) =>
                      setResForm({ ...resForm, depot_lat: Number(e.target.value) })
                    }
                    className="w-full border border-gray-300 rounded-xl px-3 py-2.5 text-sm"
                    placeholder="Latitude e.g. 22.5726"
                    required
                  />

                  <input
                    type="number"
                    step="any"
                    value={resForm.depot_lng}
                    onChange={(e) =>
                      setResForm({ ...resForm, depot_lng: Number(e.target.value) })
                    }
                    className="w-full border border-gray-300 rounded-xl px-3 py-2.5 text-sm"
                    placeholder="Longitude e.g. 88.3639"
                    required
                  />
                </div>

                {resForm.depot_lat && resForm.depot_lng && (
                  <p className="text-xs text-green-600 mt-1">
                    📍 {resForm.depot_lat}, {resForm.depot_lng}
                  </p>
                )}
              </div>

            </div>

            <button
              type="submit"
              className="w-full bg-green-600 text-white py-3 rounded-xl text-sm font-medium hover:bg-green-700 transition"
            >
              Add Resource
            </button>
          </form>
        )}
      </div>
    </div>
  );
}