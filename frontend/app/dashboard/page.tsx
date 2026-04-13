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
    depot_lat: 22.5,
    depot_lng: 88.3,
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
    } catch { showMsg("Failed to add resource."); }
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

        {/* Toast message */}
        {msg && (
          <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-3 flex justify-between items-center">
            <span className="text-sm text-green-700">{msg}</span>
            <button onClick={() => setMsg("")} className="text-green-400 hover:text-green-600 ml-4">✕</button>
          </div>
        )}

        {/* Summary cards */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: "Pending", value: summary.pending_tasks, color: "text-amber-600" },
              { label: "Dispatched", value: summary.dispatched_tasks, color: "text-blue-600" },
              { label: "Completed", value: summary.completed_tasks, color: "text-green-600" },
              { label: "Total Stock", value: summary.total_stock_units, color: "text-purple-600" },
            ].map((c) => (
              <div key={c.label} className="bg-white rounded-xl border border-gray-200 p-4">
                <p className="text-xs text-gray-400 mb-1">{c.label}</p>
                <p className={`text-2xl font-bold ${c.color}`}>{c.value}</p>
              </div>
            ))}
          </div>
        )}

        {/* Live Map */}
        {token && (
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-sm font-semibold text-gray-700 mb-3">
              Live Request Map
            </p>
            <DashboardMap token={token} />
          </div>
        )}

        {/* Tabs */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="flex border-b border-gray-100">
            {(["tasks", "inventory", "add"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 py-3 text-sm font-medium transition ${
                  activeTab === tab
                    ? "border-b-2 border-green-600 text-green-600 bg-green-50"
                    : "text-gray-500 hover:text-gray-800"
                }`}
              >
                {tab === "tasks"
                  ? `Tasks (${tasks.length})`
                  : tab === "inventory"
                  ? `Inventory (${inventory.length})`
                  : "Add Stock"}
              </button>
            ))}
          </div>

          <div className="p-5">
            {/* Tasks */}
            {activeTab === "tasks" && (
              <div className="space-y-3">
                {tasks.length === 0 ? (
                  <div className="text-center py-10">
                    <p className="text-4xl mb-2">✅</p>
                    <p className="text-gray-400 text-sm">No pending tasks</p>
                  </div>
                ) : (
                  tasks.map((task) => (
                    <div
                      key={task.request_id}
                      className="border border-gray-200 rounded-xl p-4"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-wrap gap-1.5 mb-2">
                            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${severityColor(task.severity)}`}>
                              Sev {task.severity}/5
                            </span>
                            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                              {task.need_type}
                            </span>
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              task.status === "dispatched"
                                ? "bg-green-100 text-green-700"
                                : "bg-gray-100 text-gray-600"
                            }`}>
                              {task.status}
                            </span>
                          </div>
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {task.location_name || "Unknown location"}
                          </p>
                          <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                            {task.description}
                          </p>
                        </div>
                        <div className="text-right text-xs text-gray-400 ml-3 shrink-0">
                          <p>{task.distance_km} km</p>
                          <p>{task.eta_minutes} min</p>
                          <p className="text-gray-500 mt-0.5">
                            {task.affected_count} people
                          </p>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        {task.status === "matched" && (
                          <>
                            <button
                              onClick={() => handleAccept(task.request_id)}
                              className="flex-1 bg-green-600 text-white py-2 rounded-lg text-xs font-medium hover:bg-green-700 transition"
                            >
                              Accept & Dispatch
                            </button>
                            <button
                              onClick={() => handleDecline(task.request_id)}
                              className="flex-1 border border-gray-300 text-gray-600 py-2 rounded-lg text-xs hover:bg-gray-50 transition"
                            >
                              Decline
                            </button>
                          </>
                        )}
                        {task.status === "dispatched" && (
                          <button
                            onClick={() => handleComplete(task.request_id)}
                            className="flex-1 bg-blue-600 text-white py-2 rounded-lg text-xs font-medium hover:bg-blue-700 transition"
                          >
                            Mark Complete
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* Inventory */}
            {activeTab === "inventory" && (
              <div className="space-y-3">
                {inventory.length === 0 ? (
                  <div className="text-center py-10">
                    <p className="text-4xl mb-2">📦</p>
                    <p className="text-gray-400 text-sm">No resources added yet</p>
                    <button
                      onClick={() => setActiveTab("add")}
                      className="mt-3 text-green-600 text-sm hover:underline"
                    >
                      Add your first resource →
                    </button>
                  </div>
                ) : (
                  inventory.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center justify-between border border-gray-200 rounded-xl p-4"
                    >
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {item.name}
                        </p>
                        <p className="text-xs text-gray-400">
                          {item.category} · {item.depot_name || item.depot_address}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className={`text-xl font-bold ${item.low_stock ? "text-red-500" : "text-green-600"}`}>
                          {item.quantity}
                        </p>
                        <p className="text-xs text-gray-400">{item.unit}</p>
                        {item.low_stock && (
                          <p className="text-xs text-red-500 font-medium">⚠ Low stock</p>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* Add resource */}
            {activeTab === "add" && (
              <form onSubmit={handleAddResource} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Category
                    </label>
                    <select
                      value={resForm.category}
                      onChange={(e) => setResForm({ ...resForm, category: e.target.value })}
                      className="w-full border border-gray-300 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                    >
                      {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Resource Name
                    </label>
                    <input
                      value={resForm.name}
                      onChange={(e) => setResForm({ ...resForm, name: e.target.value })}
                      className="w-full border border-gray-300 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                      placeholder="Rice 5kg pack"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Quantity
                    </label>
                    <input
                      type="number"
                      min={1}
                      value={resForm.quantity}
                      onChange={(e) => setResForm({ ...resForm, quantity: Number(e.target.value) })}
                      className="w-full border border-gray-300 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Unit
                    </label>
                    <input
                      value={resForm.unit}
                      onChange={(e) => setResForm({ ...resForm, unit: e.target.value })}
                      className="w-full border border-gray-300 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                      placeholder="packs / kits / litres"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Depot Latitude
                    </label>
                    <input
                      type="number"
                      step="any"
                      value={resForm.depot_lat}
                      onChange={(e) => setResForm({ ...resForm, depot_lat: Number(e.target.value) })}
                      className="w-full border border-gray-300 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                      placeholder="22.16"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Depot Longitude
                    </label>
                    <input
                      type="number"
                      step="any"
                      value={resForm.depot_lng}
                      onChange={(e) => setResForm({ ...resForm, depot_lng: Number(e.target.value) })}
                      className="w-full border border-gray-300 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                      placeholder="88.75"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Depot Name
                  </label>
                  <input
                    value={resForm.depot_name}
                    onChange={(e) => setResForm({ ...resForm, depot_name: e.target.value })}
                    className="w-full border border-gray-300 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                    placeholder="Gosaba Depot"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Depot Address
                  </label>
                  <input
                    value={resForm.depot_address}
                    onChange={(e) => setResForm({ ...resForm, depot_address: e.target.value })}
                    className="w-full border border-gray-300 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                    placeholder="Gosaba, South 24 Parganas"
                  />
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
      </div>
    </div>
  );
}