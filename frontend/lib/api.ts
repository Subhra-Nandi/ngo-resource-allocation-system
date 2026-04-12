const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Auth ─────────────────────────────────────────────────────
export async function loginNgo(email: string, password: string) {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error("Invalid email or password");
  return res.json();
}

export async function registerNgo(data: {
  ngo_name: string;
  email: string;
  password: string;
  contact_phone?: string;
}) {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Registration failed");
  return res.json();
}

// ── Dashboard ─────────────────────────────────────────────────
export async function getDashboardSummary(token: string) {
  const res = await fetch(`${API_URL}/dashboard/summary`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch summary");
  return res.json();
}

export async function getMapData(token: string) {
  const res = await fetch(`${API_URL}/dashboard/map-data`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch map data");
  return res.json();
}

export async function getInventory(token: string) {
  const res = await fetch(`${API_URL}/dashboard/inventory`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch inventory");
  return res.json();
}

export async function getAllRequests(token: string) {
  const res = await fetch(`${API_URL}/dashboard/requests/all`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch requests");
  return res.json();
}

// ── Tasks ─────────────────────────────────────────────────────
export async function getPendingTasks(token: string) {
  const res = await fetch(`${API_URL}/ngo/tasks`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch tasks");
  return res.json();
}

export async function acceptTask(token: string, reportId: string) {
  const res = await fetch(`${API_URL}/ngo/tasks/${reportId}/accept`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to accept task");
  return res.json();
}

export async function declineTask(token: string, reportId: string) {
  const res = await fetch(`${API_URL}/ngo/tasks/${reportId}/decline`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to decline task");
  return res.json();
}

export async function completeTask(token: string, reportId: string) {
  const res = await fetch(`${API_URL}/ngo/tasks/${reportId}/complete`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to complete task");
  return res.json();
}

// ── Resources ─────────────────────────────────────────────────
export async function addResource(token: string, data: {
  category: string;
  name: string;
  quantity: number;
  unit?: string;
  depot_lat: number;
  depot_lng: number;
  depot_address?: string;
  depot_name?: string;
}) {
  const res = await fetch(`${API_URL}/ngo/resources`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to add resource");
  return res.json();
}

// ── User request ──────────────────────────────────────────────
export async function submitRequest(data: {
  description: string;
  need_type?: string;
  lat?: number;
  lng?: number;
  source: string;
}) {
  const res = await fetch(`${API_URL}/requests/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to submit request");
  return res.json();
}

export async function getRequestStatus(requestId: string) {
  const res = await fetch(`${API_URL}/requests/${requestId}/status`);
  if (!res.ok) throw new Error("Failed to get status");
  return res.json();
}