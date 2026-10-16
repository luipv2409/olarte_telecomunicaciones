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

    // Hardware Diagnostic Elements (Fase 3)
    const hwGlobalPill = document.getElementById("hw-global-pill");
    const hwGlobalText = document.getElementById("hw-global-text");
    const btnHwRefresh = document.getElementById("btn-hw-refresh");
    const hwRc522Chip = document.getElementById("hw-rc522-chip");
    const hwRc522Badge = document.getElementById("hw-rc522-badge");
    const hwRc522Guide = document.getElementById("hw-rc522-guide");
    const pinPillMosi = document.getElementById("pin-pill-mosi");
    const pinPillMiso = document.getElementById("pin-pill-miso");
    const ledPin21 = document.getElementById("led-pin-21");
    const ledPin47 = document.getElementById("led-pin-47");
    const ledPin1 = document.getElementById("led-pin-1");
    const hwIrBadge = document.getElementById("hw-ir-badge");
    const hwCamBadge = document.getElementById("hw-cam-badge");
    const btnTestBuzzerSuccess = document.getElementById("btn-test-buzzer-success");
    const btnTestBuzzerDenied = document.getElementById("btn-test-buzzer-denied");
    const virtualBuzzerLed = document.getElementById("virtual-buzzer-led");
    const virtualBuzzerText = document.getElementById("virtual-buzzer-text");

    // Tab Navigation Elements
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");
    const tabBadgeHw = document.getElementById("tab-badge-hw");

    function switchTab(targetTabId) {
        tabButtons.forEach(btn => {
            const isActive = btn.getAttribute("data-tab") === targetTabId;
            btn.classList.toggle("active", isActive);
            btn.setAttribute("aria-selected", isActive ? "true" : "false");
        });

        tabPanes.forEach(pane => {
            const isActive = pane.id === targetTabId;
            pane.classList.toggle("active", isActive);
        });

        try {
            localStorage.setItem("olarte_active_tab", targetTabId);
        } catch (e) {}
    }

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetId = btn.getAttribute("data-tab");
            if (targetId) switchTab(targetId);
        });
    });

    // Restaurar pestaña activa anterior si existe
    try {
        const savedTab = localStorage.getItem("olarte_active_tab");
        if (savedTab && document.getElementById(savedTab)) {
            switchTab(savedTab);
        }
    } catch (e) {}

    // Sintetizador Web Audio API para simular y reproducir la frecuencia del buzzer (2700 Hz)
    let audioCtx = null;
    function playBuzzerTone(durationMs, count = 1, intervalMs = 80) {
        try {
            if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            if (audioCtx.state === 'suspended') audioCtx.resume();
            
            let startTime = audioCtx.currentTime;
            for (let i = 0; i < count; i++) {
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = "square";
                osc.frequency.setValueAtTime(2700, startTime);
                
                gain.gain.setValueAtTime(0.2, startTime);
                gain.gain.setValueAtTime(0.001, startTime + (durationMs / 1000));
                
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                
                osc.start(startTime);
                osc.stop(startTime + (durationMs / 1000));
                
                startTime += ((durationMs + intervalMs) / 1000);
            }
        } catch(e) {
            console.warn("Audio no soportado o bloqueado por el navegador:", e);
        }
    }

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

                // Telemetría de Hardware y Diagnóstico de Pines (Fase 3)
                if (data.hardware) {
                    const hw = data.hardware;

                    // 1. Diagnóstico del Lector RFID RC522
                    if (hw.rc522) {
                        const rcf = hw.rc522;
                        if (hwRc522Chip) hwRc522Chip.textContent = rcf.chip_desc || `MFRC522 (${rcf.version_hex})`;

                        if (rcf.status === "OK") {
                            if (hwRc522Badge) {
                                hwRc522Badge.className = "badge-status-ok";
                                hwRc522Badge.textContent = `🟢 OK (${rcf.version_hex})`;
                            }
                            if (hwRc522Guide) {
                                hwRc522Guide.className = "hw-guide-alert";
                                hwRc522Guide.innerHTML = `✅ <b>Estado Saludable:</b> ${rcf.solution}`;
                            }
                            if (pinPillMosi) pinPillMosi.className = "pin-pill pin-ok";
                            if (pinPillMiso) pinPillMiso.className = "pin-pill pin-ok";
                            if (ledPin21) ledPin21.className = "pin-led led-ok";
                            if (ledPin47) ledPin47.className = "pin-led led-ok";
                        } else if (rcf.status && rcf.status.includes("SHORT")) {
                            if (hwRc522Badge) {
                                hwRc522Badge.className = "badge-status-warn";
                                hwRc522Badge.textContent = "⚠️ CORTO 21/47 (0xEE)";
                            }
                            if (hwRc522Guide) {
                                hwRc522Guide.className = "hw-guide-alert hw-guide-warn";
                                hwRc522Guide.innerHTML = `⚠️ <b>Atención en Cables:</b> ${rcf.solution}`;
                            }
                            if (pinPillMosi) pinPillMosi.className = "pin-pill pin-warn-active";
                            if (pinPillMiso) pinPillMiso.className = "pin-pill pin-warn-active";
                            if (ledPin21) ledPin21.className = "pin-led led-warn";
                            if (ledPin47) ledPin47.className = "pin-led led-warn";
                        } else {
                            if (hwRc522Badge) {
                                hwRc522Badge.className = "badge-status-error";
                                hwRc522Badge.textContent = `🔴 ERROR (${rcf.version_hex})`;
                            }
                            if (hwRc522Guide) {
                                hwRc522Guide.className = "hw-guide-alert hw-guide-error";
                                hwRc522Guide.innerHTML = `🔴 <b>Falla de Comunicación:</b> ${rcf.solution}`;
                            }
                            if (ledPin21) ledPin21.className = "pin-led led-err";
                            if (ledPin47) ledPin47.className = "pin-led led-err";
                        }
                    }

                    // 2. Sensor Infrarrojo
                    if (data.ir_sensor) {
                        const isDet = data.ir_sensor.is_detected;
                        if (hwIrBadge) {
                            hwIrBadge.className = isDet ? "badge-status-warn" : "badge-status-ok";
                            hwIrBadge.textContent = isDet ? "🔴 HAZ DETECTADO (0V)" : "🟢 HAZ LIBRE (3.3V)";
                        }
                        if (ledPin1) {
                            ledPin1.className = isDet ? "pin-led led-warn" : "pin-led led-ok";
                        }
                    }

                    // 3. Cámara OV5640
                    if (hwCamBadge) {
                        hwCamBadge.className = data.camera.connected ? "badge-status-ok" : "badge-status-error";
                        hwCamBadge.textContent = data.camera.connected ? "🟢 OK (VGA 640x480)" : "🔴 DESCONECTADO";
                    }

                    // 4. Pastilla de Estado Global & Badge de Pestaña
                    if (hwGlobalPill && hwGlobalText) {
                        if (hw.rc522 && hw.rc522.status !== "OK") {
                            hwGlobalPill.className = "status-pill status-disconnected";
                            hwGlobalText.textContent = "⚠️ REVISAR CABLEADO SPI";
                            if (tabBadgeHw) {
                                tabBadgeHw.className = "tab-pill-badge badge-hw-tab-warn";
                                tabBadgeHw.textContent = hw.rc522.status && hw.rc522.status.includes("SHORT") ? "CORTO 21/47" : "FALLA SPI";
                            }
                        } else if (!data.camera.connected) {
                            hwGlobalPill.className = "status-pill status-disconnected";
                            hwGlobalText.textContent = "⚠️ CÁMARA DESCONECTADA";
                            if (tabBadgeHw) {
                                tabBadgeHw.className = "tab-pill-badge badge-hw-tab-error";
                                tabBadgeHw.textContent = "CAM OFF";
                            }
                        } else {
                            hwGlobalPill.className = "status-pill status-connected";
                            hwGlobalText.textContent = "HARDWARE 100% OPERATIVO";
                            if (tabBadgeHw) {
                                tabBadgeHw.className = "tab-pill-badge badge-hw-tab-ok";
                                tabBadgeHw.textContent = "100% OK";
                            }
                        }
                    }
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

    // Eventos de Prueba del Buzzer (Fase 3)
    if (btnTestBuzzerSuccess) {
        btnTestBuzzerSuccess.addEventListener("click", async () => {
            playBuzzerTone(150, 1);
            if (virtualBuzzerLed) {
                virtualBuzzerLed.className = "virtual-led led-active-success";
                virtualBuzzerText.textContent = "Bip Éxito (150ms)";
                setTimeout(() => {
                    virtualBuzzerLed.className = "virtual-led";
                    virtualBuzzerText.textContent = "Reposo";
                }, 400);
            }
            try {
                await fetch("/api/test/buzzer", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ pattern: "success" })
                });
            } catch(e) {}
        });
    }

    if (btnTestBuzzerDenied) {
        btnTestBuzzerDenied.addEventListener("click", async () => {
            playBuzzerTone(80, 3, 80);
            if (virtualBuzzerLed) {
                virtualBuzzerLed.className = "virtual-led led-active-denied";
                virtualBuzzerText.textContent = "Alarma Denegado (3x80ms)";
                setTimeout(() => {
                    virtualBuzzerLed.className = "virtual-led";
                    virtualBuzzerText.textContent = "Reposo";
                }, 600);
            }
            try {
                await fetch("/api/test/buzzer", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ pattern: "denied" })
                });
            } catch(e) {}
        });
    }

    if (btnHwRefresh) {
        btnHwRefresh.addEventListener("click", () => {
            updateDashboard();
        });
    }

    // Interacción con los Pines del Mapa Visual
    document.querySelectorAll(".pin-item").forEach(item => {
        item.addEventListener("click", () => {
            const pinName = item.getAttribute("data-pin");
            const pinDesc = item.getAttribute("title");
            if (pinDesc) {
                alert(`[PIN ${pinName}]\n\n${pinDesc}`);
            }
        });
    });

    // Bucle periódico de refresco
    setInterval(updateDashboard, pollInterval);
    updateDashboard();
});
