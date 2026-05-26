"""
Upgrade CC会话管理中心 HTML to v3.0 — adds 会话三维组织 (Pin/Archive/Folders).
Reads existing HTML, injects new CSS/HTML/JS, writes enhanced HTML.
"""
import re, sys, os

HTML_PATH = os.path.expanduser('~/Desktop/Claude Code/CC会话管理中心.html')
OUT_PATH = os.path.expanduser('~/Desktop/Claude Code/CC会话管理中心.html')

# Backup first
BACKUP = HTML_PATH.replace('.html', '-v2-backup.html')

NEW_CSS = """
/* === v3.0: Sidebar filter tabs === */
.sidebar-tabs { display: flex; border-bottom: 1px solid var(--border); }
.sidebar-tabs .stab { flex: 1; text-align: center; padding: 8px 4px; font-size: 11px; cursor: pointer; color: var(--text2); border-bottom: 2px solid transparent; transition: all .15s; user-select: none; background: none; border-top: none; border-left: none; border-right: none; border-radius: 0; }
.sidebar-tabs .stab:hover { color: var(--accent); background: var(--hover); }
.sidebar-tabs .stab.active { color: var(--accent); border-bottom-color: var(--accent); font-weight: 600; }
.sidebar-tabs .stab .stab-count { font-size: 9px; opacity: .5; margin-left: 2px; }

/* === v3.0: Pinned section === */
.pin-section { border-bottom: 1px solid var(--border); }
.pin-section:empty { display: none; }
.pin-header { padding: 6px 12px; font-size: 10px; font-weight: 700; color: #92400e; background: var(--pin-bg); display: flex; align-items: center; gap: 4px; user-select: none; }
.pin-header .pin-count { font-size: 9px; opacity: .5; margin-left: auto; }
.pin-item { padding: 8px 12px 8px 26px; border-radius: 0; cursor: pointer; transition: background .15s; border-left: 3px solid #f59e0b; font-size: 12px; }
.pin-item:hover { background: var(--hover); }
.pin-item .pin-title { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pin-item .pin-meta { font-size: 10px; color: var(--text2); }

/* === v3.0: Archive section === */
.arch-section { border-top: 1px solid var(--border); }
.arch-section:empty { display: none; }
.arch-header { padding: 6px 12px; font-size: 10px; font-weight: 700; color: var(--text2); background: var(--arch-bg); cursor: pointer; user-select: none; display: flex; align-items: center; gap: 4px; }
.arch-header:hover { opacity: .7; }
.arch-header .arch-chevron { font-size: 10px; transition: transform .3s; }
.arch-body { overflow: hidden; transition: max-height .3s ease; }
.arch-body.collapsed { max-height: 0 !important; }
.arch-body.collapsed + .arch-header .arch-chevron { transform: rotate(-90deg); }
.arch-item { padding: 8px 12px 8px 26px; border-radius: 0; cursor: pointer; transition: background .15s; border-left: 3px solid #9ca3af; font-size: 12px; opacity: .6; }
.arch-item:hover { background: var(--hover); opacity: .8; }
.arch-item .arch-title { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.arch-item .arch-meta { font-size: 10px; color: var(--text2); }

/* === v3.0: Session action buttons === */
.session-item .act-btns { display: flex; gap: 2px; margin-top: 3px; opacity: 0; transition: opacity .15s; }
.session-item:hover .act-btns { opacity: 1; }
.act-btn { font-size: 9px; padding: 1px 5px; border-radius: 4px; border: 1px solid var(--border); background: var(--card-bg); color: var(--text2); cursor: pointer; white-space: nowrap; transition: all .15s; }
.act-btn:hover { border-color: var(--accent); color: var(--accent); }
.act-btn.pin-active { border-color: #f59e0b; color: #92400e; background: #fef9e7; }
.act-btn.arch-active { border-color: #9ca3af; color: #6b7280; }
[data-theme="dark"] .act-btn.pin-active { background: #2a2010; color: #f59e0b; }

/* === v3.0: Folder management === */
.folder-badge { display: inline-block; font-size: 9px; padding: 1px 6px; border-radius: 6px; background: #e0e7ff; color: #4338ca; margin-right: 2px; white-space: nowrap; }
[data-theme="dark"] .folder-badge { background: #1e2040; color: #818cf8; }
.folder-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 101; }
.folder-overlay.open { display: flex; align-items: center; justify-content: center; }
.folder-panel { background: var(--card-bg); border-radius: 12px; padding: 20px; width: min(400px, 90vw); max-height: 70vh; overflow-y: auto; box-shadow: 0 8px 40px rgba(0,0,0,.3); }
.folder-panel h3 { margin-bottom: 12px; font-size: 14px; }
.folder-input-row { display: flex; gap: 6px; margin-bottom: 10px; }
.folder-input-row input { flex: 1; padding: 6px 10px; border: 1px solid var(--border); border-radius: 6px; font-size: 12px; background: var(--bg); color: var(--text); }
.folder-input-row button { padding: 6px 12px; border: 1px solid var(--accent); border-radius: 6px; background: var(--accent); color: #fff; cursor: pointer; font-size: 12px; }
.folder-list-item { display: flex; align-items: center; justify-content: space-between; padding: 6px 8px; border-radius: 6px; font-size: 12px; cursor: pointer; transition: background .15s; }
.folder-list-item:hover { background: var(--hover); }
.folder-list-item .folder-del { opacity: .3; cursor: pointer; font-size: 14px; padding: 2px 6px; border: none; background: none; color: var(--text); border-radius: 4px; }
.folder-list-item .folder-del:hover { opacity: 1; color: #ef4444; }
.folder-panel .close-btn { margin-top: 8px; width: 100%; padding: 6px; border: 1px solid var(--border); border-radius: 6px; background: var(--card-bg); color: var(--text); cursor: pointer; font-size: 12px; }
"""

NEW_HTML_SIDEBAR = """
  <div class="sidebar-tabs" id="sidebarTabs">
    <button class="stab active" onclick="filterByStatus('all')" id="stabAll">全部<span class="stab-count" id="stabAllCount"></span></button>
    <button class="stab" onclick="filterByStatus('active')" id="stabActive">活跃<span class="stab-count" id="stabActiveCount"></span></button>
    <button class="stab" onclick="filterByStatus('archived')" id="stabArchived">已归档<span class="stab-count" id="stabArchCount"></span></button>
  </div>
  <div class="pin-section" id="pinSection"></div>
"""

NEW_HTML_ARCHIVE = """
  <div class="arch-section" id="archSection">
    <div class="arch-body collapsed" id="archBody"></div>
    <div class="arch-header" id="archHeader" onclick="toggleArchiveSection()">
      <span class="arch-chevron">▶</span>📦 已归档 <span id="archCount" style="font-size:9px;opacity:.5;margin-left:auto;"></span>
    </div>
  </div>
"""

NEW_HTML_OVERLAY = """
<div class="folder-overlay" id="folderOverlay" onclick="if(event.target===this)hideFolderPanel()">
  <div class="folder-panel">
    <h3>📁 文件夹管理</h3>
    <div class="folder-input-row">
      <input type="text" id="folderNameInput" placeholder="新建文件夹名称..." onkeydown="if(event.key==='Enter')createFolder()">
      <button onclick="createFolder()">+ 创建</button>
    </div>
    <div id="folderList"></div>
    <button class="close-btn" onclick="hideFolderPanel()">关闭</button>
  </div>
</div>
"""

def main():
    # Read existing HTML
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        html = f.read()

    # Idempotency: skip if already v3.0
    if '/* === v3.0: Sidebar filter tabs === */' in html:
        print('Already v3.0, skipping')
        return

    # Backup
    with open(BACKUP, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Backup: {BACKUP}')

    # 1. Inject CSS: after the existing dark mode art-link/ref-link/ref-url lines
    css_marker = '[data-theme="dark"] .ref-url[style*="fef3c7"] { background: var(--search-bg) !important; }'
    if css_marker in html:
        html = html.replace(css_marker, css_marker + '\n' + NEW_CSS, 1)
    else:
        print('WARNING: CSS marker not found')
        # Fallback: insert before * { margin: 0
        html = html.replace('* { margin: 0; padding: 0; box-sizing: border-box; }',
            NEW_CSS + '\n* { margin: 0; padding: 0; box-sizing: border-box; }', 1)

    # 2. Inject HTML: filter tabs + pin section after tag cloud, before session list
    # Find: <div class="session-list" id="sessList">
    marker2 = '<div class="session-list" id="sessList">'
    if marker2 in html:
        html = html.replace(marker2, NEW_HTML_SIDEBAR + '\n  ' + marker2, 1)
    else:
        print('WARNING: session-list marker not found')

    # 3. Inject HTML: archive section before sidebar closing </div> (the last one before main)
    # Find: </div>\n\n<div class="main">
    marker3 = '<div class="main">'
    if marker3 in html:
        html = html.replace(marker3, NEW_HTML_ARCHIVE + '\n' + marker3, 1)
    else:
        print('WARNING: main div marker not found')

    # 4. Inject HTML: folder overlay before </body>
    marker4 = '</body>'
    if marker4 in html:
        html = html.replace(marker4, NEW_HTML_OVERLAY + '\n' + marker4, 1)

    # 5. Inject JS: Add new localStorage keys, folder/pin/archive functions
    # Insert after the TITLE_KEY / bookmark functions area, before buildTagCloud
    js_marker = "function collapseAllProjects() {"
    new_js = r"""
// ── v3.0: 会话三维组织 ──
var currentStatus = 'all';
const PIN_KEY = 'sess-viewer-pinned';
const ARCH_KEY = 'sess-viewer-archived';
const FOLDER_KEY = 'sess-viewer-folders'; // {folderId: {name, sessions: [sid]}}
const SESS_FOLDER_KEY = 'sess-viewer-session-folders'; // {sid: folderId}

function getPinned() { try { return JSON.parse(localStorage.getItem(PIN_KEY) || '[]'); } catch(e) { return []; } }
function savePinned(arr) { localStorage.setItem(PIN_KEY, JSON.stringify(arr)); rebuildSidebar(); }
function togglePin(sid) { let p = getPinned(); let idx = p.indexOf(sid); if (idx >= 0) p.splice(idx,1); else p.unshift(sid); savePinned(p); }
function isPinned(sid) { return getPinned().includes(sid); }

function getArchived() { try { return JSON.parse(localStorage.getItem(ARCH_KEY) || '[]'); } catch(e) { return []; } }
function saveArchived(arr) { localStorage.setItem(ARCH_KEY, JSON.stringify(arr)); rebuildSidebar(); }
function toggleArchive(sid) { let a = getArchived(); let idx = a.indexOf(sid); if (idx >= 0) a.splice(idx,1); else a.push(sid); saveArchived(a); }
function isArchived(sid) { return getArchived().includes(sid); }

function getFolders() { try { return JSON.parse(localStorage.getItem(FOLDER_KEY) || '{}'); } catch(e) { return {}; } }
function saveFolders(obj) { localStorage.setItem(FOLDER_KEY, JSON.stringify(obj)); }
function getSessionFolders() { try { return JSON.parse(localStorage.getItem(SESS_FOLDER_KEY) || '{}'); } catch(e) { return {}; } }
function saveSessionFolders(obj) { localStorage.setItem(SESS_FOLDER_KEY, JSON.stringify(obj)); }
function getFolderName(fid) { let f = getFolders(); return (f[fid] && f[fid].name) || fid; }

function createFolder() {
  let inp = document.getElementById('folderNameInput');
  let name = inp.value.trim();
  if (!name) return;
  let fid = 'f_' + Date.now();
  let folders = getFolders();
  folders[fid] = { name: name, sessions: [] };
  saveFolders(folders);
  inp.value = '';
  renderFolderPanel();
}

function deleteFolder(fid) {
  if (!confirm('删除文件夹「' + getFolderName(fid) + '」？会话不会被删除。')) return;
  let folders = getFolders();
  delete folders[fid];
  saveFolders(folders);
  // Also remove session assignments
  let sf = getSessionFolders();
  Object.keys(sf).forEach(sid => { if (sf[sid] === fid) delete sf[sid]; });
  saveSessionFolders(sf);
  rebuildSidebar();
  renderFolderPanel();
}

function assignToFolder(sid, fid) {
  let sf = getSessionFolders();
  if (fid) {
    sf[sid] = fid;
    let folders = getFolders();
    if (folders[fid] && folders[fid].sessions.indexOf(sid) < 0) {
      folders[fid].sessions.push(sid);
      saveFolders(folders);
    }
  } else {
    delete sf[sid];
  }
  saveSessionFolders(sf);
  rebuildSidebar();
}

function getSessionFolder(sid) {
  return getSessionFolders()[sid] || '';
}

function filterByStatus(status) {
  currentStatus = status;
  document.querySelectorAll('#sidebarTabs .stab').forEach(s => s.classList.remove('active'));
  document.getElementById('stab' + status.charAt(0).toUpperCase() + status.slice(1)).classList.add('active');
  rebuildSidebar();
}

function toggleArchiveSection() {
  let body = document.getElementById('archBody');
  let icon = document.querySelector('#archHeader .arch-chevron');
  if (body.classList.contains('collapsed')) {
    body.classList.remove('collapsed');
    body.style.maxHeight = body.scrollHeight + 'px';
    if (icon) icon.textContent = '▼';
  } else {
    body.style.maxHeight = body.scrollHeight + 'px';
    requestAnimationFrame(() => {
      body.classList.add('collapsed');
      if (icon) icon.textContent = '▶';
    });
  }
}

function hideFolderPanel() {
  document.getElementById('folderOverlay').classList.remove('open');
}

function showFolderPanel(sid) {
  window._folderTargetSid = sid;
  document.getElementById('folderOverlay').classList.add('open');
  renderFolderPanel();
}

function renderFolderPanel() {
  let folders = getFolders();
  let sf = getSessionFolders();
  let targetSid = window._folderTargetSid || '';
  let currentFid = targetSid ? sf[targetSid] || '' : '';
  let list = document.getElementById('folderList');

  let entries = Object.entries(folders);
  if (entries.length === 0) {
    list.innerHTML = '<div style="font-size:12px;color:var(--text2);padding:8px;">暂无文件夹，创建一个吧</div>';
  } else {
    list.innerHTML = entries.map(([fid, f]) => {
      let isActive = fid === currentFid;
      let count = (f.sessions || []).length;
      return '<div class="folder-list-item" style="' + (isActive ? 'background:var(--hover);font-weight:600;' : '') + '">' +
        '<span onclick="assignToFolder(\'' + targetSid + '\',\'' + (isActive ? '' : fid) + '\');' + (targetSid ? 'hideFolderPanel();' : '') + '" style="flex:1;">' +
        (isActive ? '✅ ' : '📁 ') + esc(f.name) + ' <span style="font-size:10px;opacity:.5;">(' + count + ')</span>' +
        '</span>' +
        '<button class="folder-del" onclick="event.stopPropagation();deleteFolder(\'' + fid + '\')" title="删除文件夹">✕</button>' +
      '</div>';
    }).join('');
  }
}

function rebuildSidebar() {
  let list = document.getElementById('sessList');
  let pinSection = document.getElementById('pinSection');
  let archBody = document.getElementById('archBody');
  let pinned = getPinned();
  let archived = getArchived();
  let sf = getSessionFolders();
  let folders = getFolders();

  // Clear
  list.innerHTML = '';

  // Render pinned section
  let pinnedSessions = ALL_SESSIONS.filter(s => pinned.includes(s.id));
  if (pinnedSessions.length > 0) {
    pinSection.innerHTML = '<div class="pin-header">📌 置顶<span class="pin-count">' + pinnedSessions.length + '</span></div>' +
      pinnedSessions.map(s => renderSessionItem(s, true)).join('');
  } else {
    pinSection.innerHTML = '';
  }

  // Filter for main list based on currentStatus
  let visibleSessions;
  if (currentStatus === 'archived') {
    visibleSessions = ALL_SESSIONS.filter(s => archived.includes(s.id));
  } else if (currentStatus === 'active') {
    visibleSessions = ALL_SESSIONS.filter(s => !archived.includes(s.id));
  } else {
    visibleSessions = ALL_SESSIONS;
  }

  if (currentStatus === 'archived') {
    // Show archived sessions flat
    if (visibleSessions.length > 0) {
      list.innerHTML = visibleSessions.map(s => renderSessionItem(s, false)).join('');
    } else {
      list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text2);font-size:12px;">暂无已归档会话</div>';
    }
    archBody.innerHTML = visibleSessions.map(s => renderSessionItem(s, false)).join('');
    archBody.classList.remove('collapsed');
    archBody.style.maxHeight = 'none';
    document.querySelector('#archHeader .arch-chevron').textContent = '▼';
  } else {
    // Normal view: group by project with folder support
    let groups = {};
    // Auto-detect main project: find c--* project with most sessions
    let mainKey = null;
    let projCounts = {};
    visibleSessions.forEach(s => { let p = s.project || ''; if (p.startsWith('c--')) { projCounts[p] = (projCounts[p]||0)+1; } });
    let maxCount = 0;
    for (let p in projCounts) { if (projCounts[p] > maxCount) { maxCount = projCounts[p]; mainKey = p; } }
    if (!mainKey) mainKey = '主项目';

    visibleSessions.forEach(s => {
      if (archived.includes(s.id)) return; // skip archived in normal view
      if (pinned.includes(s.id)) return; // skip pinned (shown in pin section)
      let proj = s.project || '未知项目';
      if (proj.startsWith('c--') || proj === '主项目') proj = mainKey;
      // Folder grouping overrides project grouping
      let fid = sf[s.id] || '';
      let groupKey = fid ? ('📁 ' + getFolderName(fid)) : proj;
      if (!groups[groupKey]) groups[groupKey] = [];
      groups[groupKey].push(s);
    });

    let groupNames = Object.keys(groups).sort((a, b) => {
      if (a === mainKey && b !== mainKey) return -1;
      if (b === mainKey && a !== mainKey) return 1;
      if (a.startsWith('📁') && !b.startsWith('📁')) return -1;
      if (!a.startsWith('📁') && b.startsWith('📁')) return 1;
      return a.localeCompare(b);
    });

    groupNames.forEach(projName => {
      let projSessions = groups[projName];
      projSessions.sort((a,b) => (b.date||'').localeCompare(a.date||''));

      let groupDiv = document.createElement('div');
      groupDiv.className = 'proj-group';
      let header = document.createElement('div');
      header.className = 'proj-header';
      let shortName = (projName === mainKey) ? '🏠 主项目' : projName.replace(/^c--/i, '📁 ').replace(/^d--/i, '📄 ');
      header.innerHTML = '<span class="icon">▼</span>' + esc(shortName) + '<span class="count">' + projSessions.length + '</span>';
      header.onclick = function() {
        let body = this.nextElementSibling;
        let icon = this.querySelector('.icon');
        if (body.classList.contains('collapsed')) {
          body.classList.remove('collapsed');
          body.style.maxHeight = body.scrollHeight + 'px';
          icon.textContent = '▼';
        } else {
          body.style.maxHeight = body.scrollHeight + 'px';
          requestAnimationFrame(() => {
            body.classList.add('collapsed');
            icon.textContent = '▶';
          });
        }
      };
      let body = document.createElement('div');
      body.className = 'proj-body';
      projSessions.forEach(s => {
        let div = document.createElement('div');
        div.innerHTML = renderSessionItem(s, false);
        div.firstChild.onclick = function() { selectSession(s.id); };
        body.appendChild(div.firstChild);
      });
      groupDiv.appendChild(header);
      groupDiv.appendChild(body);
      list.appendChild(groupDiv);
    });

    // Build archive section (collapsed in normal view)
    let archSessions = ALL_SESSIONS.filter(s => archived.includes(s.id));
    archSessions.sort((a,b) => (b.date||'').localeCompare(a.date||''));
    archBody.innerHTML = archSessions.map(s => renderSessionItem(s, false)).join('');
    archBody.classList.add('collapsed');
    document.querySelector('#archHeader .arch-chevron').textContent = '▶';
  }

  // Update counts
  let totalArchived = getArchived().length;
  document.getElementById('stabAllCount').textContent = ALL_SESSIONS.length;
  document.getElementById('stabActiveCount').textContent = ALL_SESSIONS.length - totalArchived;
  document.getElementById('stabArchCount').textContent = totalArchived;
  document.getElementById('archCount').textContent = totalArchived;
  if (totalArchived === 0) {
    document.getElementById('archSection').style.display = 'none';
  } else {
    document.getElementById('archSection').style.display = '';
  }

  // Update stats
  let totalSessions = ALL_SESSIONS.length;
  let totalMsgs = ALL_SESSIONS.reduce((s,x) => s + x.msgCount, 0);
  document.getElementById('sessStats').textContent =
    '共 ' + totalSessions + ' 个会话 · ' + totalMsgs + ' 条消息';
}

function renderSessionItem(sess, isPinnedItem) {
  let iter = ITER_LOOKUP[sess.id];
  let displayTitle = getDisplayTitle(sess.id, sess.title || '未命名');
  let chainHtml = '';
  if (iter) {
    let tagClass = iter.role === 'root' ? 'chain-tag root' : 'chain-tag cont';
    let tagText = iter.role === 'root' ? '起点' : ('续#' + iter.order);
    chainHtml = '<span class="' + tagClass + '">🔗 ' + tagText + '</span>';
  }
  let folderBadgeHtml = '';
  let fid = getSessionFolder(sess.id);
  if (fid) {
    folderBadgeHtml = '<span class="folder-badge">📁 ' + esc(getFolderName(fid)) + '</span>';
  }
  let pinClass = isPinned(sess.id) ? ' pin-active' : '';
  let archClass = isArchived(sess.id) ? ' arch-active' : '';
  let itemClass = isPinnedItem ? 'pin-item' : (isArchived(sess.id) ? 'arch-item' : 'session-item');
  let tagHtml = isPinnedItem ? '' :
    '<div class="sess-tags">' + (sess.tags || []).map(t => '<span class="sess-tag">' + esc(t[0]) + '·' + esc(t[1]) + '</span>').join('') + '</div>';

  return '<div class="' + itemClass + '" data-id="' + sess.id + '" data-proj="' + (sess.project||'') + '" data-search="' + escAttr((sess.title+' '+sess.id+' '+sess.date).toLowerCase()) + '" onclick="selectSession(\'' + sess.id + '\')">' +
    '<div class="sess-title">' +
      '<span class="title-text" data-orig-title="' + escAttr(displayTitle) + '">' + esc(displayTitle) + '</span>' +
      '<button class="edit-btn" onclick="event.stopPropagation();startRename(\'' + sess.id + '\',this.closest(\'.' + itemClass + '\'),event)" title="重命名">✎</button>' +
      chainHtml +
    '</div>' +
    folderBadgeHtml +
    '<div class="sess-meta">' +
      '<span>' + esc(sess.date || '?') + '</span>' +
      '<span>' + sess.msgCount + ' 条</span>' +
    '</div>' +
    '<div class="sess-id"><span>' + esc(sess.id) + '</span><button class="copy-id-btn" onclick="event.stopPropagation();copySid(\'' + sess.id + '\',this)" title="复制会话ID">📋</button></div>' +
    tagHtml +
    '<div class="act-btns">' +
      '<button class="act-btn' + pinClass + '" onclick="event.stopPropagation();togglePin(\'' + sess.id + '\')" title="置顶">📌</button>' +
      '<button class="act-btn" onclick="event.stopPropagation();showFolderPanel(\'' + sess.id + '\')" title="文件夹">📁</button>' +
      '<button class="act-btn' + archClass + '" onclick="event.stopPropagation();toggleArchive(\'' + sess.id + '\')" title="归档">📦</button>' +
    '</div>' +
  '</div>';
}

// Override the original buildSidebar — replace the IIFE
// The original IIFE is removed; rebuildSidebar() is called on init
"""

    if js_marker in html:
        html = html.replace(js_marker, new_js + '\n' + js_marker, 1)
    else:
        print('WARNING: JS marker not found')

    # 6. Replace the original buildSidebar IIFE with initSidebar
    # Old IIFE: (function buildSidebar() { ... })();
    # It ends with })(); followed by "// ── Tag cloud"
    old_iife = """(function buildSidebar() {"""
    new_init = """// Original buildSidebar replaced by v3.0 rebuildSidebar
(function initSidebar() {
  rebuildSidebar();
  updateFavBadge();
})();"""
    start_idx = html.find(old_iife)
    if start_idx >= 0:
        # Find the IIFE closing })(); — it's followed by tag cloud comment
        # Search for the pattern: })();\n\n// ── Tag cloud
        end_marker = '\n\n// ── Tag cloud ──'
        end_idx = html.find(end_marker, start_idx)
        if end_idx >= 0:
            old_block = html[start_idx:end_idx]
            html = html.replace(old_block, new_init, 1)
        else:
            print('WARNING: IIFE end marker not found')

    # Write output
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    size_kb = os.path.getsize(OUT_PATH) / 1024
    print(f'Done: {OUT_PATH} ({size_kb:.0f} KB)')

if __name__ == '__main__':
    main()