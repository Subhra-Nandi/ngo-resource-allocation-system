"use client";
import { useEffect, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import { getMapData } from "@/lib/api";
import "leaflet/dist/leaflet.css";

interface Props {
  token: string;
}

export default function DashboardMap({ token }: Props) {
  const [pins, setPins] = useState<any[]>([]);

  useEffect(() => {
    getMapData(token).then(setPins).catch(console.error);
    const interval = setInterval(() => {
      getMapData(token).then(setPins).catch(console.error);
    }, 15000);
    return () => clearInterval(interval);
  }, [token]);

  return (
    <div>
      {/* Legend */}
      <div className="flex gap-4 mb-3">
        {[
          { color: "#E24B4A", label: "Critical (4-5)" },
          { color: "#EF9F27", label: "Moderate (3)" },
          { color: "#639922", label: "Low (1-2)" },
        ].map((l) => (
          <div key={l.label} className="flex items-center gap-1.5">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: l.color }}
            />
            <span className="text-xs text-gray-500">{l.label}</span>
          </div>
        ))}
        <span className="text-xs text-gray-400 ml-auto">
          {pins.length} active request{pins.length !== 1 ? "s" : ""}
        </span>
      </div>

      <MapContainer
        center={[22.5, 88.3]}
        zoom={8}
        style={{ height: "320px", width: "100%", borderRadius: "12px" }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
        />
        {pins.map((pin) => (
          <CircleMarker
            key={pin.id}
            center={[pin.lat, pin.lng]}
            radius={Math.max(8, (pin.severity || 3) * 4)}
            pathOptions={{
              color: pin.color,
              fillColor: pin.color,
              fillOpacity: 0.75,
              weight: 2,
            }}
          >
            <Popup>
              <div style={{ fontSize: "12px", lineHeight: "1.7", minWidth: "160px" }}>
                <div style={{ fontWeight: "600", marginBottom: "4px" }}>
                  {pin.need_type} — Severity {pin.severity}/5
                </div>
                {pin.location_name && (
                  <div style={{ color: "#374151" }}>{pin.location_name}</div>
                )}
                <div style={{ color: "#6b7280", fontSize: "11px" }}>
                  {pin.description?.slice(0, 80)}
                  {pin.description?.length > 80 ? "..." : ""}
                </div>
                <div style={{ color: "#6b7280", fontSize: "11px", marginTop: "4px" }}>
                  Status: <strong>{pin.status}</strong>
                </div>
                {pin.eta_minutes && (
                  <div style={{ color: "#16a34a", fontWeight: "500" }}>
                    ETA: {pin.eta_minutes} min
                  </div>
                )}
              </div>
            </Popup>
          </CircleMarker>
        ))}

        {pins.length === 0 && (
          <div style={{
            position: "absolute", top: "50%", left: "50%",
            transform: "translate(-50%, -50%)", zIndex: 1000,
            background: "white", padding: "8px 16px",
            borderRadius: "8px", fontSize: "13px", color: "#6b7280"
          }}>
            No active requests on map
          </div>
        )}
      </MapContainer>
    </div>
  );
}