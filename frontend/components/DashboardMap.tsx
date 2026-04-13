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
    }, 30000);
    return () => clearInterval(interval);
  }, [token]);

  return (
    <MapContainer
      center={[22.5, 88.3]}
      zoom={8}
      style={{ height: "300px", width: "100%", borderRadius: "12px" }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      />
      {pins.map((pin) => (
        <CircleMarker
          key={pin.id}
          center={[pin.lat, pin.lng]}
          radius={Math.max(6, (pin.severity || 1) * 4)}
          color={pin.color}
          fillColor={pin.color}
          fillOpacity={0.7}
          weight={2}
        >
          <Popup>
            <div style={{ fontSize: "12px", lineHeight: "1.6" }}>
              <strong>{pin.need_type}</strong> — Severity {pin.severity}/5
              <br />
              {pin.location_name && <span>{pin.location_name}<br /></span>}
              <span style={{ color: "#666" }}>{pin.description}</span>
              {pin.eta_minutes && (
                <><br /><span style={{ color: "green" }}>ETA: {pin.eta_minutes} min</span></>
              )}
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}