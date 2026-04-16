const API_BASE = '/api';
let currentBasinId = 'pinglin';
let trendChart = null; // 為 Chart.js 保留實例

// 建立狀態樣式的 Helper Function
function setStatusBadge(elementId, statusText) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.className = 'status-badge'; // Reset
    const safeText = statusText || '未知';
    el.textContent = safeText;
    
    if (safeText.includes('🟢')) el.classList.add('status-green');
    else if (safeText.includes('🔴')) el.classList.add('status-red');
    else if (safeText.includes('🟡')) el.classList.add('status-yellow');
    else el.style.background = 'rgba(255,255,255,0.1)';
}

// 切換流域
window.switchBasin = function(basinId) {
    if (currentBasinId === basinId) return;
    console.log(`🔄 Switching Basin to: ${basinId}`);
    
    // Update Tab UI
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    const targetTab = document.getElementById(`tab-${basinId}`);
    if (targetTab) targetTab.classList.add('active');
    
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
        if (!container) return;
        
        let routesHtml = '';
        
        // 渲染交通管制與施工等特殊訊息
        if (data.traffic_controls && data.traffic_controls.length > 0) {
            routesHtml += `<div style="margin-bottom: 1rem; padding: 0.6rem; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; color: #fca5a5; font-size: 0.85rem; line-height: 1.5;">`;
            data.traffic_controls.forEach(msg => {
                routesHtml += `<div style="margin-bottom: 4px;">${msg}</div>`;
            });
            routesHtml += `</div>`;
        }
        
        if (data.routes) {
            data.routes.forEach(r => {
                const statusStr = r.status || '';
                let colorClass = statusStr.includes('🟢') ? 'highlight' : (statusStr.includes('🔴') ? 'text-red' : 'text-yellow');
                routesHtml += `
                    <div style="margin-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 0.5rem;">
                        <div class="metric" style="color: #38bdf8;"><strong>${r.route_name || '未知路段'}</strong></div>
                        <div class="metric"><span class="label">車速</span><span class="value ${colorClass}">${r.avg_speed_kmh || '--'} km/h</span></div>
                        <div class="metric"><span class="label">狀態</span><span class="value">${statusStr}</span></div>
                    </div>
                `;
            });
        }
        
        if (data.cameras && data.cameras.length > 0) {
            routesHtml += `<div style="margin-top: 1rem; color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.5rem;">即時監控：</div>`;
            data.cameras.forEach(c => {
                routesHtml += `
                    <div style="margin-bottom: 0.5rem;">
                        <a href="${c.url}" target="_blank" style="color: #38bdf8; text-decoration: none; font-size: 0.95rem; display: flex; align-items: center; gap: 8px; background: rgba(56, 189, 248, 0.1); padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(56, 189, 248, 0.2); transition: all 0.2s;">
                            <i class="fa-solid fa-video"></i> ${c.cam_name}
                        </a>
                    </div>
                `;
            });
        }
        
        routesHtml += `<div style="text-align:right; font-size: 0.75rem; color:#64748b;">最後更新: ${data.last_update || '--'}</div>`;
        container.innerHTML = routesHtml;

    } catch (e) {
        console.error('Traffic API Error:', e);
        const el = document.getElementById('traffic-container');
        if (el) el.innerHTML = '<div class="status-badge status-red">交通資訊暫不可用 🔴</div>';
    }
}

// 獲取天氣資料 (CWA 排版)
async function fetchWeather(stationId) {
    try {
        const res = await fetch(`${API_BASE}/live/weather/${stationId}`);
        if (!res.ok) throw new Error('Weather API 400');
        const data = await res.json();

        document.getElementById('w-temp').textContent = `${data.current_temp || '--'}°C`;
        const desc = data.weather_desc || '未知';
        document.getElementById('w-desc').textContent = desc;
        document.getElementById('w-feels').textContent = `${data.feels_like_temp || '--'}°C`;
        document.getElementById('w-humidity').textContent = data.humidity || '--';
        document.getElementById('w-wind').textContent = data.wind_speed || '--';
        document.getElementById('w-uv').textContent = data.uv_index || '--';
        
        // Icon logic
        let icon = '☀️';
        if (desc.includes('雨')) icon = '🌧️';
        else if (desc.includes('雲')) icon = '⛅';
        else if (desc.includes('陰')) icon = '☁️';
        document.getElementById('w-icon').textContent = icon;
        
        // 渲染天氣警示訊息
        let warnContainer = document.getElementById('weather-warning-container');
        if (warnContainer) {
            if (data.weather_warning) {
                const warnTextAttr = data.weather_warning || '';
                let warnColor = warnTextAttr.includes('雷') ? 'rgba(239, 68, 68, 0.15)' : 'rgba(249, 115, 22, 0.15)';
                let warnBorder = warnTextAttr.includes('雷') ? 'rgba(239, 68, 68, 0.3)' : 'rgba(249, 115, 22, 0.3)';
                let warnText = warnTextAttr.includes('雷') ? '#fca5a5' : '#fdba74';
                warnContainer.innerHTML = `<div style="margin-bottom: 15px; padding: 0.6rem; background: ${warnColor}; border: 1px solid ${warnBorder}; border-radius: 8px; color: ${warnText}; font-size: 0.85rem; line-height: 1.5; font-weight: bold; text-align: center;">${data.weather_warning}</div>`;
            } else {
                warnContainer.innerHTML = '';
            }
            // 渲染策略建議
            renderStrategicForecast(data);
        }
        
        document.getElementById('w-update').textContent = `觀測站: ${data.station_name || '未知'} | 更新: ${data.last_update || '--'}`;
        
    } catch (e) {
        console.error('Weather API Error:', e);
        document.getElementById('w-temp').textContent = 'X';
        document.getElementById('w-desc').textContent = '連結中...';
    }
}

function renderStrategicForecast(liveWeather) {
    const container = document.getElementById('weather-warning-container');
    if (!container) return;
    
    const desc = liveWeather.weather_desc || '';
    let rainProb = desc.includes('雨') ? 85 : 20;
    let advice = rainProb > 30 ? "⚠️ 明日預期降雨，溪水恐起水，建議縮短作釣時間。" : "✅ 氣候穩定，預期未來 48h 水位持平，適合長征作釣。";
    
    const adviceHtml = `
        <div style="margin-bottom: 10px; padding: 10px; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; font-size: 0.8rem;">
            <div style="color: #38bdf8; font-weight: bold; margin-bottom: 5px;">📡 48H 戰術評估</div>
            <div style="color: #e2e8f0;">${advice}</div>
            <div style="margin-top: 5px; color: #94a3b8;">預期降雨率: ${rainProb}%</div>
        </div>
    `;
    container.innerHTML = adviceHtml + container.innerHTML;
}

// 獲取水文站資料
async function fetchWater(stationId) {
    try {
        const res = await fetch(`${API_BASE}/live/water/${stationId}`);
        if (!res.ok) throw new Error('Water API 400');
        const data = await res.json();

        if (data.station_id === "UNKNOWN") {
            document.getElementById('h-station').textContent = "無官方觀測站";
            document.getElementById('h-rain-24h').textContent = "- mm";
            document.getElementById('h-rain-72h').textContent = "- mm";
            setStatusBadge('h-turbidity', data.turbidity_status);
            return;
        }

        document.getElementById('h-station').textContent = data.station_name || '未知';
        document.getElementById('h-rain-24h').textContent = `${data.rain_24h !== undefined ? data.rain_24h : '-'} mm`;
        document.getElementById('h-rain-72h').textContent = `${data.rain_72h !== undefined ? data.rain_72h : '-'} mm`;
        
        // 取得正確的 CWA ID 產生圖表連結 (對應氣象署實施站點)
        if (currentBasinId === 'pinglin') {
            document.getElementById('h-trend-link').href = `https://www.cwa.gov.tw/V8/C/P/Rainfall/Rainfall_PlotImg.html?ID=C0A53`;
        } else {
            document.getElementById('h-trend-link').href = `https://www.cwa.gov.tw/V8/C/P/Rainfall/Rainfall_PlotImg.html?ID=C0A56`;
        }
        
        setStatusBadge('h-turbidity', data.turbidity_status);
    } catch (e) {
        console.error('Rainfall API Error:', e);
        setStatusBadge('h-turbidity', '連線失敗 🔴');
    }
}

// Toggle Accordion for Fishing Spots
window.toggleSpotDetails = function(element) {
    const details = element.querySelector('.spot-details');
    const icon = element.querySelector('.toggle-icon');
    const spotName = element.querySelector('.spot-name');
    
    if (!details) return;
    
    if (details.style.display === 'none') {
        details.style.display = 'block';
        if (icon) icon.style.transform = 'rotate(180deg)';
        if (spotName) spotName.style.color = '#38bdf8';
    } else {
        details.style.display = 'none';
        if (icon) icon.style.transform = 'rotate(0deg)';
        if (spotName) spotName.style.color = '';
    }
}

// 獲取核心資料庫 (流域與釣點) 並渲染
async function fetchAndRenderBasin() {
    console.log(`[Init] Fetching data for: ${currentBasinId}`);
    try {
        const res = await fetch(`${API_BASE}/fishing_spots/${currentBasinId}`);
        if (!res.ok) throw new Error('Basin API Failed');
        const data = await res.json();
        
        const listContainer = document.getElementById('river-list');
        if (!listContainer) return;
        
        if (!data || !data.river_sections || data.river_sections.length === 0) {
            console.warn('No sections found');
            listContainer.innerHTML = `
                <div class="glass-card" style="padding: 30px; text-align: center;">
                    <h3 style="color: #fca5a5;">⚠️ 資料庫讀取中</h3>
                    <p style="color: #94a3b8;">請稍候，或確認後端是否正在進行 Seeding。</p>
                </div>
            `;
            return;
        }
        
        // 隔離執行各組件，互不干擾
        try { fetchTraffic(); } catch(err) { console.error("Traffic fail", err); }
        try { fetchWeather(data.weather_station_id); } catch(err) { console.error("Weather fail", err); }
        
        const main_station = (data.river_sections || []).find(s => (s.type || s.section_type || '').includes('主流'))?.water_level_station_id || 'UNKNOWN';
        try { fetchWater(main_station); } catch(err) { console.error("Water fail", err); }
        try { fetchReports(); } catch(err) { console.error("Reports fail", err); }
        
        // 更新表單釣點選單 (並保存使用者已選項目防止被計時器覆蓋)
        const spotSelect = document.getElementById('report-spot');
        if (spotSelect) {
            const currentSelected = spotSelect.value;
            spotSelect.innerHTML = '<option value="">請選擇本次作釣點...</option>';
            spotSelect.innerHTML += '<option value="自家菜園 (不便透露)">🤫 自家菜園 (不便透露)</option>';
            data.river_sections.forEach(section => {
                if (section.fishing_spots) {
                    section.fishing_spots.forEach(spot => {
                        spotSelect.innerHTML += `<option value="${spot.spot_name}">${spot.spot_name}</option>`;
                    });
                }
            });
            if (currentSelected) {
                spotSelect.value = currentSelected;
            }
        }

        // Render River Sections
        listContainer.innerHTML = '';
        data.river_sections.forEach(section => {
            const card = document.createElement('div');
            card.className = 'glass-card river-card';

            let spotsHtml = '';
            if (!section.fishing_spots || section.fishing_spots.length === 0) {
                spotsHtml = '<div class="spot-item"><span class="spot-name">未解鎖 / 尚未勘查</span></div>';
            } else {
                spotsHtml = section.fishing_spots.map(spot => {
                    let decoyText = spot.decoy_vendor ? `販售魚媒：${spot.decoy_vendor}` : `有販售魚媒`;
                    const decoyBadge = spot.has_decoy ? `<span class="badge decoy-badge" style="pointer-events: none;">${decoyText}</span>` : '';
                    return `
                    <li class="spot-item" style="cursor: pointer; transition: background 0.3s;" onclick="window.toggleSpotDetails(this)">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="display:flex; align-items:center; gap: 8px;">
                                <span class="spot-name" style="margin-bottom:0; transition: color 0.3s;">📍 ${spot.spot_name}</span>
                                <span class="toggle-icon" style="font-size: 0.8rem; color: #64748b; transition: transform 0.3s; display: inline-block;">▼</span>
                            </div>
                            ${decoyBadge}
                        </div>
                        <div class="spot-details" style="display: none; margin-top: 12px; background: rgba(0,0,0,0.9); border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; padding: 15px;">
                            <div style="margin-bottom: 12px; font-size: 0.95rem;">
                                <span style="color: #38bdf8; font-weight: 700; font-size: 0.75rem; display: block; margin-bottom: 4px;">📝 FEATURE / 特色</span>
                                <span style="color: #f8fafc;">${spot.spot_desc || '尚無描述'}</span>
                            </div>
                            <div style="margin-bottom: 12px; font-size: 0.95rem;">
                                <span style="color: #4ade80; font-weight: 700; font-size: 0.75rem; display: block; margin-bottom: 4px;">🥾 ACCESS / 徒步下切</span>
                                <span style="color: #f8fafc;">${spot.access_info || '未知'}</span>
                            </div>
                            <div style="font-size: 0.95rem;">
                                <span style="color: #f8fafc;">${spot.business_status || '--'}</span>
                            </div>
                            ${spot.map_url ? `
                            <div style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px;">
                                <a href="${spot.map_url}" target="_blank" style="display: block; width: 100%; padding: 10px; background: #38bdf8; color: #000; text-decoration: none; text-align: center; border-radius: 8px; font-weight: 900; font-size: 0.9rem;">🏎️ GOOGLE 直達導航</a>
                            </div>
                            ` : ''}
                        </div>
                    </li>
                `.trim()}).join('');
            }

            const typeStr = section.type || section.section_type || '';
            const isMainstream = typeStr.includes('主流');
            card.innerHTML = `
                <h3>${section.name || '未知河段'} <span class="river-type">${isMainstream ? '主流' : '支流'}</span></h3>
                <p class="river-desc">${section.characteristics || ''}</p>
                <ul class="spots-list">
                    ${spotsHtml}
                </ul>
            `;
            listContainer.appendChild(card);
        });

    } catch (e) {
        console.error('Basin Fetch Critical Error:', e);
        const el = document.getElementById('river-list');
        if (el) el.innerHTML = '<div class="glass-card" style="padding:20px; color:#fca5a5;">⚠️ 無法載入流域資料，請檢查後端連線或重新整理頁面。</div>';
    }
}

// 獲取並渲染戰報
async function fetchReports() {
    try {
        const res = await fetch(`${API_BASE}/reports/${currentBasinId}`);
        const reports = await res.json();
        const container = document.getElementById('reports-container');
        if (!container) return;
        
        if (!reports || reports.length === 0) {
            container.innerHTML = '<div style="color:#64748b; padding: 20px;">尚無紀錄或戰報正在等待審核中...</div>';
            return;
        }
        
        let html = '';
        reports.forEach(r => {
            // Populate lightbox data
            if (r.photo_urls && r.photo_urls.length > 0) {
                window.lightboxData[r.id] = r.photo_urls;
            }

            const telemetry = r.telemetry || {};
            let photosHtml = '';
            if (r.photo_urls && r.photo_urls.length > 0) {
                photosHtml = '<div class="report-photos-grid">';
                r.photo_urls.forEach((url, idx) => {
                    photosHtml += `<img src="${url}" alt="戰報照片" onclick="window.openLightbox('${r.id}', ${idx})">`;
                });
                photosHtml += '</div>';
            } else {
                photosHtml = `<img src="https://via.placeholder.com/300" alt="戰報照片" class="single-photo">`;
            }

            html += `
                <div class="report-card">
                    ${photosHtml}
                    <div class="report-card-body">
                        <div class="report-meta">
                            <span>📍 ${r.spot_name || '未知'}</span>
                            <span>👤 ${r.author || '釣客'}</span>
                        </div>
                        <p style="font-size: 0.9rem; color: #e2e8f0; margin-bottom: 10px; line-height: 1.4;">
                            ${r.content || ''}
                        </p>
                        <div style="margin-bottom: 10px;">
                            <span class="badge" style="background: rgba(34,197,94,0.2); color:#4ade80;">🐟 釣獲總數 ${r.catch?.count || '--'}</span>
                            <span class="badge" style="background: rgba(234,179,8,0.2); color:#fde047;">📏 最大 ${r.catch?.max_size || '--'}cm</span>
                        </div>
                        <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;">
                            <span class="tackle-tag">🎣 ${r.tackle?.rod || '--'}</span>
                            <span class="tackle-tag">🧵 ${r.tackle?.line || '--'}</span>
                            <span class="tackle-tag">🪝 ${r.tackle?.hook || '--'}</span>
                        </div>
                        <div style="margin-top: 10px; font-size: 0.75rem; color: #64748b; display:flex; justify-content:space-between; align-items: center; border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 8px;">
                            <span>💦 ${telemetry.water_level || '--'} / ${telemetry.turbidity || '--'}</span>
                            <span style="color: #38bdf8; font-weight: bold;">🌤️ ${telemetry.weather_desc || ''} ${telemetry.temp || '--'}℃</span>
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

let isSubmittingReport = false;

// 提交表單邏輯
window.submitReport = async function(e) {
    e.preventDefault();
    if (isSubmittingReport) {
        console.log("阻擋重複提交");
        return;
    }
    isSubmittingReport = true;
    
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
    
    // 讀取分享者名稱
    const authorEl = document.getElementById('report-author');
    formData.append('author', authorEl ? authorEl.value : "匿名釣客");
    
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

    // Add up to 5 photo files
    const photoInput = document.getElementById('report-photo');
    if (photoInput && photoInput.files.length > 0) {
        let maxFiles = Math.min(photoInput.files.length, 5);
        for (let i = 0; i < maxFiles; i++) {
            formData.append('photos', photoInput.files[i]);
        }
    }
    const submitBtn = e.target.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '⏳ 上傳中請稍候...';
    }

    try {
        const res = await fetch(`${API_BASE}/reports`, {
            method: 'POST',
            body: formData
        });
        const result = await res.json();
        alert(result.message);
        window.closeReportModal();
        e.target.reset();
    } catch (err) {
        console.error(err);
        alert("送出失敗，請檢查網路連線或照片大小");
    } finally {
        isSubmittingReport = false;
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '送出等待站長審核';
        }
    }
}

// --- 圖表與趨勢邏輯 ---
window.showTrend = async function() {
    const modal = document.getElementById('trend-modal');
    if (modal) modal.style.display = 'flex';
    try {
        const res = await fetch(`${API_BASE}/telemetry/history/${currentBasinId}`);
        const data = await res.json();
        renderTrendChart(data);
    } catch (err) {
        console.error("Trend Fetch Error:", err);
    }
}

window.closeTrendModal = function() {
    const modal = document.getElementById('trend-modal');
    if (modal) modal.style.display = 'none';
    if (trendChart) {
        trendChart.destroy();
        trendChart = null;
    }
}

function renderTrendChart(history) {
    const canvas = document.getElementById('trendChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    if (!history.levels || !history.rains) return;
    
    const labels = history.levels.map(l => l.time);
    const levelData = history.levels.map(l => l.value);
    const rainData = history.rains.map(l => l.value);


    if (trendChart) {
        trendChart.destroy();
    }

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
    console.log("🚀 Ayu Radar System Initializing...");
    
    // Lightbox Data map
    window.lightboxData = {};

    window.openLightbox = function(reportId, startIndex) {
        const modal = document.getElementById('lightbox-modal');
        const img = document.getElementById('lightbox-img');
        if (modal && img && window.lightboxData[reportId]) {
            modal.currentReportId = reportId;
            modal.currentIndex = startIndex;
            img.src = window.lightboxData[reportId][startIndex];
            modal.style.display = 'flex';
        }
    }
    
    window.nextLightboxImage = function(e, direction) {
        if (e) e.stopPropagation();
        const modal = document.getElementById('lightbox-modal');
        const img = document.getElementById('lightbox-img');
        const reportId = modal.currentReportId;
        if (!reportId || !window.lightboxData[reportId]) return;
        
        const urls = window.lightboxData[reportId];
        let nextIdx = modal.currentIndex + direction;
        
        if (nextIdx >= urls.length) nextIdx = 0; // wrap around
        if (nextIdx < 0) nextIdx = urls.length - 1;
        
        modal.currentIndex = nextIdx;
        img.src = urls[nextIdx];
    }
    
    window.closeLightbox = function(e) {
        // Prevent closing if clicked directly on image or buttons
        if (e && (e.target.id === 'lightbox-img' || e.target.classList.contains('lightbox-btn'))) return;
        const modal = document.getElementById('lightbox-modal');
        if (modal) modal.style.display = 'none';
    }

    fetchAndRenderBasin();
    setInterval(fetchAndRenderBasin, 120000); // 2分鐘輪詢一次
});
