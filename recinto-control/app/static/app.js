/**
 * Script de actualización en vivo para el Dashboard de Recinto Control
 */
document.addEventListener("DOMContentLoaded", () => {
    const devicePill = document.getElementById("device-pill");
    const deviceStatusText = document.getElementById("device-status-text");
    
    const kpiInterrupted = document.getElementById("kpi-ir-interrupted");
    const kpiCleared = document.getElementById("kpi-ir-cleared");
    const kpiPersonas = document.getElementById("kpi-personas-visibles");

    const valDeviceId = document.getElementById("val-device-id");
    const valIp = document.getElementById("val-ip");
    const valFirmware = document.getElementById("val-firmware");
    const valRssi = document.getElementById("val-rssi");
    const valLastSeen = document.getElementById("val-last-seen");

    const tableBody = document.getElementById("events-table-body");
    const eventsCountBadge = document.getElementById("events-count-badge");

    async function fetchDashboard() {
        try {
            const resp = await fetch("/api/v1/dashboard/summary");
            if (!resp.ok) return;

            const data = await resp.json();

            // Estado del dispositivo
            if (data.online) {
                devicePill.className = "device-status-pill online";
                deviceStatusText.textContent = "ESP32 En Línea";
            } else {
                devicePill.className = "device-status-pill offline";
                deviceStatusText.textContent = data.device_id ? "ESP32 Desconectado" : "Sin Dispositivos";
            }

            // KPIs
            kpiInterrupted.textContent = data.ir_interrupted_count;
            kpiCleared.textContent = data.ir_cleared_count;
            kpiPersonas.textContent = data.personas_visibles !== null ? data.personas_visibles : "--";

            // Telemetría
            valDeviceId.textContent = data.device_id || "N/A";
            valIp.textContent = data.ip_address || "N/A";
            valFirmware.textContent = data.firmware_version || "N/A";
            valRssi.textContent = data.wifi_rssi !== null ? `${data.wifi_rssi} dBm` : "N/A";
            valLastSeen.textContent = data.last_seen_at ? new Date(data.last_seen_at).toLocaleTimeString() : "N/A";

            // Tabla de eventos
            eventsCountBadge.textContent = `${data.recent_events.length} recientes`;

            if (data.recent_events.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="5" class="empty-state">No se han registrado eventos aún.</td></tr>`;
            } else {
                tableBody.innerHTML = data.recent_events.map(ev => {
                    const tagClass = ev.event_type === "IR_INTERRUPTED" ? "tag-interrupted" : "tag-cleared";
                    const originClass = ev.is_simulated ? "origin-sim" : "origin-real";
                    const originText = ev.is_simulated ? "SIMULADO" : "FIRMWARE";
                    const timeStr = new Date(ev.occurred_at).toLocaleTimeString();

                    return `
                        <tr>
                            <td class="font-mono">${timeStr}</td>
                            <td>${ev.sensor_id}</td>
                            <td><span class="tag-badge ${tagClass}">${ev.event_type}</span></td>
                            <td><span class="origin-badge ${originClass}">${originText}</span></td>
                            <td class="font-mono text-muted">${ev.event_id.slice(0, 16)}...</td>
                        </tr>
                    `;
                }).join("");
            }

        } catch (err) {
            console.warn("Fallo temporal de consulta:", err);
            devicePill.className = "device-status-pill offline";
            deviceStatusText.textContent = "Error Conexión API";
        }
    }

    setInterval(fetchDashboard, 2000);
    fetchDashboard();
});
