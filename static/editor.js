// Guide Editor — editor.js
const API = '';

// State
let guide = null;          // Full guide JSON
let guideList = [];        // Available guides
let allChampions = [];     // DDragon champion list
let ddragonVersion = '';
let runeTreeData = [];     // Full rune tree from DDragon
let shardData = [];        // Shard definitions
let allItems = [];         // All items from DDragon
let dirty = false;         // Unsaved changes flag
let currentTab = 'matchups';

// --- Init ---

async function init() {
    const [guideResp, champResp, verResp] = await Promise.all([
        fetch(API + '/api/guides').then(r => r.json()),
        fetch(API + '/api/ddragon/champions').then(r => r.json()),
        fetch(API + '/api/ddragon/version').then(r => r.json()),
    ]);

    guideList = guideResp.guides || [];
    allChampions = champResp.champions || [];
    ddragonVersion = verResp.version;

    // Populate guide selector
    const sel = document.getElementById('guide-select');
    sel.innerHTML = guideList.length
        ? guideList.map(g => `<option value="${g.guide_id}">${g.guide_name} (${g.champion}) by ${g.author}</option>`).join('')
        : '<option value="">No guides found</option>';

    // Load first guide
    if (guideList.length) {
        await loadGuide(guideList[0].guide_id);
    }

    // Warn on leave with unsaved changes
    window.addEventListener('beforeunload', (e) => {
        if (dirty) { e.preventDefault(); e.returnValue = ''; }
    });
}

async function loadSelectedGuide() {
    const id = document.getElementById('guide-select').value;
    if (id) await loadGuide(id);
}

async function loadGuide(guideId) {
    try {
        const resp = await fetch(API + '/api/guides/' + encodeURIComponent(guideId));
        guide = await resp.json();
        dirty = false;
        updateSaveStatus();
        document.getElementById('save-btn').disabled = false;
        renderAll();
    } catch (e) {
        toast('Failed to load guide: ' + e.message, 'error');
    }
}

// --- Tab Switching ---

function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.getElementById('panel-' + tab).classList.add('active');

    // Lazy-load DDragon data for tabs that need it
    if (tab === 'runes' && !runeTreeData.length) loadRuneData();
    if (tab === 'items' && !allItems.length) loadItemData();
    if (tab === 'preview') {
        populatePreviewDropdown();
        if (!runeTreeData.length) loadRuneData();
    }
}

// --- Render All ---

function renderAll() {
    if (!guide) return;
    updateCounts();
    renderMatchups();
    renderRunePages();
    renderItemBuilds();
    renderSkillOrders();
    renderBuckets();
}

function updateCounts() {
    const d = guide.data || {};
    document.getElementById('count-matchups').textContent = Object.keys(d.matchups || {}).length;
    document.getElementById('count-runes').textContent = Object.keys(d.rune_pages || {}).length;
    document.getElementById('count-items').textContent = Object.keys(d.item_builds || {}).length;
    // Skill orders are from the Python module, not guide JSON. Show what's in guide if present.
    const skillCount = d.skill_orders ? Object.keys(d.skill_orders).length : 3;
    document.getElementById('count-skills').textContent = skillCount;
    document.getElementById('count-buckets').textContent = Object.keys(d.buckets || {}).length;
}

// --- HTML Escaping ---

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// --- Matchup Table ---

function renderMatchups() {
    const tbody = document.getElementById('matchup-tbody');
    const matchups = guide.data.matchups || {};
    const sorted = Object.entries(matchups).sort((a, b) => a[0].localeCompare(b[0]));

    tbody.innerHTML = sorted.map(([enemy, m]) => {
        const keystones = (m.keystones || []).map(k =>
            `<span class="keystone-chip">${escapeHtml(k)}</span>`
        ).join('');
        const tags = (m.tags || []).map(t =>
            `<span class="tag-chip">${escapeHtml(t)}</span>`
        ).join('');

        return `<tr data-enemy="${escapeHtml(enemy)}">
            <td><button class="edit-row-btn" onclick="editMatchup('${enemy.replace(/'/g, "\\'")}')" title="Edit">&#9998;</button></td>
            <td><strong>${escapeHtml(enemy)}</strong></td>
            <td><span class="diff-badge diff-${escapeHtml(m.difficulty)}">${escapeHtml(m.difficulty)}</span></td>
            <td><div class="keystones-list">${keystones}</div></td>
            <td><span style="font-size:0.8rem;color:#8888a0">${escapeHtml(m.item_category || 'default')}</span></td>
            <td>${tags}</td>
            <td class="advice-cell" title="${escapeHtml(m.advice || '')}">${escapeHtml(m.advice || '')}</td>
            <td style="font-size:0.8rem;color:#8888a0">${escapeHtml(m.summoner_spells || 'Ghost/Ignite')}</td>
        </tr>`;
    }).join('');
}

function filterMatchups() {
    const search = document.getElementById('matchup-search').value.toLowerCase();
    const diff = document.getElementById('matchup-diff-filter').value;
    const rows = document.querySelectorAll('#matchup-tbody tr');

    rows.forEach(row => {
        const enemy = row.dataset.enemy.toLowerCase();
        const rowDiff = row.querySelector('.diff-badge')?.textContent || '';
        const matchSearch = !search || enemy.includes(search);
        const matchDiff = !diff || rowDiff === diff;
        row.style.display = (matchSearch && matchDiff) ? '' : 'none';
    });
}

// --- Matchup Edit Modal ---

let modalKeystones = [];
let modalTags = [];

function editMatchup(enemy) {
    const m = guide.data.matchups[enemy];
    if (!m) return;

    document.getElementById('modal-title').textContent = 'Edit Matchup: ' + enemy;
    document.getElementById('modal-enemy-key').value = enemy;
    document.getElementById('modal-enemy').value = enemy;
    document.getElementById('modal-difficulty').value = m.difficulty || 'Medium';
    document.getElementById('modal-item-category').value = m.item_category || 'default';
    document.getElementById('modal-summoners').value = m.summoner_spells || 'Ghost/Ignite';
    document.getElementById('modal-shard-override').value = m.shard_override || '';
    document.getElementById('modal-exhaust').value = m.exhaust_viable ? 'true' : 'false';
    document.getElementById('modal-special-note').value = m.special_note || '';
    document.getElementById('modal-advice').value = m.advice || '';
    document.getElementById('modal-delete-btn').style.display = '';

    modalKeystones = [...(m.keystones || [])];
    modalTags = [...(m.tags || [])];
    renderChips('modal-keystones-container', 'modal-keystones-input', modalKeystones);
    renderChips('modal-tags-container', 'modal-tags-input', modalTags);

    document.getElementById('matchup-modal').classList.remove('hidden');
}

function addMatchup() {
    document.getElementById('modal-title').textContent = 'Add Matchup';
    document.getElementById('modal-enemy-key').value = '';
    document.getElementById('modal-enemy').value = '';
    document.getElementById('modal-enemy').readOnly = false;
    document.getElementById('modal-difficulty').value = 'Medium';
    document.getElementById('modal-item-category').value = 'default';
    document.getElementById('modal-summoners').value = 'Ghost/Ignite';
    document.getElementById('modal-shard-override').value = '';
    document.getElementById('modal-exhaust').value = 'false';
    document.getElementById('modal-special-note').value = '';
    document.getElementById('modal-advice').value = '';
    document.getElementById('modal-delete-btn').style.display = 'none';

    modalKeystones = ['Grasp-1'];
    modalTags = [];
    renderChips('modal-keystones-container', 'modal-keystones-input', modalKeystones);
    renderChips('modal-tags-container', 'modal-tags-input', modalTags);

    document.getElementById('matchup-modal').classList.remove('hidden');

    // Add datalist for champion autocomplete
    setupChampionAutocomplete();
}

function setupChampionAutocomplete() {
    const input = document.getElementById('modal-enemy');
    let listId = 'champ-datalist';
    let dl = document.getElementById(listId);
    if (!dl) {
        dl = document.createElement('datalist');
        dl.id = listId;
        document.body.appendChild(dl);
    }
    dl.innerHTML = allChampions.map(c => `<option value="${c}">`).join('');
    input.setAttribute('list', listId);
}

function closeModal() {
    document.getElementById('matchup-modal').classList.add('hidden');
    document.getElementById('modal-enemy').readOnly = true;
}

function saveMatchupEdit() {
    const origKey = document.getElementById('modal-enemy-key').value;
    const enemy = document.getElementById('modal-enemy').value.trim();
    if (!enemy) { toast('Champion name required', 'error'); return; }

    const matchup = {
        difficulty: document.getElementById('modal-difficulty').value,
        keystones: [...modalKeystones],
        item_category: document.getElementById('modal-item-category').value,
        tags: [...modalTags],
        shard_override: document.getElementById('modal-shard-override').value || null,
        exhaust_viable: document.getElementById('modal-exhaust').value === 'true',
        summoner_spells: document.getElementById('modal-summoners').value || 'Ghost/Ignite',
        special_note: document.getElementById('modal-special-note').value,
        advice: document.getElementById('modal-advice').value,
    };

    // If renamed, remove old key
    if (origKey && origKey !== enemy) {
        delete guide.data.matchups[origKey];
    }
    guide.data.matchups[enemy] = matchup;

    markDirty();
    closeModal();
    renderMatchups();
    updateCounts();
    toast('Matchup saved: ' + enemy, 'success');
}

function deleteMatchup() {
    const enemy = document.getElementById('modal-enemy-key').value;
    if (!enemy) return;
    if (!confirm(`Delete matchup for ${enemy}?`)) return;

    delete guide.data.matchups[enemy];
    markDirty();
    closeModal();
    renderMatchups();
    updateCounts();
    toast('Matchup deleted: ' + enemy, 'success');
}

// --- Chip Input ---

function renderChips(containerId, inputId, arr) {
    const container = document.getElementById(containerId);
    const input = document.getElementById(inputId);

    // Remove existing chips (keep input)
    container.querySelectorAll('.chip-item').forEach(el => el.remove());

    arr.forEach((val, i) => {
        const chip = document.createElement('span');
        chip.className = 'chip-item';
        chip.innerHTML = `${val} <button class="chip-remove" onclick="removeChip('${containerId}','${inputId}',${i})">&times;</button>`;
        container.insertBefore(chip, input);
    });

    // Setup input handler
    input.onkeydown = (e) => {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            const val = input.value.trim().replace(/,/g, '');
            if (val) {
                arr.push(val);
                input.value = '';
                renderChips(containerId, inputId, arr);
            }
        } else if (e.key === 'Backspace' && !input.value && arr.length) {
            arr.pop();
            renderChips(containerId, inputId, arr);
        }
    };
}

function removeChip(containerId, inputId, idx) {
    // Determine which array this belongs to
    if (containerId === 'modal-keystones-container') {
        modalKeystones.splice(idx, 1);
        renderChips(containerId, inputId, modalKeystones);
    } else if (containerId === 'modal-tags-container') {
        modalTags.splice(idx, 1);
        renderChips(containerId, inputId, modalTags);
    }
}

// --- Rune Pages ---

async function loadRuneData() {
    try {
        const resp = await fetch(API + '/api/ddragon/all-runes');
        const data = await resp.json();
        runeTreeData = data.rune_trees || [];
        shardData = data.shards || [];
        renderRunePages();
    } catch (e) {
        console.error('Failed to load rune data:', e);
    }
}

function runeIconUrl(runeId) {
    // Search through rune trees for the icon
    for (const tree of runeTreeData) {
        if (tree.id === runeId) return `https://ddragon.leagueoflegends.com/cdn/img/${tree.icon}`;
        for (const slot of tree.slots || []) {
            for (const rune of slot.runes || []) {
                if (rune.id === runeId) return `https://ddragon.leagueoflegends.com/cdn/img/${rune.icon}`;
            }
        }
    }
    // Check shards
    const shard = shardData.find(s => s.id === runeId);
    if (shard) return shard.icon;
    return '';
}

function runeName(runeId) {
    for (const tree of runeTreeData) {
        if (tree.id === runeId) return tree.name;
        for (const slot of tree.slots || []) {
            for (const rune of slot.runes || []) {
                if (rune.id === runeId) return rune.name;
            }
        }
    }
    const shard = shardData.find(s => s.id === runeId);
    if (shard) return shard.name;
    return String(runeId);
}

function renderRunePages() {
    const container = document.getElementById('rune-cards');
    const pages = guide.data.rune_pages || {};

    container.innerHTML = Object.entries(pages).map(([name, page]) => {
        const perkIds = page.selected_perk_ids || [];
        const mainRunes = perkIds.slice(0, 4);
        const secRunes = perkIds.slice(4, 6);
        const shards = perkIds.slice(6, 9);

        const mainIcons = mainRunes.map((id, i) =>
            `<img class="icon-img ${i === 0 ? 'keystone' : ''}" src="${runeIconUrl(id)}" alt="${runeName(id)}" title="${runeName(id)}" onerror="this.style.display='none'">`
        ).join('');
        const secIcons = secRunes.map(id =>
            `<img class="icon-img" src="${runeIconUrl(id)}" alt="${runeName(id)}" title="${runeName(id)}" onerror="this.style.display='none'">`
        ).join('');
        const shardIcons = shards.map(id =>
            `<img class="icon-img" style="width:24px;height:24px" src="${runeIconUrl(id)}" alt="${runeName(id)}" title="${runeName(id)}" onerror="this.style.display='none'">`
        ).join('');

        return `<div class="data-card">
            <div class="data-card-header">
                <span class="data-card-title">${escapeHtml(name)}</span>
                <button class="edit-row-btn" onclick="editRunePage('${name.replace(/'/g, "\\'")}')" title="Edit">&#9998;</button>
            </div>
            <div class="icon-row" style="margin-bottom:6px">${mainIcons}</div>
            <div class="icon-row" style="margin-bottom:4px">${secIcons}</div>
            <div class="icon-row">${shardIcons}</div>
        </div>`;
    }).join('');
}

function editRunePage(name) {
    toast('Rune page visual editor coming soon — edit in guide JSON for now', 'error');
}

function addRunePage() {
    toast('Rune page visual editor coming soon — edit in guide JSON for now', 'error');
}

// --- Item Builds ---

async function loadItemData() {
    try {
        const resp = await fetch(API + '/api/ddragon/all-items');
        const data = await resp.json();
        allItems = data.items || [];
        renderItemBuilds();
    } catch (e) {
        console.error('Failed to load item data:', e);
    }
}

function itemIconUrl(itemId) {
    return `https://ddragon.leagueoflegends.com/cdn/${ddragonVersion}/img/item/${itemId}.png`;
}

function itemName(itemId) {
    const item = allItems.find(i => i.id === itemId);
    return item ? item.name : String(itemId);
}

function renderItemBuilds() {
    const container = document.getElementById('item-cards');
    const builds = guide.data.item_builds || {};

    container.innerHTML = Object.entries(builds).map(([name, build]) => {
        const coreIds = build.core || [];
        const coreIcons = coreIds.map(id =>
            `<img class="icon-img item" src="${itemIconUrl(id)}" alt="${itemName(id)}" title="${itemName(id)}" onerror="this.style.display='none'">`
        ).join('<span style="color:#333;margin:0 2px">→</span>');

        const starterIds = build.starter || [];
        const starterIcons = starterIds.map(id =>
            `<img class="icon-img item" style="width:24px;height:24px" src="${itemIconUrl(id)}" title="${itemName(id)}" onerror="this.style.display='none'">`
        ).join('');

        return `<div class="data-card">
            <div class="data-card-header">
                <span class="data-card-title">${escapeHtml(name)}</span>
                <button class="edit-row-btn" onclick="editItemBuild('${name.replace(/'/g, "\\'")}')" title="Edit">&#9998;</button>
            </div>
            <div class="data-card-body">
                <div style="margin-bottom:4px"><span style="color:#6b6b80;font-size:0.7rem">STARTER:</span> ${starterIcons}</div>
                <div><span style="color:#6b6b80;font-size:0.7rem">CORE:</span> <span class="icon-row">${coreIcons}</span></div>
            </div>
        </div>`;
    }).join('');
}

function filterItemBuilds() {
    const search = document.getElementById('item-search').value.toLowerCase();
    const cards = document.querySelectorAll('#item-cards .data-card');
    cards.forEach(card => {
        const name = card.querySelector('.data-card-title').textContent.toLowerCase();
        card.style.display = (!search || name.includes(search)) ? '' : 'none';
    });
}

function editItemBuild(name) {
    toast('Item build visual editor coming soon — edit in guide JSON for now', 'error');
}

function addItemBuild() {
    toast('Item build visual editor coming soon — edit in guide JSON for now', 'error');
}

// --- Skill Orders ---

function renderSkillOrders() {
    const container = document.getElementById('skill-cards');
    // Skill orders come from data/skill_orders.py, not the guide JSON
    // Fetch them from the Python module via a build query to introspect
    // For now, render from hardcoded knowledge of the 3 templates
    const skillOrders = [
        { id: 'w_stack', name: 'W-Stack vs Immobile', levels: ['Q','E','W','Q','W','R','W','Q','Q','Q','R','E','E','E','E','R','W','W'], max: ['Q','E','W'], desc: 'Put 3 points into W by Lvl 7, then max Q, then E, W last.' },
        { id: 'standard', name: 'Standard Q-Max', levels: ['Q','E','W','E','Q','R','Q','Q','Q','E','R','W','E','W','E','R','W','W'], max: ['Q','E','W'], desc: 'Start Q, 2 points into E, then Q max.' },
        { id: 'e_max', name: 'E-Max vs Ranged', levels: ['E','Q','W','E','Q','R','E','E','E','Q','R','Q','Q','W','W','R','W','W'], max: ['E','Q','W'], desc: 'E max vs ranged when using Comet or Aery.' },
    ];

    container.innerHTML = skillOrders.map(so => {
        const abilities = ['Q', 'W', 'E', 'R'];
        let grid = '<div class="skill-grid-compact">';
        // Header row
        grid += '<div class="skill-cell label"></div>';
        for (let lvl = 1; lvl <= 18; lvl++) grid += `<div class="skill-cell header">${lvl}</div>`;
        // Ability rows
        for (const ab of abilities) {
            grid += `<div class="skill-cell label">${ab}</div>`;
            for (let i = 0; i < 18; i++) {
                const isActive = so.levels[i] === ab;
                grid += `<div class="skill-cell${isActive ? ' active' : ''}">${isActive ? ab : ''}</div>`;
            }
        }
        grid += '</div>';

        return `<div class="data-card" style="margin-bottom:12px">
            <div class="data-card-header">
                <div>
                    <span class="data-card-title">${so.name}</span>
                    <span class="data-card-subtitle" style="margin-left:8px">${so.max.join(' > ')} max</span>
                </div>
            </div>
            ${grid}
            <div class="data-card-body" style="margin-top:8px">${so.desc}</div>
        </div>`;
    }).join('');
}

function addSkillOrder() {
    toast('Skill order editor coming soon — edit data/skill_orders.py for now', 'error');
}

// --- Buckets ---

function renderBuckets() {
    const container = document.getElementById('bucket-cards');
    const buckets = guide.data.buckets || {};

    container.innerHTML = Object.entries(buckets).sort((a, b) => a[0].localeCompare(b[0])).map(([name, champs]) => {
        const champChips = (champs || []).sort().map(c =>
            `<span class="bucket-champ">${c}</span>`
        ).join('');

        return `<div class="bucket-card">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <span class="bucket-name">${name}</span>
                <span style="font-size:0.75rem;color:#6b6b80">${(champs || []).length} champs</span>
            </div>
            <div class="bucket-champs">${champChips}</div>
        </div>`;
    }).join('');
}

// --- Preview ---

function populatePreviewDropdown() {
    const sel = document.getElementById('preview-enemy');
    if (sel.options.length > 1) return; // Already populated

    const matchups = guide.data.matchups || {};
    const sorted = Object.keys(matchups).sort();

    // Known matchups group
    let html = '<option value="">Select enemy...</option>';
    html += '<optgroup label="Guide Matchups">';
    sorted.forEach(e => {
        html += `<option value="${e}">${e} (${matchups[e].difficulty})</option>`;
    });
    html += '</optgroup>';

    // All other champions
    const knownSet = new Set(sorted);
    const others = allChampions.filter(c => !knownSet.has(c));
    if (others.length) {
        html += '<optgroup label="Other Champions">';
        others.forEach(c => { html += `<option value="${c}">${c}</option>`; });
        html += '</optgroup>';
    }

    sel.innerHTML = html;
}

async function runPreview() {
    const enemy = document.getElementById('preview-enemy').value;
    const output = document.getElementById('preview-output');
    if (!enemy) {
        output.innerHTML = '<p style="color:#6b6b80;text-align:center;padding:40px 0">Select an enemy champion to preview</p>';
        return;
    }

    output.innerHTML = '<p style="color:#6b6b80;text-align:center;padding:40px 0">Loading...</p>';

    try {
        // Execute the guide for this matchup
        const resp = await fetch(API + '/api/guides/' + encodeURIComponent(guide.guide_id) + '/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enemy }),
        });
        const data = await resp.json();

        if (data.error) {
            output.innerHTML = `<p style="color:#e06666">${data.error}</p>`;
            return;
        }

        const builds = data.builds || [];
        if (!builds.length) {
            output.innerHTML = '<p style="color:#e06666">No builds returned for this matchup</p>';
            return;
        }

        // Also get matchup info
        const matchup = guide.data.matchups[enemy];
        const difficulty = matchup ? matchup.difficulty : 'Unknown';
        const advice = matchup ? matchup.advice : '';
        const specialNote = matchup ? matchup.special_note : '';

        let html = `<div style="margin-bottom:12px">
            <h3 style="color:#c89b3c;font-size:1rem">Yorick vs ${enemy}
                <span class="diff-badge diff-${difficulty}">${difficulty}</span>
            </h3>
            ${specialNote ? `<div style="color:#ff4444;font-weight:700;font-size:1.1rem;margin:8px 0">${specialNote}</div>` : ''}
        </div>`;

        builds.forEach((build, i) => {
            const perkIds = build.selected_perk_ids || [];
            const runeIcons = perkIds.slice(0, 6).map(id =>
                `<img class="icon-img" src="${runeIconUrl(id)}" alt="${runeName(id)}" title="${runeName(id)}" onerror="this.style.display='none'">`
            ).join('');
            const shardIcons = perkIds.slice(6, 9).map(id =>
                `<img class="icon-img" style="width:24px;height:24px" src="${runeIconUrl(id)}" alt="${runeName(id)}" title="${runeName(id)}" onerror="this.style.display='none'">`
            ).join('');

            const coreIcons = (build.core || []).map(id =>
                `<img class="icon-img item" src="${itemIconUrl(id)}" title="${itemName(id)}" onerror="this.style.display='none'">`
            ).join('<span style="color:#333;margin:0 2px">→</span>');

            const starterIcons = (build.starter || []).map(id =>
                `<img class="icon-img item" style="width:24px;height:24px" src="${itemIconUrl(id)}" title="${itemName(id)}" onerror="this.style.display='none'">`
            ).join('+');

            const so = build.skill_order || {};

            html += `<div class="preview-option">
                <div class="preview-option-header">
                    ${i === 0 ? '<span style="color:#c89b3c">★</span>' : '#' + (i + 1)}
                    ${build.keystone} — ${build.item_build_name}
                </div>
                <div class="preview-row">
                    <span class="preview-label">Runes</span>
                    <span class="icon-row">${runeIcons}</span>
                </div>
                <div class="preview-row">
                    <span class="preview-label">Shards</span>
                    <span class="icon-row">${shardIcons}</span>
                    <span style="color:#6b6b80;font-size:0.75rem;margin-left:6px">${build.resolve_code || ''}</span>
                </div>
                <div class="preview-row">
                    <span class="preview-label">Summoners</span>
                    <span class="preview-value">${build.summoners || ''}</span>
                </div>
                <div class="preview-row">
                    <span class="preview-label">Starter</span>
                    <span class="icon-row">${starterIcons}</span>
                    <span style="color:#6b6b80;font-size:0.8rem;margin-left:6px">${build.starter_info?.name || ''}</span>
                </div>
                <div class="preview-row">
                    <span class="preview-label">Core</span>
                    <span class="icon-row">${coreIcons}</span>
                </div>
                ${so.name ? `<div class="preview-row">
                    <span class="preview-label">Skill Order</span>
                    <span class="preview-value">${so.name} (${(so.max_order||[]).join(' > ')} max)</span>
                </div>` : ''}
                <div class="preview-advice">"${build.reasoning || advice || 'No advice'}"</div>
            </div>`;
        });

        output.innerHTML = html;
    } catch (e) {
        output.innerHTML = `<p style="color:#e06666">Preview failed: ${e.message}</p>`;
    }
}

// --- Save / Export ---

function markDirty() {
    dirty = true;
    updateSaveStatus();
}

function updateSaveStatus() {
    const el = document.getElementById('save-status');
    if (dirty) {
        el.textContent = 'Unsaved changes';
        el.className = 'save-status unsaved';
    } else {
        el.textContent = 'Saved';
        el.className = 'save-status saved';
    }
}

async function saveGuide() {
    if (!guide) return;
    const btn = document.getElementById('save-btn');
    btn.disabled = true;
    btn.textContent = 'Saving...';

    try {
        const resp = await fetch(API + '/api/guides/' + encodeURIComponent(guide.guide_id), {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(guide),
        });
        const data = await resp.json();
        if (data.ok) {
            dirty = false;
            updateSaveStatus();
            toast('Guide saved!', 'success');
        } else {
            toast('Save failed: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (e) {
        toast('Save failed: ' + e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Save';
    }
}

async function exportGuide() {
    if (!guide) return;
    try {
        const resp = await fetch(API + '/api/guides/' + encodeURIComponent(guide.guide_id) + '/export');
        const data = await resp.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${guide.guide_id}.json`;
        a.click();
        URL.revokeObjectURL(url);
        toast('Guide exported!', 'success');
    } catch (e) {
        toast('Export failed: ' + e.message, 'error');
    }
}

// --- Toast ---

function toast(msg, type = 'success') {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = `toast ${type}`;
    setTimeout(() => el.classList.add('hidden'), 3000);
}

// --- Close modal on backdrop click ---
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        closeModal();
    }
});

// --- Boot ---
document.addEventListener('DOMContentLoaded', init);
