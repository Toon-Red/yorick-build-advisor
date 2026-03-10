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
    // Force auto-import checkboxes off (prevent Edge from restoring cached state)
    document.getElementById('auto-runes').checked = false;
    document.getElementById('auto-items').checked = false;
    document.getElementById('auto-spells').checked = false;

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
            badge.title = `Port ${data.port} | PID ${data.pid}`;
        } else {
            badge.textContent = 'LCU: Off';
            badge.className = 'lcu-badge lcu-off';
            if (data.port) {
                badge.title = `Port ${data.port} unreachable (PID ${data.pid})`;
            } else if (data.lockfile_exists === false) {
                badge.title = `Lockfile not found: ${data.lockfile_path}`;
            } else {
                badge.title = 'League client not detected';
            }
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
            generateBuildForEnemy(data.predicted_opponent, true);
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

async function generateBuildForEnemy(enemyName, autoImport = false) {
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
        if (autoImport) handleAutoImport(data);
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
    // Auto-import from first profile's first option
    const profiles = data.profiles || [];
    if (!profiles.length || !profiles[0].options.length) return;

    clearTimeout(autoImportDebounce);
    autoImportDebounce = setTimeout(async () => {
        const opt = profiles[0].options[0];
        const doRunes = document.getElementById('auto-runes').checked;
        const doItems = document.getElementById('auto-items').checked;
        const doSpells = document.getElementById('auto-spells').checked;

        if (doRunes) await importRunesData(opt);
        if (doItems) await importItemsData(data.champion, opt);
        if (doSpells) await importSpellsData(opt);
    }, 2000);
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

    const profiles = data.profiles || [];

    // Backwards compat: if old format (data.options), wrap it
    if (!profiles.length && data.options) {
        profiles.push({
            guide_id: '_legacy', guide_name: 'Built-in Engine',
            author: 'System', options: data.options, count: data.options.length,
        });
    }

    let globalIdx = 0;
    profiles.forEach((profile, pi) => {
        const profileDiv = document.createElement('div');
        profileDiv.className = 'profile-group';
        profileDiv.dataset.profileId = profile.guide_id;

        const profileHeader = document.createElement('div');
        profileHeader.className = 'profile-header';
        profileHeader.innerHTML = `
            <button class="profile-toggle" onclick="toggleProfile(this)" title="Minimize/Expand">▼</button>
            <span class="profile-name">${profile.guide_name}</span>
            <span class="profile-author">by ${profile.author}</span>
            <span class="profile-count">${profile.count} option${profile.count !== 1 ? 's' : ''}</span>
            <label class="profile-hide-label"><input type="checkbox" class="profile-hide-check" onchange="toggleProfileVisibility(this)"> Hide</label>
        `;
        profileDiv.appendChild(profileHeader);

        const profileBody = document.createElement('div');
        profileBody.className = 'profile-body';

        profile.options.forEach((opt, i) => {
            const card = document.createElement('div');
            const isFirst = (pi === 0 && i === 0);
            card.className = 'build-option' + (isFirst ? ' expanded' : '');

            card.innerHTML = `
                <div class="option-header" onclick="toggleOption(this)">
                    <span class="option-number">${isFirst ? '<span class="option-star">★</span>' : '#' + (globalIdx + 1)}</span>
                    <span class="option-keystone">${opt.keystone}</span>
                    <span class="option-build-name">— ${opt.item_build_name}</span>
                    <span class="option-expand">${isFirst ? '▼' : '▶'}</span>
                </div>
                <div class="option-body">
                    ${renderOptionBody(opt, pi, i)}
                </div>
            `;

            profileBody.appendChild(card);
            globalIdx++;
        });

        profileDiv.appendChild(profileBody);
        list.appendChild(profileDiv);
    });
}

function toggleProfile(btn) {
    const body = btn.closest('.profile-group').querySelector('.profile-body');
    const isCollapsed = body.style.display === 'none';
    body.style.display = isCollapsed ? '' : 'none';
    btn.textContent = isCollapsed ? '▼' : '▶';
}

function toggleProfileVisibility(checkbox) {
    const group = checkbox.closest('.profile-group');
    const body = group.querySelector('.profile-body');
    const header = group.querySelector('.profile-header');
    if (checkbox.checked) {
        body.style.display = 'none';
        header.classList.add('profile-hidden');
    } else {
        body.style.display = '';
        header.classList.remove('profile-hidden');
    }
}

function renderOptionBody(opt, profileIdx, optIdx) {
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
            <div class="detail-value icon-row">${renderSpellIcons(opt.summoners)}</div>
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
        <div class="import-buttons" data-pi="${profileIdx}" data-oi="${optIdx}">
            <button class="btn-import" onclick="importRunes(${profileIdx},${optIdx})">Import Runes</button>
            <button class="btn-import" onclick="importItems(${profileIdx},${optIdx})">Import Items</button>
            <button class="btn-import" onclick="importSpells(${profileIdx},${optIdx})">Import Spells</button>
        </div>
    `;
}

const SPELL_KEYS = {
    'ghost': 'SummonerHaste', 'ignite': 'SummonerDot', 'flash': 'SummonerFlash',
    'exhaust': 'SummonerExhaust', 'tp': 'SummonerTeleport', 'teleport': 'SummonerTeleport',
    'barrier': 'SummonerBarrier', 'heal': 'SummonerHeal', 'cleanse': 'SummonerBoost',
    'smite': 'SummonerSmite',
};

function renderSpellIcons(summonerText) {
    if (!summonerText) return '';
    // Extract spell names: "Ghost/Ignite", "Exhaust viable (Ghost/Ignite default)", etc.
    // Find the primary pair (first X/Y pattern)
    const pairMatch = summonerText.match(/(\w+)\s*\/\s*(\w+)/);
    let spells = [];
    if (pairMatch) {
        spells = [pairMatch[1], pairMatch[2]];
    }
    const icons = spells.map(s => {
        const key = SPELL_KEYS[s.toLowerCase()];
        if (!key) return `<span class="spell-name">${s}</span>`;
        const url = `https://ddragon.leagueoflegends.com/cdn/${ddragonVersion}/img/spell/${key}.png`;
        return `<img class="rune-icon" src="${url}" alt="${s}" title="${s}">`;
    }).join('');
    // Show the full text too for context (e.g. "Exhaust viable")
    const extraText = summonerText.replace(/(\w+)\s*\/\s*(\w+)/, '').replace(/[()]/g, '').trim();
    return icons + (extraText ? `<span style="margin-left:8px;font-size:0.8rem;color:#6b6b80">${extraText}</span>` : '');
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

function getOption(pi, oi) {
    if (!lastBuildData) return null;
    const profiles = lastBuildData.profiles || [];
    if (!profiles[pi] || !profiles[pi].options[oi]) return null;
    return profiles[pi].options[oi];
}

async function importRunes(pi, oi) {
    const opt = getOption(pi, oi);
    if (!opt) { console.error('importRunes: no option at', pi, oi); return; }
    const result = await importRunesData(opt);
    flashButton(pi, oi, 'runes', result);
}

async function importItems(pi, oi) {
    const opt = getOption(pi, oi);
    if (!opt) { console.error('importItems: no option at', pi, oi); return; }
    const result = await importItemsData(lastBuildData.champion, opt);
    flashButton(pi, oi, 'items', result);
}

async function importSpells(pi, oi) {
    const opt = getOption(pi, oi);
    if (!opt) { console.error('importSpells: no option at', pi, oi); return; }
    const result = await importSpellsData(opt);
    flashButton(pi, oi, 'spells', result);
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
        if (!result.success) console.warn('Rune import failed:', result.error);
        return result.success;
    } catch (e) {
        console.error('Rune import error:', e);
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
        if (!result.success) console.warn('Item import failed:', result.error);
        return result.success;
    } catch (e) {
        console.error('Item import error:', e);
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
        if (!result.success) console.warn('Spell import failed:', result.error);
        return result.success;
    } catch (e) {
        console.error('Spell import error:', e);
        return false;
    }
}

function flashButton(pi, oi, type, success) {
    const container = document.querySelector(`.import-buttons[data-pi="${pi}"][data-oi="${oi}"]`);
    if (!container) return;
    const buttons = container.querySelectorAll('.btn-import');
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
