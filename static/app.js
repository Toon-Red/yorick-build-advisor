// Yorick Build Advisor — Frontend with Live Detection

const API = '';

// State
let champions = [];
let championMap = {};  // internal_name -> {name, key}
let ddragonVersion = '';
let lastBuildData = null;

// Live detection state
let sseSource = null;
let userOverride = false;
let selectedEnemy = null;
let selectedAllEnemies = false;
let currentEnemies = [];
let autoImportDebounce = null;
let lcuConnected = false;

// --- Init ---

async function init() {
    await loadChampions();
    await checkLCU();
    setupEventListeners();
    startSSEStream();
    checkForUpdates();
    // Re-check LCU every 10s
    setInterval(checkLCU, 10000);
}

async function checkForUpdates() {
    try {
        const r = await fetch(API + '/api/update/check');
        const data = await r.json();
        if (data.update_available) {
            const banner = document.createElement('div');
            banner.className = 'update-banner';
            banner.innerHTML = `Update v${data.latest_version} available! <button onclick="installUpdate(this)">Update Now</button>`;
            document.querySelector('.container').prepend(banner);
        }
    } catch {}
}

async function installUpdate(btn) {
    btn.disabled = true;
    btn.textContent = 'Downloading...';
    try {
        await fetch(API + '/api/update/install', {method: 'POST'});
    } catch {}
}

async function loadChampions() {
    try {
        const resp = await fetch(`${API}/api/ddragon/champions`);
        const data = await resp.json();
        champions = data.champions;
        ddragonVersion = (await (await fetch(`${API}/api/ddragon/version`)).json()).version;
        document.getElementById('ddragon-version').textContent = `v${ddragonVersion}`;

        const matchResp = await fetch(`${API}/api/matchups`);
        const matchData = await matchResp.json();
        const matchupEnemies = new Set(matchData.matchups.map(m => m.enemy));

        const enemySelect = document.getElementById('enemy-select');
        enemySelect.innerHTML = '<option value="">Select enemy...</option>';

        const knownGroup = document.createElement('optgroup');
        knownGroup.label = 'Known Matchups';
        for (const m of matchData.matchups) {
            const opt = document.createElement('option');
            opt.value = m.enemy;
            opt.textContent = `${m.enemy} (${m.difficulty})`;
            knownGroup.appendChild(opt);
        }
        enemySelect.appendChild(knownGroup);

        const otherChamps = champions.filter(c => !matchupEnemies.has(c));
        if (otherChamps.length > 0) {
            const otherGroup = document.createElement('optgroup');
            otherGroup.label = 'Other Champions';
            for (const c of otherChamps) {
                const opt = document.createElement('option');
                opt.value = c;
                opt.textContent = c;
                otherGroup.appendChild(opt);
            }
            enemySelect.appendChild(otherGroup);
        }

        const champSelect = document.getElementById('champion-select');
        champSelect.innerHTML = '';
        for (const c of champions) {
            const opt = document.createElement('option');
            opt.value = c;
            opt.textContent = c;
            if (c === 'Yorick') opt.selected = true;
            champSelect.appendChild(opt);
        }
    } catch (e) {
        console.error('Failed to load champions:', e);
    }
}

async function checkLCU() {
    try {
        const resp = await fetch(`${API}/api/lcu/status`);
        const data = await resp.json();
        const badge = document.getElementById('lcu-status');
        lcuConnected = data.connected;
        if (data.connected) {
            badge.textContent = 'LCU: Connected';
            badge.className = 'lcu-badge lcu-on';
        } else {
            badge.textContent = 'LCU: Off';
            badge.className = 'lcu-badge lcu-off';
        }
    } catch {
        lcuConnected = false;
    }
}

function setupEventListeners() {
    document.getElementById('generate-btn').addEventListener('click', generateBuild);
    document.getElementById('enemy-select').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') generateBuild();
    });
    document.getElementById('enemy-select').addEventListener('change', () => {
        userOverride = true;
        selectedAllEnemies = false;
    });
}

// --- SSE Live Detection ---

function startSSEStream() {
    if (sseSource) {
        sseSource.close();
    }
    sseSource = new EventSource(`${API}/api/lcu/champ-select-stream`);

    sseSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleSSEEvent(data);
    };

    sseSource.onerror = () => {
        // Reconnect after 5s
        setTimeout(() => {
            if (sseSource) sseSource.close();
            startSSEStream();
        }, 5000);
    };
}

function handleSSEEvent(data) {
    const statusBadge = document.getElementById('detect-status');
    const enemyListEl = document.getElementById('enemy-list');

    if (data.type === 'disconnected') {
        statusBadge.textContent = 'LCU not connected';
        statusBadge.className = 'detect-badge detect-idle';
        enemyListEl.innerHTML = '<div class="enemy-placeholder">League client not running</div>';
        return;
    }

    if (data.type === 'end') {
        statusBadge.textContent = 'Champ select ended';
        statusBadge.className = 'detect-badge detect-idle';
        userOverride = false;
        selectedAllEnemies = false;
        return;
    }

    if (data.type === 'update') {
        statusBadge.textContent = 'In Champ Select';
        statusBadge.className = 'detect-badge detect-active';

        currentEnemies = data.enemies || [];
        renderEnemyList(currentEnemies, data.predicted_opponent);

        // Auto-select predicted opponent if user hasn't overridden
        if (!userOverride && data.predicted_opponent) {
            selectedEnemy = data.predicted_opponent;
            selectedAllEnemies = false;
            // Set the manual dropdown too
            const enemySelect = document.getElementById('enemy-select');
            enemySelect.value = data.predicted_opponent;
            // Auto-generate build
            generateBuildForEnemy(data.predicted_opponent);
        }
    }
}

function renderEnemyList(enemies, predictedOpponent) {
    const el = document.getElementById('enemy-list');
    if (!enemies || enemies.length === 0) {
        el.innerHTML = '<div class="enemy-placeholder">Waiting for enemy picks...</div>';
        return;
    }

    let html = '';
    for (const enemy of enemies) {
        const pct = Math.round(enemy.top_probability * 100);
        const isSelected = !selectedAllEnemies && (
            userOverride ? enemy.champion_name === selectedEnemy : enemy.champion_name === predictedOpponent
        );
        const barColor = pct >= 70 ? '#e06666' : pct >= 40 ? '#e69138' : pct >= 15 ? '#ffd966' : '#6b6b80';

        // Get portrait URL from DataDragon
        const champKey = getChampionKey(enemy.champion_name);
        const portraitUrl = `https://ddragon.leagueoflegends.com/cdn/${ddragonVersion}/img/champion/${champKey}.png`;

        html += `
            <div class="enemy-row ${isSelected ? 'selected' : ''}" onclick="selectEnemy('${enemy.champion_name.replace(/'/g, "\\'")}')">
                <img class="enemy-portrait" src="${portraitUrl}" alt="${enemy.champion_name}" onerror="this.style.display='none'">
                <span class="enemy-name">${enemy.champion_name}</span>
                <div class="prob-bar-container">
                    <div class="prob-bar" style="width:${pct}%;background:${barColor}"></div>
                </div>
                <span class="prob-pct">${pct}%</span>
            </div>
        `;
    }

    // "All" option
    html += `
        <div class="enemy-row enemy-all ${selectedAllEnemies ? 'selected' : ''}" onclick="selectAllEnemies()">
            <span class="all-icon">ALL</span>
            <span class="enemy-name">Averaged Build</span>
            <span class="prob-pct" style="color:#c89b3c">Multi</span>
        </div>
    `;

    el.innerHTML = html;
}

function getChampionKey(displayName) {
    // Map display names back to DataDragon internal keys for portrait URLs
    const nameMap = {
        "Aurelion Sol": "AurelionSol",
        "Bel'Veth": "Belveth",
        "Cho'Gath": "Chogath",
        "Dr. Mundo": "DrMundo",
        "Jarvan IV": "JarvanIV",
        "Kai'Sa": "Kaisa",
        "Kha'Zix": "Khazix",
        "Kog'Maw": "KogMaw",
        "K'Sante": "KSante",
        "LeBlanc": "Leblanc",
        "Lee Sin": "LeeSin",
        "Master Yi": "MasterYi",
        "Miss Fortune": "MissFortune",
        "Wukong": "MonkeyKing",
        "Nunu & Willump": "Nunu",
        "Rek'Sai": "RekSai",
        "Renata Glasc": "Renata",
        "Tahm Kench": "TahmKench",
        "Twisted Fate": "TwistedFate",
        "Vel'Koz": "Velkoz",
        "Xin Zhao": "XinZhao",
    };
    return nameMap[displayName] || displayName;
}

function selectEnemy(enemyName) {
    userOverride = true;
    selectedEnemy = enemyName;
    selectedAllEnemies = false;
    renderEnemyList(currentEnemies, null);
    document.getElementById('enemy-select').value = enemyName;
    generateBuildForEnemy(enemyName);
}

function selectAllEnemies() {
    userOverride = true;
    selectedAllEnemies = true;
    selectedEnemy = null;
    renderEnemyList(currentEnemies, null);
    generateMultiBuild();
}

// --- Build Generation ---

async function generateBuildForEnemy(enemyName) {
    const champion = document.getElementById('champion-select').value;
    try {
        const resp = await fetch(`${API}/api/build/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ champion, enemy: enemyName }),
        });
        const data = await resp.json();
        lastBuildData = data;
        renderResults(data);
        handleAutoImport(data);
    } catch (e) {
        console.error('Build query failed:', e);
    }
}

async function generateMultiBuild() {
    const champion = document.getElementById('champion-select').value;
    if (!currentEnemies.length) return;

    const enemies = currentEnemies.map(e => ({
        name: e.champion_name,
        weight: e.top_probability,
    }));

    try {
        const resp = await fetch(`${API}/api/build/query-multi`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ champion, enemies }),
        });
        const data = await resp.json();
        lastBuildData = data;
        renderResults(data);
        handleAutoImport(data);
    } catch (e) {
        console.error('Multi-build query failed:', e);
    }
}

async function generateBuild() {
    const champion = document.getElementById('champion-select').value;
    const enemy = document.getElementById('enemy-select').value;

    if (!enemy) {
        alert('Select an enemy champion');
        return;
    }

    userOverride = true;
    selectedEnemy = enemy;
    selectedAllEnemies = false;

    const btn = document.getElementById('generate-btn');
    btn.disabled = true;
    btn.textContent = 'Loading...';

    try {
        await generateBuildForEnemy(enemy);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Generate Build';
    }
}

// --- Auto Import ---

function handleAutoImport(data) {
    if (!data || !data.options || !data.options.length) return;

    clearTimeout(autoImportDebounce);
    autoImportDebounce = setTimeout(async () => {
        const opt = data.options[0]; // Import the top recommendation
        const doRunes = document.getElementById('auto-runes').checked;
        const doItems = document.getElementById('auto-items').checked;
        const doSpells = document.getElementById('auto-spells').checked;

        if (doRunes) await importRunesData(opt);
        if (doItems) await importItemsData(data.champion, opt);
        if (doSpells) await importSpellsData(opt);
    }, 2000); // 2s debounce to avoid spam during rapid picks
}

// --- Render Results ---

function renderResults(data) {
    const section = document.getElementById('results-section');
    section.classList.remove('hidden');

    const header = document.getElementById('results-header');
    let headerHtml = `<h2>${data.champion} vs ${data.enemy} <span class="difficulty diff-${data.difficulty}">${data.difficulty}</span></h2>`;
    if (data.special_note) {
        headerHtml += `<div class="special-note">${data.special_note}</div>`;
    }
    header.innerHTML = headerHtml;

    const list = document.getElementById('results-list');
    list.innerHTML = '';

    data.options.forEach((opt, i) => {
        const card = document.createElement('div');
        card.className = 'build-option' + (i === 0 ? ' expanded' : '');

        card.innerHTML = `
            <div class="option-header" onclick="toggleOption(this)">
                <span class="option-number">${i === 0 ? '<span class="option-star">★</span>' : '#' + (i + 1)}</span>
                <span class="option-keystone">${opt.keystone}</span>
                <span class="option-build-name">— ${opt.item_build_name}</span>
                <span class="option-expand">${i === 0 ? '▼' : '▶'}</span>
            </div>
            <div class="option-body">
                ${renderOptionBody(opt, i)}
            </div>
        `;

        list.appendChild(card);
    });
}

function renderOptionBody(opt, index) {
    const runeIcons = opt.rune_details.map(r =>
        `<img class="rune-icon" src="${r.icon}" alt="${r.name}" title="${r.name}">`
    ).join('');

    const starterIcons = opt.starter.map(id =>
        renderItemIcon(opt, id)
    ).join('<span class="arrow-sep">+</span>');

    const coreIcons = opt.core.map(id =>
        renderItemIcon(opt, id)
    ).join('<span class="arrow-sep">→</span>');

    const bootsIcons = opt.boots.map(id =>
        renderItemIcon(opt, id)
    ).join(' / ');

    const sitIcons = opt.situational.map(id =>
        renderItemIcon(opt, id)
    ).join(' ');

    return `
        <div class="detail-row">
            <span class="detail-label">Runes</span>
            <div class="detail-value icon-row">${runeIcons}</div>
        </div>
        <div class="detail-row">
            <span class="detail-label">Shards</span>
            <div class="detail-value icon-row">${(opt.shard_details||[]).map(s =>
                `<img class="rune-icon" src="${s.icon}" alt="${s.name}" title="${s.name}">`
            ).join('')}${(opt.shard_details||[]).length === 0 ? opt.shard_info : ''}
            <span style="margin-left:8px;font-size:0.75rem;color:#6b6b80">${opt.resolve_code}</span></div>
        </div>
        <div class="detail-row">
            <span class="detail-label">Summoners</span>
            <div class="detail-value">${opt.summoners}</div>
        </div>
        <div class="detail-row">
            <span class="detail-label">Starter</span>
            <div class="detail-value">
                <span class="icon-row">${starterIcons}</span>
                <span style="margin-left:8px;font-size:0.8rem;color:#6b6b80">${opt.starter_info.name}</span>
            </div>
        </div>
        <div class="detail-row">
            <span class="detail-label">Boots</span>
            <div class="detail-value icon-row">${bootsIcons}</div>
        </div>
        <div class="detail-row">
            <span class="detail-label">Core</span>
            <div class="detail-value icon-row">${coreIcons}</div>
        </div>
        <div class="detail-row">
            <span class="detail-label">Situational</span>
            <div class="detail-value icon-row">${sitIcons}</div>
        </div>
        <div class="reasoning-text">"${opt.reasoning}"</div>
        <div class="import-buttons">
            <button class="btn-import" onclick="importRunes(${index})">Import Runes</button>
            <button class="btn-import" onclick="importItems(${index})">Import Items</button>
            <button class="btn-import" onclick="importSpells(${index})">Import Spells</button>
        </div>
    `;
}

function renderItemIcon(opt, itemId) {
    const detail = opt.item_details[String(itemId)];
    if (!detail) return `<span>[${itemId}]</span>`;
    return `<img class="item-icon" src="${detail.icon}" alt="${detail.name}" title="${detail.name}">`;
}

function toggleOption(headerEl) {
    const card = headerEl.parentElement;
    const isExpanded = card.classList.contains('expanded');
    card.classList.toggle('expanded');
    headerEl.querySelector('.option-expand').textContent = isExpanded ? '▶' : '▼';
}

// --- LCU Import (manual button clicks) ---

async function importRunes(index) {
    if (!lastBuildData) return;
    const opt = lastBuildData.options[index];
    const result = await importRunesData(opt);
    flashButton(index, 'runes', result);
}

async function importItems(index) {
    if (!lastBuildData) return;
    const opt = lastBuildData.options[index];
    const result = await importItemsData(lastBuildData.champion, opt);
    flashButton(index, 'items', result);
}

async function importSpells(index) {
    if (!lastBuildData) return;
    const opt = lastBuildData.options[index];
    const result = await importSpellsData(opt);
    flashButton(index, 'spells', result);
}

// --- LCU Import (shared logic) ---

async function importRunesData(opt) {
    try {
        const resp = await fetch(`${API}/api/lcu/import-runes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: `${opt.keystone} (v2)`,
                primary_style_id: opt.primary_style_id,
                sub_style_id: opt.sub_style_id,
                selected_perk_ids: opt.selected_perk_ids,
            }),
        });
        const result = await resp.json();
        return result.success;
    } catch {
        return false;
    }
}

async function importItemsData(champion, opt) {
    try {
        const resp = await fetch(`${API}/api/lcu/import-items`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                champion,
                starter: opt.starter,
                core: opt.core,
                boots: opt.boots[0] || 0,
                situational: opt.situational,
            }),
        });
        const result = await resp.json();
        return result.success;
    } catch {
        return false;
    }
}

async function importSpellsData(opt) {
    try {
        const resp = await fetch(`${API}/api/lcu/import-spells`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ spells: opt.summoners.split(' ')[0] }),
        });
        const result = await resp.json();
        return result.success;
    } catch {
        return false;
    }
}

function flashButton(optIndex, type, success) {
    const cards = document.querySelectorAll('.build-option');
    if (!cards[optIndex]) return;
    const buttons = cards[optIndex].querySelectorAll('.btn-import');
    const typeMap = { runes: 0, items: 1, spells: 2 };
    const btn = buttons[typeMap[type]];
    if (!btn) return;

    btn.classList.add(success ? 'success' : 'error');
    btn.textContent = success ? 'Imported!' : 'Failed';
    setTimeout(() => {
        btn.classList.remove('success', 'error');
        btn.textContent = `Import ${type.charAt(0).toUpperCase() + type.slice(1)}`;
    }, 2000);
}

// Boot
document.addEventListener('DOMContentLoaded', init);
