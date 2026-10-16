/**
 * Cliente JavaScript para el panel de monitoreo ESP32-S3 + YOLO
 */
document.addEventListener("DOMContentLoaded", () => {
    const streamImg = document.getElementById("camera-stream");
    const toggleRaw = document.getElementById("toggle-raw");
    const personCountElem = document.getElementById("person-count");
    const inferenceTimeElem = document.getElementById("inference-time");
    const framesTotalElem = document.getElementById("frames-total");
    const cameraBadge = document.getElementById("camera-badge");
    const cameraStatusText = document.getElementById("camera-status-text");
    const captureTimeElem = document.getElementById("capture-time");
    const fpsValElem = document.getElementById("fps-val");
    const detectorStatusElem = document.getElementById("detector-status");

    // DeepSeek elements
    const btnDeepSeek = document.getElementById("btn-deepseek-analyze");
    const btnDeepSeekText = document.getElementById("btn-deepseek-text");
    const deepseekResultBox = document.getElementById("deepseek-result-box");
    const deepseekOutputContent = document.getElementById("deepseek-output-content");

    // IR Sensor elements
    const irStatusBox = document.getElementById("ir-status-box");
    const irStateText = document.getElementById("ir-state-text");
    const irSubText = document.getElementById("ir-sub-text");
    const irActivationsCount = document.getElementById("ir-activations-count");
    const irLastTime = document.getElementById("ir-last-time");
    const irEventsList = document.getElementById("ir-events-list");

    // RFID elements (Fase 2)
    const rfidStatusBox = document.getElementById("rfid-status-box");
    const rfidStatusText = document.getElementById("rfid-status-text");
    const rfidSubText = document.getElementById("rfid-sub-text");
    const rfidLastUid = document.getElementById("rfid-last-uid");
    const rfidCardHolder = document.getElementById("rfid-card-holder");
    const rfidReadsCount = document.getElementById("rfid-reads-count");
    const rfidLastTime = document.getElementById("rfid-last-time");
    const rfidCardsList = document.getElementById("rfid-cards-list");

    let isFetching = false;
    let pollInterval = 1000; // ms para respuesta ágil

    // Actualiza telemetría y recarga fotograma
    async function updateDashboard() {
        if (isFetching) return;
        isFetching = true;

        try {
            const res = await fetch("/api/status");
            if (res.ok) {
                const data = await res.json();

                // Estado de cámara
                if (data.camera.connected) {
                    cameraBadge.className = "status-pill status-connected";
                    cameraStatusText.textContent = "ESP32 Conectado";
                } else {
                    cameraBadge.className = "status-pill status-disconnected";
                    cameraStatusText.textContent = data.camera.error 
                        ? (data.camera.error.length > 25 ? "Error Cámara" : data.camera.error)
                        : "Desconectado";
                }

                // Estado del Lector RFID (Fase 2)
                if (data.rfid && rfidStatusBox) {
                    const rfid = data.rfid;
                    if (rfid.last_uid && rfid.last_uid !== "--") {
                        const isAuth = rfid.access_granted;
                        rfidStatusBox.className = isAuth ? "rfid-status-box is-authorized" : "rfid-status-box is-denied";
                        rfidStatusText.textContent = rfid.status || (isAuth ? "ACCESO AUTORIZADO" : "ACCESO DENEGADO");
                        rfidSubText.textContent = isAuth 
                            ? `Tarjeta UID ${rfid.last_uid} - Ingreso al Recinto Concedido` 
                            : `Tarjeta UID ${rfid.last_uid} - CREDENCIAL BLOQUEADA`;
                        if (rfidLastUid) rfidLastUid.textContent = rfid.last_uid;
                        if (rfidCardHolder) {
                            rfidCardHolder.textContent = rfid.card_holder || (isAuth ? "Autorizado" : "Bloqueado");
                            rfidCardHolder.className = isAuth ? "rfid-metric-val font-mono text-emerald" : "rfid-metric-val font-mono text-error";
                        }
                        if (rfidReadsCount) rfidReadsCount.textContent = rfid.total_reads || 0;
                        if (rfidLastTime) rfidLastTime.textContent = rfid.last_time || "--:--:--";
                    }

                    // Renderizar lista de credenciales registradas
                    if (rfidCardsList && rfid.known_cards && rfid.known_cards.length > 0) {
                        rfidCardsList.innerHTML = rfid.known_cards.map(c => {
                            const badge = c.status === "BLOQUEADA" 
                                ? `<span class="badge-blocked">BLOQUEADA</span>` 
                                : `<span class="badge-authorized">AUTORIZADA</span>`;
                            return `
                                <div class="rfid-card-item">
                                    <span class="badge-rfid font-mono">🪪 ${c.uid}</span>
                                    <span class="rfid-card-name">${c.holder}</span>
                                    ${badge}
                                    <span class="font-mono text-muted text-xs">${c.scans} usos</span>
                                </div>
                            `;
                        }).join("");
                    }
                }

                // Estado del Sensor Infrarrojo (Fase 1)
                if (data.ir_sensor && irStatusBox) {
                    const ir = data.ir_sensor;
                    if (ir.is_detected) {
                        irStatusBox.className = "ir-status-box is-detected";
                        irStateText.textContent = "DETECTADO";
                        irSubText.textContent = "¡Paso detectado por haz óptico!";
                    } else {
                        irStatusBox.className = "ir-status-box is-free";
                        irStateText.textContent = "LIBRE";
                        irSubText.textContent = "Haz óptico despejado";
                    }

                    if (irActivationsCount) irActivationsCount.textContent = ir.total_activations || 0;
                    if (irLastTime) irLastTime.textContent = ir.last_detection_time || "--:--:--";

                    if (irEventsList && ir.recent_events && ir.recent_events.length > 0) {
                        irEventsList.innerHTML = ir.recent_events.slice(0, 10).map(ev => {
                            if (ev.event_type === "CARD_SCANNED") {
                                const uidLabel = ev.uid ? `UID: ${ev.uid}` : "TARJETA";
                                return `
                                    <div class="ir-event-row" style="background: rgba(14, 165, 233, 0.1); border-left: 2px solid #38bdf8;">
                                        <span class="font-mono text-muted">${ev.time}</span>
                                        <span class="badge-rfid">🪪 ${uidLabel} [ACCESO]</span>
                                    </div>
                                `;
                            }
                            const badgeClass = ev.event_type === "IR_INTERRUPTED" ? "badge-interrupted" : "badge-cleared";
                            const badgeText = ev.event_type === "IR_INTERRUPTED" ? "IR: PASO DETECTADO" : "IR: HAZ LIBRE";
                            const simLabel = ev.is_simulated ? " [SIM]" : "";
                            return `
                                <div class="ir-event-row">
                                    <span class="font-mono text-muted">${ev.time}</span>
                                    <span class="${badgeClass}">${badgeText}${simLabel}</span>
                                </div>
                            `;
                        }).join("");
                    }
                }

                // Conteo de personas
                const count = data.detector.persons_visible;
                personCountElem.textContent = count !== undefined ? count : "--";

                // Métricas
                inferenceTimeElem.textContent = `${data.detector.inference_ms} ms`;
                framesTotalElem.textContent = data.camera.frames_processed || 0;
                fpsValElem.textContent = data.fps_estimate || "0.0";

                // Error del detector si existe
                if (data.detector.error) {
                    detectorStatusElem.textContent = "Alerta: error";
                    detectorStatusElem.className = "stat-val text-error";
                } else {
                    detectorStatusElem.textContent = "Activo";
                    detectorStatusElem.className = "stat-val text-success";
                }

                // Marca de tiempo
                if (data.camera.last_capture_ts) {
                    const date = new Date(data.camera.last_capture_ts * 1000);
                    captureTimeElem.textContent = `Última: ${date.toLocaleTimeString()}`;
                }

                // Recargar imagen solo si hay conexión
                refreshImage();
            }
        } catch (err) {
            console.warn("Fallo temporal de consulta de telemetría:", err);
            cameraBadge.className = "status-pill status-disconnected";
            cameraStatusText.textContent = "Error de red local";
        } finally {
            isFetching = false;
        }
    }

    function refreshImage() {
        const isRaw = toggleRaw.checked;
        const cacheBuster = Date.now();
        const newSrc = `/api/snapshot?raw=${isRaw}&t=${cacheBuster}`;

        const nextImg = new Image();
        nextImg.onload = () => {
            streamImg.src = newSrc;
        };
        nextImg.src = newSrc;
    }

    // Alternar modo raw
    toggleRaw.addEventListener("change", () => {
        refreshImage();
    });

    // Acción explícita para DeepSeek
    if (btnDeepSeek) {
        btnDeepSeek.addEventListener("click", async () => {
            btnDeepSeek.disabled = true;
            btnDeepSeekText.textContent = "Analizando con DeepSeek...";
            deepseekResultBox.classList.remove("hidden");
            deepseekOutputContent.textContent = "Enviando fotograma a la API de DeepSeek...";

            try {
                const response = await fetch("/api/analyze/deepseek", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({})
                });

                const result = await response.json();

                if (response.ok && result.success) {
                    deepseekOutputContent.textContent = result.estimation || "Respuesta sin contenido descriptivo.";
                } else {
                    deepseekOutputContent.textContent = `Aviso: ${result.error || "No se pudo completar el análisis."}`;
                }
            } catch (err) {
                deepseekOutputContent.textContent = `Error de conexión: ${err.message}`;
            } finally {
                btnDeepSeek.disabled = false;
                btnDeepSeekText.textContent = "Consultar DeepSeek";
            }
        });
    }

    // Bucle periódico de refresco
    setInterval(updateDashboard, pollInterval);
    updateDashboard();
});
