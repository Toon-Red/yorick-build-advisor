// ============================================================================
// Decision Tree Editor — Visual node-graph editor for build logic
// ============================================================================

// --- Data Model ---

let treeData = null;       // current tree JSON
let treeChampion = '';     // current champion
let nodeIdCounter = 0;
let selectedNodeId = null;
let treeDirty = false;
let treeDirection = 'TB';  // TB = top-bottom, LR = left-right

function newId() { return 'n_' + (nodeIdCounter++); }

function createNode(type, extra = {}) {
    const node = { id: newId(), type, ...extra };
    if (type === 'ROOT') {
        node.label = extra.label || 'Champion';
        node.children = [];
    } else if (type === 'IF') {
        node.condition = extra.condition || { field: 'enemy', op: 'in', value: [] };
        node.label = extra.label || '';
        node.children_true = [];
        node.children_false = [];
    } else if (type === 'SWITCH') {
        node.field = extra.field || 'enemy_bucket';
        node.label = extra.label || '';
        node.cases = extra.cases || [
            { label: 'default', match: '*', children: [] }
        ];
    } else if (type === 'SET') {
        node.assignments = extra.assignments || [];
        node.children = [];
    } else if (type === 'GROUP') {
        node.label = extra.label || 'Group';
        node.collapsed = false;
        node.children = [];
    }
    return node;
}

function getChildren(node) {
    if (!node) return [];
    if (node.type === 'IF') {
        return [
            ...(node.children_true || []),
            ...(node.children_false || [])
        ];
    }
    if (node.type === 'SWITCH') {
        const kids = [];
        for (const c of (node.cases || [])) {
            kids.push(...(c.children || []));
        }
        return kids;
    }
    return node.children || [];
}

function getBranches(node) {
    // Returns structured branches for rendering connectors with labels
    if (node.type === 'IF') {
        return [
            { label: 'True', children: node.children_true || [] },
            { label: 'False', children: node.children_false || [] },
        ];
    }
    if (node.type === 'SWITCH') {
        return (node.cases || []).map(c => ({
            label: c.label,
            children: c.children || [],
        }));
    }
    return [{ label: '', children: node.children || [] }];
}

function findNode(root, id) {
    if (!root) return null;
    if (root.id === id) return root;
    for (const child of getChildren(root)) {
        const found = findNode(child, id);
        if (found) return found;
    }
    return null;
}

function findParent(root, id) {
    if (!root) return null;
    const branches = getBranches(root);
    for (const branch of branches) {
        for (const child of branch.children) {
            if (child.id === id) return { parent: root, branch };
            const found = findParent(child, id);
            if (found) return found;
        }
    }
    return null;
}

function removeNodeFromTree(root, id) {
    const info = findParent(root, id);
    if (!info) return false;
    const idx = info.branch.children.findIndex(c => c.id === id);
    if (idx >= 0) {
        info.branch.children.splice(idx, 1);
        return true;
    }
    return false;
}

function addChildToNode(parent, child, branchIndex = 0) {
    if (parent.type === 'IF') {
        if (branchIndex === 0) (parent.children_true = parent.children_true || []).push(child);
        else (parent.children_false = parent.children_false || []).push(child);
    } else if (parent.type === 'SWITCH') {
        const c = parent.cases[branchIndex];
        if (c) (c.children = c.children || []).push(child);
    } else {
        (parent.children = parent.children || []).push(child);
    }
}

function reindexIds(node) {
    node.id = newId();
    for (const child of getChildren(node)) reindexIds(child);
}

function treeToJSON() {
    return {
        champion: treeChampion,
        version: 1,
        root: treeData,
    };
}

function treeFromJSON(json) {
    treeChampion = json.champion || '';
    treeData = json.root || null;
    // Recount IDs
    nodeIdCounter = 0;
    function countIds(node) {
        if (!node) return;
        const num = parseInt(node.id?.replace('n_', '') || '0');
        if (num >= nodeIdCounter) nodeIdCounter = num + 1;
        for (const child of getChildren(node)) countIds(child);
    }
    countIds(treeData);
}


// --- Layout Engine ---

const LAYOUT = {
    nodeW: 200,
    nodeH: 72,
    gapX: 28,
    gapY: 110,
    branchGapX: 40,  // extra gap between IF true/false branches
};

function computeLayout(root) {
    const positions = new Map();
    if (!root) return positions;

    // Pass 1: measure subtree widths bottom-up
    function measure(node) {
        if (node.type === 'GROUP' && node.collapsed) return LAYOUT.nodeW;

        const branches = getBranches(node);
        let totalW = 0;
        let hasBranches = false;

        for (const branch of branches) {
            if (branch.children.length === 0) continue;
            hasBranches = true;
            let branchW = 0;
            for (let i = 0; i < branch.children.length; i++) {
                const cw = measure(branch.children[i]);
                branchW += cw;
                if (i > 0) branchW += LAYOUT.gapX;
            }
            branch._width = Math.max(branchW, LAYOUT.nodeW);
            totalW += branch._width;
        }

        if (hasBranches) {
            const activeBranches = branches.filter(b => b.children.length > 0);
            totalW += (activeBranches.length - 1) * LAYOUT.branchGapX;
        }

        node._subtreeW = hasBranches ? Math.max(totalW, LAYOUT.nodeW) : LAYOUT.nodeW;
        return node._subtreeW;
    }

    // Pass 2: assign positions top-down
    function assign(node, cx, depth) {
        positions.set(node.id, {
            x: cx - LAYOUT.nodeW / 2,
            y: depth * LAYOUT.gapY,
            w: LAYOUT.nodeW,
            h: LAYOUT.nodeH,
        });

        if (node.type === 'GROUP' && node.collapsed) return;

        const branches = getBranches(node);
        const activeBranches = branches.filter(b => b.children.length > 0);
        if (activeBranches.length === 0) return;

        let totalW = activeBranches.reduce((s, b) => s + (b._width || LAYOUT.nodeW), 0)
            + (activeBranches.length - 1) * LAYOUT.branchGapX;
        let left = cx - totalW / 2;

        for (const branch of activeBranches) {
            const bw = branch._width || LAYOUT.nodeW;
            const branchCx = left + bw / 2;

            // Position children within this branch
            let childLeft = branchCx - bw / 2;
            for (const child of branch.children) {
                const cw = child._subtreeW || LAYOUT.nodeW;
                assign(child, childLeft + cw / 2, depth + 1);
                childLeft += cw + LAYOUT.gapX;
            }

            left += bw + LAYOUT.branchGapX;
        }
    }

    measure(root);
    assign(root, 0, 0);

    // Normalize so minimum x is 40
    let minX = Infinity;
    for (const p of positions.values()) {
        if (p.x < minX) minX = p.x;
    }
    const offsetX = 40 - minX;
    for (const p of positions.values()) {
        p.x += offsetX;
    }

    return positions;
}


// --- Renderer ---

function renderTree() {
    const canvas = document.getElementById('tree-canvas');
    if (!canvas || !treeData) return;

    const positions = computeLayout(treeData);

    // Compute canvas size
    let maxX = 0, maxY = 0;
    for (const p of positions.values()) {
        if (p.x + p.w > maxX) maxX = p.x + p.w;
        if (p.y + p.h > maxY) maxY = p.y + p.h;
    }

    canvas.innerHTML = '';

    // SVG layer for connectors
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'tree-svg');
    svg.setAttribute('width', maxX + 80);
    svg.setAttribute('height', maxY + 80);
    canvas.appendChild(svg);

    // Node container
    const nodesDiv = document.createElement('div');
    nodesDiv.className = 'tree-nodes';
    nodesDiv.style.width = (maxX + 80) + 'px';
    nodesDiv.style.height = (maxY + 80) + 'px';
    canvas.appendChild(nodesDiv);

    // Render connectors
    renderConnectors(svg, treeData, positions);

    // Render nodes
    renderNodes(nodesDiv, treeData, positions);
}

function renderConnectors(svg, root, positions) {
    function draw(parent, child, label) {
        const pp = positions.get(parent.id);
        const cp = positions.get(child.id);
        if (!pp || !cp) return;

        const x1 = pp.x + pp.w / 2;
        const y1 = pp.y + pp.h;
        const x2 = cp.x + cp.w / 2;
        const y2 = cp.y;
        const midY = (y1 + y2) / 2;

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', `M${x1},${y1} C${x1},${midY} ${x2},${midY} ${x2},${y2}`);
        path.setAttribute('class', 'tree-connector');
        svg.appendChild(path);

        if (label) {
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', (x1 + x2) / 2);
            text.setAttribute('y', midY - 6);
            text.setAttribute('class', 'tree-connector-label');
            text.textContent = label;
            svg.appendChild(text);
        }
    }

    function walk(node) {
        if (node.type === 'GROUP' && node.collapsed) return;
        const branches = getBranches(node);
        for (const branch of branches) {
            for (const child of branch.children) {
                draw(node, child, branch.label);
                walk(child);
            }
        }
    }
    walk(root);
}

function renderNodes(container, root, positions) {
    function walk(node) {
        const pos = positions.get(node.id);
        if (!pos) return;

        const el = document.createElement('div');
        el.className = `tree-node tree-node-${node.type.toLowerCase()}`;
        el.dataset.nodeId = node.id;
        el.style.left = pos.x + 'px';
        el.style.top = pos.y + 'px';
        el.style.width = pos.w + 'px';
        el.style.minHeight = pos.h + 'px';

        if (node.id === selectedNodeId) el.classList.add('selected');

        el.innerHTML = buildNodeHTML(node);

        el.addEventListener('click', (e) => {
            e.stopPropagation();
            selectNode(node.id);
        });

        el.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            e.stopPropagation();
            showContextMenu(node.id, e.clientX, e.clientY);
        });

        container.appendChild(el);

        if (!(node.type === 'GROUP' && node.collapsed)) {
            for (const child of getChildren(node)) walk(child);
        }
    }
    walk(root);
}

function buildNodeHTML(node) {
    switch (node.type) {
        case 'ROOT':
            return `<div class="node-header node-header-root">
                <span class="node-icon">👤</span>
                <span class="node-title">${esc(node.label || treeChampion)}</span>
            </div>`;

        case 'IF':
            return `<div class="node-header node-header-if">
                <span class="node-icon">◆</span>
                <span class="node-title">IF</span>
            </div>
            <div class="node-body">${formatCondition(node.condition)}</div>`;

        case 'SWITCH':
            const caseCount = (node.cases || []).length;
            return `<div class="node-header node-header-switch">
                <span class="node-icon">⬡</span>
                <span class="node-title">SWITCH</span>
            </div>
            <div class="node-body">${esc(node.field)} (${caseCount} cases)</div>`;

        case 'SET':
            const chips = (node.assignments || []).map(a => {
                const color = setFieldColor(a.key);
                return `<span class="set-chip" style="border-color:${color}">
                    <span class="set-key" style="color:${color}">${esc(a.key)}</span>
                    <span class="set-val">${esc(String(a.value))}</span>
                </span>`;
            }).join('');
            return `<div class="node-header node-header-set">
                <span class="node-icon">●</span>
                <span class="node-title">SET</span>
            </div>
            <div class="node-body node-body-set">${chips || '<em>empty</em>'}</div>`;

        case 'GROUP':
            const collapseIcon = node.collapsed ? '▶' : '▼';
            return `<div class="node-header node-header-group">
                <span class="node-collapse" onclick="event.stopPropagation(); toggleCollapse('${node.id}')">${collapseIcon}</span>
                <span class="node-title">${esc(node.label)}</span>
            </div>`;

        default:
            return `<div class="node-header"><span>${esc(node.type)}</span></div>`;
    }
}

function formatCondition(cond) {
    if (!cond) return '<em>no condition</em>';
    const val = Array.isArray(cond.value)
        ? cond.value.map(v => esc(v)).join(', ')
        : esc(String(cond.value));
    return `<span class="cond-field">${esc(cond.field)}</span>
            <span class="cond-op">${esc(cond.op)}</span>
            <span class="cond-val">${val}</span>`;
}

function setFieldColor(key) {
    const colors = {
        rune_page: '#5588cc',
        shards: '#5588cc',
        resolve_code: '#5588cc',
        item_build: '#cc8833',
        starter_items: '#cc8833',
        items: '#cc8833',
        summoners: '#44aa44',
        summoner_spells: '#44aa44',
        difficulty: '#cc4444',
        special_note: '#cc4444',
    };
    return colors[key] || '#888888';
}

function esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}


// --- Interaction ---

function selectNode(id) {
    selectedNodeId = id;
    document.querySelectorAll('.tree-node.selected').forEach(el => el.classList.remove('selected'));
    const el = document.querySelector(`.tree-node[data-node-id="${id}"]`);
    if (el) el.classList.add('selected');
}

function toggleCollapse(id) {
    const node = findNode(treeData, id);
    if (node && node.type === 'GROUP') {
        node.collapsed = !node.collapsed;
        renderTree();
    }
}

function showContextMenu(nodeId, x, y) {
    hideContextMenu();
    const node = findNode(treeData, nodeId);
    if (!node) return;

    const menu = document.createElement('div');
    menu.className = 'tree-context-menu';
    menu.style.left = x + 'px';
    menu.style.top = y + 'px';
    menu.id = 'tree-ctx-menu';

    const items = [];

    // Edit
    items.push({ label: 'Edit Node', action: () => openNodeEditor(nodeId) });

    // Add children — determine which branches are available
    if (node.type === 'IF') {
        items.push({ label: 'Add to True branch', action: () => addNodePrompt(nodeId, 0) });
        items.push({ label: 'Add to False branch', action: () => addNodePrompt(nodeId, 1) });
    } else if (node.type === 'SWITCH') {
        (node.cases || []).forEach((c, i) => {
            items.push({ label: `Add to "${c.label}"`, action: () => addNodePrompt(nodeId, i) });
        });
        items.push({ label: 'Add new case', action: () => addSwitchCase(nodeId) });
    } else {
        items.push({ label: 'Add Child', action: () => addNodePrompt(nodeId, 0) });
    }

    // Delete (not root)
    if (node.type !== 'ROOT') {
        items.push({ label: 'Delete', action: () => deleteNode(nodeId), danger: true });
    }

    for (const item of items) {
        const row = document.createElement('div');
        row.className = 'ctx-item' + (item.danger ? ' ctx-danger' : '');
        row.textContent = item.label;
        row.addEventListener('click', (e) => {
            e.stopPropagation();
            hideContextMenu();
            item.action();
        });
        menu.appendChild(row);
    }

    document.body.appendChild(menu);

    // Close on click outside
    setTimeout(() => {
        document.addEventListener('click', hideContextMenu, { once: true });
    }, 10);
}

function hideContextMenu() {
    const m = document.getElementById('tree-ctx-menu');
    if (m) m.remove();
}

function addNodePrompt(parentId, branchIndex) {
    const parent = findNode(treeData, parentId);
    if (!parent) return;

    // Show a quick type picker
    const types = ['IF', 'SWITCH', 'SET', 'GROUP'];
    const menu = document.createElement('div');
    menu.className = 'tree-context-menu';
    menu.id = 'tree-ctx-menu';

    // Position near center of screen
    menu.style.left = '50%';
    menu.style.top = '40%';
    menu.style.transform = 'translate(-50%, -50%)';

    const title = document.createElement('div');
    title.className = 'ctx-title';
    title.textContent = 'Add Node';
    menu.appendChild(title);

    for (const t of types) {
        const row = document.createElement('div');
        row.className = 'ctx-item';
        row.textContent = t;
        row.addEventListener('click', (e) => {
            e.stopPropagation();
            hideContextMenu();
            const child = createNode(t);
            addChildToNode(parent, child, branchIndex);
            treeDirty = true;
            renderTree();
            openNodeEditor(child.id);
        });
        menu.appendChild(row);
    }

    document.body.appendChild(menu);
    setTimeout(() => {
        document.addEventListener('click', hideContextMenu, { once: true });
    }, 10);
}

function addSwitchCase(nodeId) {
    const node = findNode(treeData, nodeId);
    if (!node || node.type !== 'SWITCH') return;
    const label = prompt('Case label:');
    if (!label) return;
    node.cases.push({ label, match: label, children: [] });
    treeDirty = true;
    renderTree();
}

function deleteNode(nodeId) {
    if (!confirm('Delete this node and all its children?')) return;
    removeNodeFromTree(treeData, nodeId);
    if (selectedNodeId === nodeId) selectedNodeId = null;
    treeDirty = true;
    renderTree();
}


// --- Node Editor Modal ---

function openNodeEditor(nodeId) {
    const node = findNode(treeData, nodeId);
    if (!node) return;

    const overlay = document.getElementById('tree-node-modal');
    const body = document.getElementById('tree-modal-body');
    if (!overlay || !body) return;

    body.innerHTML = buildEditorForm(node);
    overlay.classList.add('active');

    // Wire up save button
    document.getElementById('tree-modal-save').onclick = () => {
        saveEditorForm(node);
        overlay.classList.remove('active');
        treeDirty = true;
        renderTree();
    };
}

function closeNodeEditor() {
    const overlay = document.getElementById('tree-node-modal');
    if (overlay) overlay.classList.remove('active');
}

function buildEditorForm(node) {
    switch (node.type) {
        case 'ROOT':
            return `<h3>Root Node</h3>
                <label>Champion Label</label>
                <input type="text" id="ne-label" value="${esc(node.label || '')}" class="ne-input">`;

        case 'IF':
            return `<h3>IF Condition</h3>
                <label>Field</label>
                <select id="ne-cond-field" class="ne-input">
                    ${condFieldOptions(node.condition?.field)}
                </select>
                <label>Operator</label>
                <select id="ne-cond-op" class="ne-input">
                    ${condOpOptions(node.condition?.op)}
                </select>
                <label>Value (comma-separated for lists)</label>
                <input type="text" id="ne-cond-value" class="ne-input"
                    value="${esc(Array.isArray(node.condition?.value) ? node.condition.value.join(', ') : String(node.condition?.value || ''))}">
                <label>Label (optional)</label>
                <input type="text" id="ne-label" value="${esc(node.label || '')}" class="ne-input">`;

        case 'SWITCH':
            return `<h3>SWITCH</h3>
                <label>Field to switch on</label>
                <select id="ne-switch-field" class="ne-input">
                    ${condFieldOptions(node.field)}
                </select>
                <label>Label (optional)</label>
                <input type="text" id="ne-label" value="${esc(node.label || '')}" class="ne-input">
                <div class="ne-cases">
                    <h4>Cases</h4>
                    ${(node.cases || []).map((c, i) => `
                        <div class="ne-case-row">
                            <input type="text" class="ne-input ne-case-label" value="${esc(c.label)}" data-idx="${i}">
                            <input type="text" class="ne-input ne-case-match" value="${esc(c.match)}" data-idx="${i}" placeholder="match value">
                        </div>
                    `).join('')}
                </div>`;

        case 'SET':
            return `<h3>SET Values</h3>
                <div id="ne-assignments">
                    ${(node.assignments || []).map((a, i) => setAssignmentRow(a, i)).join('')}
                </div>
                <button class="ne-btn" onclick="addSetRow()">+ Add Assignment</button>`;

        case 'GROUP':
            return `<h3>Group</h3>
                <label>Label</label>
                <input type="text" id="ne-label" value="${esc(node.label || '')}" class="ne-input">`;

        default:
            return '<p>Unknown node type</p>';
    }
}

function condFieldOptions(selected) {
    const fields = [
        'enemy', 'enemy_bucket', 'keystone', 'matchup.difficulty',
        'matchup.item_category', 'matchup.shard_override', 'matchup.exhaust_viable',
        'matchup.summoner_spells',
    ];
    return fields.map(f =>
        `<option value="${f}" ${f === selected ? 'selected' : ''}>${f}</option>`
    ).join('');
}

function condOpOptions(selected) {
    const ops = ['in', 'not_in', 'eq', 'neq', 'has_tag'];
    return ops.map(o =>
        `<option value="${o}" ${o === selected ? 'selected' : ''}>${o}</option>`
    ).join('');
}

function setAssignmentRow(a, i) {
    const keys = [
        'rune_page', 'item_build', 'shards', 'summoners', 'starter_items',
        'resolve_code', 'difficulty', 'special_note', 'reasoning',
    ];
    const keyOpts = keys.map(k =>
        `<option value="${k}" ${k === a.key ? 'selected' : ''}>${k}</option>`
    ).join('');

    return `<div class="ne-assign-row" data-idx="${i}">
        <select class="ne-input ne-assign-key">${keyOpts}</select>
        <input type="text" class="ne-input ne-assign-val" value="${esc(String(a.value || ''))}">
        <button class="ne-btn-sm ne-btn-danger" onclick="removeSetRow(${i})">×</button>
    </div>`;
}

function addSetRow() {
    const container = document.getElementById('ne-assignments');
    if (!container) return;
    const idx = container.children.length;
    const html = setAssignmentRow({ key: 'rune_page', value: '', ref_type: 'literal' }, idx);
    container.insertAdjacentHTML('beforeend', html);
}

function removeSetRow(idx) {
    const rows = document.querySelectorAll('#ne-assignments .ne-assign-row');
    if (rows[idx]) rows[idx].remove();
}

function saveEditorForm(node) {
    switch (node.type) {
        case 'ROOT':
        case 'GROUP':
            node.label = document.getElementById('ne-label')?.value || node.label;
            break;

        case 'IF': {
            const field = document.getElementById('ne-cond-field')?.value || 'enemy';
            const op = document.getElementById('ne-cond-op')?.value || 'in';
            const rawVal = document.getElementById('ne-cond-value')?.value || '';
            let value;
            if (op === 'in' || op === 'not_in') {
                value = rawVal.split(',').map(s => s.trim()).filter(Boolean);
            } else {
                value = rawVal.trim();
            }
            node.condition = { field, op, value };
            node.label = document.getElementById('ne-label')?.value || '';
            break;
        }

        case 'SWITCH': {
            node.field = document.getElementById('ne-switch-field')?.value || node.field;
            node.label = document.getElementById('ne-label')?.value || '';
            // Update case labels/matches
            document.querySelectorAll('.ne-case-label').forEach(el => {
                const idx = parseInt(el.dataset.idx);
                if (node.cases[idx]) node.cases[idx].label = el.value;
            });
            document.querySelectorAll('.ne-case-match').forEach(el => {
                const idx = parseInt(el.dataset.idx);
                if (node.cases[idx]) node.cases[idx].match = el.value;
            });
            break;
        }

        case 'SET': {
            const rows = document.querySelectorAll('#ne-assignments .ne-assign-row');
            node.assignments = [];
            rows.forEach(row => {
                const key = row.querySelector('.ne-assign-key')?.value;
                const val = row.querySelector('.ne-assign-val')?.value;
                if (key) node.assignments.push({ key, value: val, ref_type: 'literal' });
            });
            break;
        }
    }
}


// --- Import / Export ---

function exportTree() {
    if (!treeData) { alert('No tree to export'); return; }
    const json = JSON.stringify(treeToJSON(), null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${treeChampion || 'tree'}_decision_tree.json`;
    a.click();
    URL.revokeObjectURL(url);
}

function importTree() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (ev) => {
            try {
                const json = JSON.parse(ev.target.result);
                treeFromJSON(json);
                // Update champion selector
                const sel = document.getElementById('tree-champion-select');
                if (sel && treeChampion) sel.value = treeChampion;
                treeDirty = true;
                renderTree();
            } catch (err) {
                alert('Invalid JSON: ' + err.message);
            }
        };
        reader.readAsText(file);
    };
    input.click();
}


// --- API Persistence ---

async function loadTreeForChampion(champion) {
    treeChampion = champion;
    try {
        // Find guides for this champion
        const r = await fetch('/api/guides');
        if (r.ok) {
            const data = await r.json();
            const guides = (data.guides || []).filter(g =>
                g.champion.toLowerCase() === champion.toLowerCase()
            );
            if (guides.length > 0) {
                // Load the first (active) guide's tree
                const gr = await fetch(`/api/guides/${encodeURIComponent(guides[0].guide_id)}`);
                if (gr.ok) {
                    const guide = await gr.json();
                    if (guide && guide.root) {
                        treeFromJSON(guide);
                        treeDirty = false;
                        renderTree();
                        return;
                    }
                }
            }
        }
    } catch {}

    // No guide exists — generate default for Yorick, empty for others
    nodeIdCounter = 0;
    if (champion === 'Yorick') {
        generateYorickTree();
    } else {
        treeData = createNode('ROOT', { label: champion });
    }
    treeDirty = false;
    renderTree();
}

async function saveTree() {
    if (!treeChampion || !treeData) return;
    try {
        // Find existing guide for this champion
        const lr = await fetch('/api/guides');
        const ld = await lr.json();
        const guides = (ld.guides || []).filter(g =>
            g.champion.toLowerCase() === treeChampion.toLowerCase()
        );

        if (guides.length > 0) {
            // Update existing guide's tree
            const gr = await fetch(`/api/guides/${encodeURIComponent(guides[0].guide_id)}`);
            const guide = await gr.json();
            guide.root = treeToJSON().root;
            const r = await fetch(`/api/guides/${encodeURIComponent(guides[0].guide_id)}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(guide),
            });
            if (r.ok) {
                treeDirty = false;
                showTreeToast('Saved to guide!');
            }
        } else {
            // Create new guide with just the tree
            const newGuide = {
                champion: treeChampion,
                guide_name: `${treeChampion} Guide`,
                author: 'Custom',
                root: treeToJSON().root,
                data: { matchups: {}, rune_pages: {}, item_builds: {}, buckets: {} },
            };
            const r = await fetch('/api/guides/import', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newGuide),
            });
            if (r.ok) {
                treeDirty = false;
                showTreeToast('Guide created!');
            }
        }
    } catch (err) {
        showTreeToast('Save failed: ' + err.message, true);
    }
}

function showTreeToast(msg, isError = false) {
    const toast = document.createElement('div');
    toast.className = 'tree-toast' + (isError ? ' tree-toast-error' : '');
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2500);
}


// --- Generate Default Yorick Tree ---

function generateYorickTree() {
    nodeIdCounter = 0;
    const root = createNode('ROOT', { label: 'Yorick' });

    // Resolve Adaptation
    const resolveGroup = createNode('GROUP', { label: 'Resolve Adaptation' });
    const resolveIf1 = createNode('IF', {
        condition: { field: 'enemy_bucket', op: 'in', value: ['RANGED_POKE_CHAMPS'] },
        label: 'Poke matchup?'
    });
    const setB = createNode('SET', { assignments: [
        { key: 'resolve_code', value: 'B', ref_type: 'literal' },
    ]});
    const resolveIf2 = createNode('IF', {
        condition: { field: 'enemy_bucket', op: 'in', value: ['BURST_CC_CHAMPS'] },
        label: 'Burst/CC matchup?'
    });
    const setC = createNode('SET', { assignments: [
        { key: 'resolve_code', value: 'C', ref_type: 'literal' },
    ]});
    const setA = createNode('SET', { assignments: [
        { key: 'resolve_code', value: 'A', ref_type: 'literal' },
    ]});
    resolveIf2.children_true.push(setC);
    resolveIf2.children_false.push(setA);
    resolveIf1.children_true.push(setB);
    resolveIf1.children_false.push(resolveIf2);
    resolveGroup.children.push(resolveIf1);

    // Shards
    const shardGroup = createNode('GROUP', { label: 'Shard Selection' });
    const shardSwitch = createNode('SWITCH', {
        field: 'enemy_bucket',
        cases: [
            { label: 'MS champs', match: 'MS_SHARD_CHAMPS', children: [
                createNode('SET', { assignments: [{ key: 'shards', value: 'AS / MS / Tenacity', ref_type: 'literal' }] })
            ]},
            { label: 'Adaptive champs', match: 'ADAPTIVE_SHARD_CHAMPS', children: [
                createNode('SET', { assignments: [{ key: 'shards', value: 'AS / AF / Tenacity', ref_type: 'literal' }] })
            ]},
            { label: 'default', match: '*', children: [
                createNode('SET', { assignments: [{ key: 'shards', value: 'AS / HP / Tenacity', ref_type: 'literal' }] })
            ]},
        ]
    });
    shardGroup.children.push(shardSwitch);

    // Summoner Spells
    const summGroup = createNode('GROUP', { label: 'Summoner Spells' });
    const summIf1 = createNode('IF', {
        condition: { field: 'enemy_bucket', op: 'in', value: ['EXHAUST_PRIMARY'] },
        label: 'Exhaust primary?'
    });
    const summSet1 = createNode('SET', { assignments: [{ key: 'summoners', value: 'Exhaust/TP', ref_type: 'literal' }] });
    const summIf2 = createNode('IF', {
        condition: { field: 'enemy_bucket', op: 'in', value: ['EXHAUST_SECONDARY'] },
        label: 'Exhaust secondary?'
    });
    const summSet2 = createNode('SET', { assignments: [{ key: 'summoners', value: 'Exhaust viable (Ghost/Ignite default)', ref_type: 'literal' }] });
    const summSet3 = createNode('SET', { assignments: [{ key: 'summoners', value: 'Ghost/Ignite', ref_type: 'literal' }] });
    summIf2.children_true.push(summSet2);
    summIf2.children_false.push(summSet3);
    summIf1.children_true.push(summSet1);
    summIf1.children_false.push(summIf2);
    summGroup.children.push(summIf1);

    // Starter Items
    const starterGroup = createNode('GROUP', { label: 'Starter Items' });
    const starterSwitch = createNode('SWITCH', {
        field: 'enemy_bucket',
        cases: [
            { label: 'Bad AD', match: 'BAD_AD_MATCHUPS', children: [
                createNode('SET', { assignments: [{ key: 'starter_items', value: 'Cloth Armor + Refillable', ref_type: 'literal' }] })
            ]},
            { label: 'AP Melee', match: 'AP_MELEE_CHAMPS', children: [
                createNode('SET', { assignments: [{ key: 'starter_items', value: 'Long Sword + Refillable', ref_type: 'literal' }] })
            ]},
            { label: 'AP Poke', match: 'AP_POKE_CHAMPS', children: [
                createNode('SET', { assignments: [{ key: 'starter_items', value: "Doran's Shield", ref_type: 'literal' }] })
            ]},
            { label: 'Ranged AD', match: 'RANGED_AD_CHAMPS', children: [
                createNode('SET', { assignments: [{ key: 'starter_items', value: "Doran's Shield", ref_type: 'literal' }] })
            ]},
            { label: 'default', match: '*', children: [
                createNode('SET', { assignments: [{ key: 'starter_items', value: "Doran's Blade + HP Pot", ref_type: 'literal' }] })
            ]},
        ]
    });
    starterGroup.children.push(starterSwitch);

    // Item Path
    const itemGroup = createNode('GROUP', { label: 'Item Path' });
    const itemSwitch = createNode('SWITCH', {
        field: 'enemy_bucket',
        cases: [
            { label: 'Sheen/Iceborn', match: 'SHEEN_ICEBORN_CHAMPS', children: [
                createNode('SET', { assignments: [{ key: 'item_build', value: 'Iceborn Cleaver', ref_type: 'item_build' }] })
            ]},
            { label: 'Tiamat/Titanic', match: 'TIAMAT_TITANIC_CHAMPS', children: [
                createNode('SET', { assignments: [{ key: 'item_build', value: 'Titanic Breaker', ref_type: 'item_build' }] })
            ]},
            { label: 'Eclipse Poke', match: 'ECLIPSE_POKE_CHAMPS', children: [
                createNode('SET', { assignments: [{ key: 'item_build', value: 'Eclipse Poke', ref_type: 'item_build' }] })
            ]},
            { label: 'Liandry Shred', match: 'LIANDRY_SHRED_CHAMPS', children: [
                createNode('SET', { assignments: [{ key: 'item_build', value: 'Liandry Tank Shred', ref_type: 'item_build' }] })
            ]},
            { label: 'default', match: '*', children: [
                createNode('SET', { assignments: [{ key: 'item_build', value: 'Default BBC', ref_type: 'item_build' }] })
            ]},
        ]
    });
    itemGroup.children.push(itemSwitch);

    root.children.push(resolveGroup, shardGroup, summGroup, starterGroup, itemGroup);
    treeData = root;
    treeChampion = 'Yorick';
}


// --- Init ---

function initTreeEditor() {
    const champSelect = document.getElementById('tree-champion-select');
    if (champSelect) {
        champSelect.addEventListener('change', () => {
            if (treeDirty && !confirm('Unsaved changes. Switch anyway?')) {
                champSelect.value = treeChampion;
                return;
            }
            loadTreeForChampion(champSelect.value);
        });
    }

    // Click on canvas background deselects
    const canvas = document.getElementById('tree-canvas');
    if (canvas) {
        canvas.addEventListener('click', () => {
            selectedNodeId = null;
            document.querySelectorAll('.tree-node.selected').forEach(el => el.classList.remove('selected'));
        });
    }
}
