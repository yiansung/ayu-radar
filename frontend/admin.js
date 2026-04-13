const API_BASE = '/api';
let adminPass = "";

window.checkAuth = function() {
    const pass = document.getElementById('admin-pass').value;
    if (pass === "qingshu1212") {
        adminPass = pass;
        document.getElementById('auth-overlay').style.display = 'none';
        document.getElementById('admin-main').style.display = 'block';
        fetchAdminReports();
    } else {
        alert("密碼錯誤，請重新輸入");
    }
};

async function fetchAdminReports() {
    try {
        const res = await fetch(`${API_BASE}/admin/reports`, {
            headers: { 'X-Admin-Password': adminPass }
        });
        const reports = await res.json();
        renderAdminTable(reports);
    } catch (err) { console.error(err); }
}

function renderAdminTable(reports) {
    const tbody = document.getElementById('admin-reports-table');
    tbody.innerHTML = reports.map(r => `
        <tr>
            <td><img src="${r.photo_urls[0]}" class="report-preview-img"></td>
            <td style="font-family: monospace; color: #38bdf8;">${r.id}</td>
            <td><strong>${r.spot_name}</strong><br><small>${r.basin_id}</small></td>
            <td>${r.author}</td>
            <td><span class="status-pill status-${r.status}">${r.status}</span></td>
            <td>
                ${r.status === 'pending' ? `<button class="btn btn-approve" onclick="approveReport('${r.id}')">✅ 批准</button>` : ''}
                <button class="btn btn-delete" onclick="deleteReport('${r.id}')">🔴 刪除</button>
            </td>
        </tr>
    `).join('');
}

window.switchTab = function(tab) {
    document.getElementById('section-reports').style.display = tab === 'reports' ? 'block' : 'none';
    document.getElementById('section-spots').style.display = tab === 'spots' ? 'block' : 'none';
    
    // Update button styles
    const reportsBtn = document.getElementById('tab-reports-btn');
    const spotsBtn = document.getElementById('tab-spots-btn');
    
    if (tab === 'reports') {
        reportsBtn.style.background = 'rgba(56, 189, 248, 0.2)';
        reportsBtn.style.color = '#38bdf8';
        spotsBtn.style.background = 'rgba(255,255,255,0.05)';
        spotsBtn.style.color = '#94a3b8';
        fetchAdminReports();
    } else {
        spotsBtn.style.background = 'rgba(56, 189, 248, 0.2)';
        spotsBtn.style.color = '#38bdf8';
        reportsBtn.style.background = 'rgba(255,255,255,0.05)';
        reportsBtn.style.color = '#94a3b8';
        fetchAdminSpots();
    }
};

async function fetchAdminSpots() {
    try {
        const res = await fetch(`${API_BASE}/admin/spots`, {
            headers: { 'X-Admin-Password': adminPass }
        });
        const spots = await res.json();
        renderAdminSpots(spots);
    } catch (err) { alert("釣點載入失敗"); }
}

function renderAdminSpots(spots) {
    const tbody = document.getElementById('admin-spots-table');
    tbody.innerHTML = spots.map(s => `
        <tr>
            <td style="color: #64748b; font-family: monospace;">#${s.id}</td>
            <td><strong style="color: #38bdf8;">${s.name}</strong></td>
            <td style="font-size: 0.85rem; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${s.desc}</td>
            <td>
                <input type="text" id="map-url-${s.id}" value="${s.map_url || ''}" placeholder="貼上 Google Maps 網址" 
                    style="width: 100%; padding: 5px; background: #000; color: #fff; border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; font-size: 0.8rem;">
            </td>
            <td>
                <button class="btn btn-approve" onclick="updateSpot(${s.id})">💾 儲存</button>
            </td>
        </tr>
    `).join('');
}

window.updateSpot = async function(id) {
    const mapUrl = document.getElementById(`map-url-${id}`).value;
    try {
        const res = await fetch(`${API_BASE}/admin/spots/${id}`, {
            method: 'PUT',
            headers: { 
                'X-Admin-Password': adminPass,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ map_url: mapUrl })
        });
        if (res.ok) alert("✅ 釣點資訊已更新");
    } catch (err) { alert("更新失敗"); }
};

window.approveReport = async function(id) {
    if (!confirm("確定要批准並發布這則戰報嗎？")) return;
    try {
        const res = await fetch(`${API_BASE}/admin/approve/${id}`, {
            method: 'POST',
            headers: { 'X-Admin-Password': adminPass }
        });
        if (res.ok) {
            fetchAdminReports();
        }
    } catch (err) { alert("操作失敗"); }
};

window.deleteReport = async function(id) {
    if (!confirm("⚠️ 確定要永久刪除這則戰報與照片嗎？此動作無法復原。")) return;
    try {
        const res = await fetch(`${API_BASE}/admin/delete/${id}`, {
            method: 'DELETE',
            headers: { 'X-Admin-Password': adminPass }
        });
        if (res.ok) {
            fetchAdminReports();
        }
    } catch (err) { alert("操作失敗"); }
};
