const API_BASE = '/api';
let currentBasinId = 'pinglin';
let trendChart = null; // 為 Chart.js 保留實例

// 建立狀態樣式的 Helper Function
function setStatusBadge(elementId, statusText) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.className = 'status-badge'; // Reset
    el.textContent = statusText;
    
    if (statusText.includes('🟢')) el.classList.add('status-green');
    else if (statusText.includes('🔴')) el.classList.add('status-red');
    else if (statusText.includes('🟡')) el.classList.add('status-yellow');
    else el.style.background = 'rgba(255,255,255,0.1)';
}

// 切換流域
window.switchBasin = function(basinId) {
    if (currentBasinId === basinId) return;
    
    // Update Tab UI
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`tab-${basinId}`).classList.add('active');
    
    // Set State & Reload
    currentBasinId = basinId;
    fetchAndRenderBasin();
}

// Modal Logic
window.openReportModal = function() {
    document.getElementById('report-modal').style.display = 'flex';
}
window.closeReportModal = function() {
    document.getElementById('report-modal').style.display = 'none';
}

// 獲取交通資料
async function fetchTraffic() {
    try {
        const res = await fetch(`${API_BASE}/live/traffic/${currentBasinId}`);
        const data = await res.json();
        
        let container = document.getElementById('traffic-container');
        let routesHtml = '';
        
        // 渲染交通管制與施工等特殊訊息
        if (data.traffic_controls && data.traffic_controls.length > 0) {
            routesHtml += `<div style="margin-bottom: 1rem; padding: 0.6rem; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; color: #fca5a5; font-size: 0.85rem; line-height: 1.5;">`;
            data.traffic_controls.forEach(msg => {
                routesHtml += `<div style="margin-bottom: 4px;">${msg}</div>`;
            });
            routesHtml += `</div>`;
        }
        
        data.routes.forEach(r => {
            let colorClass = r.status.includes('🟢') ? 'highlight' : (r.status.includes('🔴') ? 'text-red' : 'text-yellow');
            routesHtml += `
                <div style="margin-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 0.5rem;">
                    <div class="metric" style="color: #38bdf8;"><strong>${r.route_name}</strong></div>
                    <div class="metric"><span class="label">車速</span><span class="value ${colorClass}">${r.avg_speed_kmh} km/h</span></div>
                    <div class="metric"><span class="label">狀態</span><span class="value">${r.status}</span></div>
                </div>
            `;
        });
        
        routesHtml += `<div style="text-align:right; font-size: 0.75rem; color:#64748b;">最後更新: ${data.last_update}</div>`;
        container.innerHTML = routesHtml;

    } catch (e) {
        console.error('Traffic API Error:', e);
        document.getElementById('traffic-container').innerHTML = '<div class="status-badge status-red">連線失敗 🔴</div>';
    }
}

// 獲取天氣資料 (CWA 排版)
async function fetchWeather(stationId) {
    try {
        const res = await fetch(`${API_BASE}/live/weather/${stationId}`);
        const data = await res.json();

        document.getElementById('w-temp').textContent = `${data.current_temp}°C`;
        document.getElementById('w-desc').textContent = data.weather_desc;
        document.getElementById('w-feels').textContent = `${data.feels_like_temp}°C`;
        document.getElementById('w-humidity').textContent = data.humidity;
        document.getElementById('w-wind').textContent = data.wind_speed;
        document.getElementById('w-uv').textContent = data.uv_index;
        
        // Icon logic
        let icon = '☀️';
        if (data.weather_desc.includes('雨')) icon = '🌧️';
        else if (data.weather_desc.includes('雲')) icon = '⛅';
        else if (data.weather_desc.includes('陰')) icon = '☁️';
        document.getElementById('w-icon').textContent = icon;
        
        // 渲染天氣警示訊息 (如：雷陣雨、烈日高溫)
        let warnContainer = document.getElementById('weather-warning-container');
        if (data.weather_warning) {
            let warnColor = data.weather_warning.includes('雷') ? 'rgba(239, 68, 68, 0.15)' : 'rgba(249, 115, 22, 0.15)';
            let warnBorder = data.weather_warning.includes('雷') ? 'rgba(239, 68, 68, 0.3)' : 'rgba(249, 115, 22, 0.3)';
            let warnText = data.weather_warning.includes('雷') ? '#fca5a5' : '#fdba74';
            warnContainer.innerHTML = `<div style="margin-bottom: 15px; padding: 0.6rem; background: ${warnColor}; border: 1px solid ${warnBorder}; border-radius: 8px; color: ${warnText}; font-size: 0.85rem; line-height: 1.5; font-weight: bold; text-align: center;">${data.weather_warning}</div>`;
        } else {
            warnContainer.innerHTML = '';
        }
        
        document.getElementById('w-update').textContent = `觀測站: ${data.station_name} | 更新: ${data.last_update}`;
        
        // --- 48H 戰術預估邏輯 (模擬分析) ---
        renderStrategicForecast(data);
        
    } catch (e) {
        console.error('Weather API Error:', e);
        document.getElementById('w-temp').textContent = 'X';
    }
}

function renderStrategicForecast(liveWeather) {
    const container = document.getElementById('weather-warning-container');
    // 模擬未來 48 小時降雨機率與建議
    let rainProb = liveWeather.weather_desc.includes('雨') ? 85 : 20;
    let advice = rainProb > 30 ? "⚠️ 明日預期降雨，溪水恐起水，建議縮短作釣時間。" : "✅ 氣候穩定，預期未來 48h 水位持平，適合長征作釣。";
    
    // 將建議以戰術風格顯示
    const adviceHtml = `
        <div style="margin-bottom: 10px; padding: 10px; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; font-size: 0.8rem;">
            <div style="color: #38bdf8; font-weight: bold; margin-bottom: 5px;">📡 48H 戰術評估</div>
            <div style="color: #e2e8f0;">${advice}</div>
            <div style="margin-top: 5px; color: #94a3b8;">預期降雨率: ${rainProb}%</div>
        </div>
    `;
    // 先清空原本的 warning，再重新組合（保持 order）
    container.innerHTML = adviceHtml + container.innerHTML;
}

// 獲取水文站資料 (含降雨與濁度)
async function fetchWater(stationId) {
    try {
        const res = await fetch(`${API_BASE}/live/water/${stationId}`);
        const data = await res.json();

        if (data.station_id === "UNKNOWN") {
            document.getElementById('h-station').textContent = "無官方水文站";
            document.getElementById('h-level').textContent = "-";
            document.getElementById('h-warn').textContent = "-";
            document.getElementById('h-rain-1h').textContent = "- mm";
            document.getElementById('h-rain-24h').textContent = "- mm";
            setStatusBadge('h-status', data.status);
            setStatusBadge('h-turbidity', data.turbidity_status);
            return;
        }

        document.getElementById('h-station').textContent = data.station_name;
        document.getElementById('h-level').textContent = `${data.current_level_m} m`;
        document.getElementById('h-warn').textContent = `${data.warning_level_m} m`;
        document.getElementById('h-rain-1h').textContent = `${data.rain_accumulated_1h_mm} mm`;
        document.getElementById('h-rain-24h').textContent = `${data.rain_accumulated_24h_mm} mm`;
        
        setStatusBadge('h-status', data.status);
        setStatusBadge('h-turbidity', data.turbidity_status);
    } catch (e) {
        console.error('Water API Error:', e);
        setStatusBadge('h-status', '連線失敗 🔴');
        setStatusBadge('h-turbidity', '連線失敗 🔴');
    }
}

// Toggle Accordion for Fishing Spots
window.toggleSpotDetails = function(element) {
    const details = element.querySelector('.spot-details');
    const icon = element.querySelector('.toggle-icon');
    const spotName = element.querySelector('.spot-name');
    
    if (details.style.display === 'none') {
        details.style.display = 'block';
        icon.style.transform = 'rotate(180deg)';
        spotName.style.color = '#38bdf8';
    } else {
        details.style.display = 'none';
        icon.style.transform = 'rotate(0deg)';
        spotName.style.color = '';
    }
}

// 獲取核心資料庫 (流域與釣點) 並渲染
async function fetchAndRenderBasin() {
    try {
        const res = await fetch(`${API_BASE}/fishing_spots/${currentBasinId}`);
        const data = await res.json();
        
        // Fetch Live APIs
        fetchTraffic();
        fetchWeather(data.weather_station_id);
        
        // 取主流來當水情指標
        const main_station = data.river_sections.find(s => s.type.includes('主流'))?.water_level_station_id || 'UNKNOWN';
        fetchWater(main_station);
        
        // 更新表單釣點選單
        const spotSelect = document.getElementById('report-spot');
        spotSelect.innerHTML = '<option value="">請選擇本次作釣點...</option>';
        spotSelect.innerHTML += '<option value="自家菜園 (不便透露)">🤫 自家菜園 (不便透露)</option>';
        data.river_sections.forEach(section => {
            section.fishing_spots.forEach(spot => {
                spotSelect.innerHTML += `<option value="${spot.spot_name}">${spot.spot_name}</option>`;
            });
        });
        
        // 載入該流域戰報
        fetchReports();

        // Render River Sections
        const listContainer = document.getElementById('river-list');
        listContainer.innerHTML = '';

        data.river_sections.forEach(section => {
            const card = document.createElement('div');
            card.className = 'glass-card river-card';

            let spotsHtml = '';
            if (section.fishing_spots.length === 0) {
                spotsHtml = '<div class="spot-item"><span class="spot-name">未解鎖 / 尚未勘查</span></div>';
            } else {
                spotsHtml = section.fishing_spots.map(spot => {
                    let decoyText = spot.decoy_vendor ? `販售魚媒：${spot.decoy_vendor}` : `有販售魚媒`;
                    const decoyBadge = spot.has_decoy ? `<span class="badge decoy-badge" style="pointer-events: none;">${decoyText}</span>` : '';
                    return `
                    <li class="spot-item" style="cursor: pointer; transition: background 0.3s;" onmouseover="this.style.background='rgba(255,255,255,0.08)'" onmouseout="this.style.background='rgba(255,255,255,0.05)'" onclick="window.toggleSpotDetails(this)">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="display:flex; align-items:center; gap: 8px;">
                                <span class="spot-name" style="margin-bottom:0; transition: color 0.3s;">📍 ${spot.spot_name}</span>
                                <span class="toggle-icon" style="font-size: 0.8rem; color: #64748b; transition: transform 0.3s; display: inline-block;">▼</span>
                            </div>
                            ${decoyBadge}
                        </div>
                        <div class="spot-details" style="display: none; margin-top: 12px; background: rgba(0,0,0,0.9); border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; padding: 15px; box-shadow: inset 0 2px 10px rgba(0,0,0,0.5);">
                            
                            <div style="margin-bottom: 12px; line-height: 1.6; font-size: 0.95rem; letter-spacing: 0.5px; font-weight: 300;">
                                <span style="color: #38bdf8; font-weight: 700; font-size: 0.75rem; letter-spacing: 1.5px; display: block; margin-bottom: 4px; border-bottom: 1px solid rgba(56,189,248,0.3); padding-bottom: 2px; width: fit-content;">📝 FEATURE / 特色</span>
                                <span style="color: #f8fafc;">${spot.spot_desc || '尚無描述'}</span>
                            </div>
                            
                            <div style="margin-bottom: 12px; line-height: 1.6; font-size: 0.95rem; letter-spacing: 0.5px; font-weight: 300;">
                                <span style="color: #4ade80; font-weight: 700; font-size: 0.75rem; letter-spacing: 1.5px; display: block; margin-bottom: 4px; border-bottom: 1px solid rgba(74,222,128,0.3); padding-bottom: 2px; width: fit-content;">🥾 ACCESS / 徒步下切</span>
                                <span style="color: #f8fafc;">${spot.access_info}</span>
                            </div>
                            
                            <div style="line-height: 1.6; font-size: 0.95rem; letter-spacing: 0.5px; font-weight: 300;">
                                <span style="color: #f8fafc;">${spot.business_status}</span>
                            </div>

                            ${spot.map_url ? `
                            <div style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px;">
                                <a href="${spot.map_url}" target="_blank" style="display: block; width: 100%; padding: 10px; background: #38bdf8; color: #000; text-decoration: none; text-align: center; border-radius: 8px; font-weight: 900; font-size: 0.9rem; letter-spacing: 1px; box-shadow: 0 4px 15px rgba(56, 189, 248, 0.3); transition: all 0.2s;">🏎️ GOOGLE MAP 直達導航</a>
                            </div>
                            ` : ''}
                        </div>
                            
                        </div>
                    </li>
                `}).join('');
            }

            card.innerHTML = `
                <h3>${section.name} <span class="river-type">${section.type.includes('主流') ? '主流' : '支流'}</span></h3>
                <p class="river-desc">${section.characteristics}</p>
                <ul class="spots-list">
                    ${spotsHtml}
                </ul>
            `;
            listContainer.appendChild(card);
        });

    } catch (e) {
        console.error('Basin Fetch Error:', e);
        document.getElementById('basin-title').textContent = '⚠️ 無法載入流域資料，請確認後端是否重啟';
    }
}

// 獲取並渲染戰報
async function fetchReports() {
    try {
        const res = await fetch(`${API_BASE}/reports/${currentBasinId}`);
        const reports = await res.json();
        const container = document.getElementById('reports-container');
        
        if (reports.length === 0) {
            container.innerHTML = '<div style="color:#64748b; padding: 20px;">尚無紀錄或戰報正在等待審核中...</div>';
            return;
        }
        
        let html = '';
        reports.forEach(r => {
            html += `
                <div class="report-card">
                    <img src="${r.photo_urls[0]}" alt="戰報照片">
                    <div class="report-card-body">
                        <div class="report-meta">
                            <span>📍 ${r.spot_name}</span>
                            <span>👤 ${r.author}</span>
                        </div>
                        <p style="font-size: 0.9rem; color: #e2e8f0; margin-bottom: 10px; line-height: 1.4;">
                            ${r.content}
                        </p>
                        <div style="margin-bottom: 10px;">
                            <span class="badge" style="background: rgba(34,197,94,0.2); color:#4ade80;">🐟 ${r.catch.count}</span>
                            <span class="badge" style="background: rgba(234,179,8,0.2); color:#fde047;">📏 最大 ${r.catch.max_size}cm</span>
                        </div>
                        <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;">
                            <span class="tackle-tag">🎣 ${r.tackle.rod}</span>
                            <span class="tackle-tag">🧵 ${r.tackle.line}</span>
                            <span class="tackle-tag">🪝 ${r.tackle.hook}</span>
                        </div>
                        <div style="margin-top: 10px; font-size: 0.75rem; color: #64748b; display:flex; justify-content:space-between; align-items: center; border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 8px;">
                            <span>💦 ${r.telemetry.water_level} / ${r.telemetry.turbidity}</span>
                            <span style="color: #38bdf8; font-weight: bold;">🌤️ ${r.telemetry.weather_desc} ${r.telemetry.temp}℃</span>
                        </div>
                    </div>
                </div>
            `;
        });
        container.innerHTML = html;
    } catch (e) {
        console.error("Failed to load reports:", e);
    }
}

// 提交表單邏輯
window.submitReport = async function(e) {
    e.preventDefault();
    
    // 安全地抓取當下儀表板數值
    const waterLevel = document.getElementById('h-level')?.textContent || '未知';
    const turbidityEl = document.getElementById('h-turbidity');
    const turbidity = turbidityEl ? turbidityEl.textContent : '未知';
    const temp = document.getElementById('w-temp')?.textContent || '未知';
    const weather = document.getElementById('w-desc')?.textContent || '未知';

    // 使用 FormData 以支援檔案上傳
    const formData = new FormData();
    formData.append('basin_id', currentBasinId);
    formData.append('spot_name', document.getElementById('report-spot').value);
    formData.append('author', "匿名釣客");
    formData.append('content', document.getElementById('report-content').value);
    formData.append('catch_count', document.getElementById('report-count').value || "-");
    formData.append('catch_max_size', document.getElementById('report-size').value || "-");
    formData.append('tackle_rod', document.getElementById('report-rod').value);
    formData.append('tackle_line', document.getElementById('report-line').value);
    formData.append('tackle_hook', document.getElementById('report-hook').value);
    
    // Telemetry as JSON string
    formData.append('telemetry', JSON.stringify({
        water_level: waterLevel,
        turbidity: turbidity,
        weather_desc: weather,
        temp: temp
    }));

    // Add the photo file
    const photoInput = document.getElementById('report-photo');
    if (photoInput.files.length > 0) {
        formData.append('photo', photoInput.files[0]);
    }

    try {
        const res = await fetch(`${API_BASE}/reports`, {
            method: 'POST',
            body: formData // Fetch allows passing FormData directly
        });
        const result = await res.json();
        alert(result.message);
        window.closeReportModal();
        e.target.reset();
    } catch (err) {
        console.error(err);
        alert("送出失敗，請檢查網路連線或照片大小");
    }
}

// --- 圖表與趨勢邏輯 ---
window.showTrend = async function() {
    document.getElementById('trend-modal').style.display = 'flex';
    try {
        const res = await fetch(`${API_BASE}/telemetry/history/${currentBasinId}`);
        const data = await res.json();
        renderTrendChart(data);
    } catch (err) {
        console.error("Trend Fetch Error:", err);
    }
}

window.closeTrendModal = function() {
    document.getElementById('trend-modal').style.display = 'none';
    if (trendChart) {
        trendChart.destroy();
        trendChart = null;
    }
}

function renderTrendChart(history) {
    const ctx = document.getElementById('trendChart').getContext('2d');
    
    const labels = history.levels.map(l => l.time);
    const levelData = history.levels.map(l => l.value);
    const rainData = history.rains.map(l => l.value);

    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '水位 (m)',
                    data: levelData,
                    borderColor: '#38bdf8',
                    backgroundColor: 'rgba(56, 189, 248, 0.1)',
                    yAxisID: 'y',
                    fill: true,
                    tension: 0.3
                },
                {
                    label: '降雨 (mm)',
                    data: rainData,
                    borderColor: '#fbbf24',
                    backgroundColor: 'rgba(251, 191, 36, 0.1)',
                    yAxisID: 'y1',
                    fill: true,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#94a3b8' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#94a3b8' }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    fetchAndRenderBasin();
    setInterval(fetchAndRenderBasin, 60000);
});
