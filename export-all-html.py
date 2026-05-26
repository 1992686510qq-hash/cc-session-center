"""
@tool:      session-export-all-html
@summary:   扫描所有 Claude Code 会话 JSONL，生成单一 HTML 页面，左侧列表右侧聊天。支持项目分组折叠、迭代链显示
@tags:      session, export, html, conversation, all, browser, iteration
@inputs:    output_dir (str) - 输出目录，默认桌面
@output:    HTML 文件路径

用法:
  python export-all-html.py                  # 扫描所有会话，输出到桌面
  python export-all-html.py <output_dir>     # 指定输出目录
"""

import json, os, re, sys, datetime, glob as globmod

HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Claude Code 会话管理中心</title>
<style>
:root {
  --bg: #f5f5f5; --sidebar-bg: #fff; --card-bg: #fff; --text: #1a1a1a; --text2: #888;
  --border: #e8e8e8; --hover: #f0f4ff; --active: #e8f0fe; --user-bubble: #2563eb;
  --user-text: #fff; --ai-bubble: #f0f0f0; --ai-text: #1a1a1a; --tool-bg: #fafafa;
  --accent: #2563eb; --badge: #e8f0fe; --shadow: 0 1px 3px rgba(0,0,0,.06);
  --chain-bg: #fef3c7; --chain-border: #f59e0b; --proj-header-bg: #f8fafc;
  --sidebar-width: 340px; --pin-bg: #fef9e7;
}
[data-theme="dark"] {
  --bg: #0f0f1a; --sidebar-bg: #141428; --card-bg: #1a1a30; --text: #d0d0d0;
  --text2: #777; --border: #252545; --hover: #1e2a40; --active: #203050;
  --user-bubble: #3b82f6; --user-text: #fff; --ai-bubble: #1e2a3a; --ai-text: #ccc;
  --tool-bg: #1a2540; --accent: #3b82f6; --badge: #1a3050; --shadow: 0 1px 3px rgba(0,0,0,.4);
  --chain-bg: #2a2010; --chain-border: #92400e; --proj-header-bg: #1a1a2e;
  --art-bg: #1e3050; --ref-bg: #1a3540; --url-bg: #2a2040; --search-bg: #302a10; --pin-bg: #2a2010;
}
[data-theme="dark"] .art-link { background: var(--art-bg); }
[data-theme="dark"] .ref-link { background: var(--ref-bg); }
[data-theme="dark"] .ref-url { background: var(--url-bg); }
[data-theme="dark"] .ref-url[style*="fef3c7"] { background: var(--search-bg) !important; }
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
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', system-ui, sans-serif; background: var(--bg); color: var(--text); height: 100vh; overflow: hidden; display: flex; }

/* Sidebar */
.sidebar { width: var(--sidebar-width); background: var(--sidebar-bg); border-right: 1px solid var(--border); display: flex; flex-direction: column; flex-shrink: 0; }
.sidebar-header { padding: 16px; border-bottom: 1px solid var(--border); }
.sidebar-header h2 { font-size: 16px; font-weight: 700; margin-bottom: 10px; }
.sidebar-header input { width: 100%; padding: 8px 12px; border: 1px solid var(--border); border-radius: 8px; font-size: 13px; background: var(--bg); color: var(--text); outline: none; }
.sidebar-header input:focus { border-color: var(--accent); }
.sidebar-stats { font-size: 11px; color: var(--text2); padding: 8px 16px; }
/* Refresh button */
.sidebar-refresh { width: 100%; padding: 6px 16px; border: none; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); background: var(--card-bg); color: var(--accent); font-size: 12px; cursor: pointer; font-weight: 500; transition: all .15s; }
.sidebar-refresh:hover { background: var(--hover); }
.refresh-modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 200; }
.refresh-modal.open { display: flex; align-items: center; justify-content: center; }
.refresh-modal-content { background: var(--card-bg); border-radius: 12px; padding: 24px; width: min(520px, 90vw); box-shadow: 0 8px 40px rgba(0,0,0,.3); }
.refresh-modal-content h3 { margin-bottom: 8px; font-size: 15px; }
.refresh-modal-content p { font-size: 12px; color: var(--text2); margin-bottom: 12px; }
.refresh-modal-content pre { background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 12px; font-size: 12px; overflow-x: auto; white-space: pre-wrap; word-break: break-all; margin-bottom: 12px; }
.refresh-modal-content .btn-row { display: flex; gap: 8px; }
.refresh-modal-content .btn-copy { padding: 8px 20px; background: var(--accent); color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; }
.refresh-modal-content .btn-copy:hover { opacity: .85; }
.refresh-modal-content .btn-close { padding: 8px 16px; background: var(--card-bg); color: var(--text); border: 1px solid var(--border); border-radius: 6px; cursor: pointer; font-size: 13px; }
/* Tag cloud */
.tag-cloud { padding: 6px 10px; border-bottom: 1px solid var(--border); display: flex; flex-wrap: wrap; gap: 4px; max-height: 150px; overflow-y: auto; }
.tag-chip { font-size: 10px; padding: 2px 8px; border-radius: 10px; cursor: pointer; border: 1px solid var(--border); background: var(--card-bg); color: var(--text2); white-space: nowrap; transition: all .15s; user-select: none; }
.tag-chip:hover { border-color: var(--accent); color: var(--accent); }
.tag-chip.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.tag-chip .tag-count { font-size: 9px; opacity: .7; margin-left: 2px; }
/* Session tags in sidebar */
.session-item .sess-tags { display: flex; flex-wrap: wrap; gap: 2px; margin-top: 2px; }
.session-item .sess-tag { font-size: 9px; padding: 0 5px; border-radius: 6px; background: var(--badge); color: var(--accent); white-space: nowrap; }
.session-list { flex: 1; overflow-y: auto; padding: 4px 8px; }

/* Project group */
.proj-group { margin-bottom: 6px; }
.proj-header { padding: 8px 10px; border-radius: 6px; cursor: pointer; display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; color: var(--text2); background: var(--proj-header-bg); user-select: none; transition: background .15s; }
.proj-header:hover { background: var(--hover); }
.proj-header .icon { font-size: 10px; transition: transform .2s; width: 14px; text-align: center; }
.proj-header .count { font-size: 10px; background: var(--badge); padding: 1px 6px; border-radius: 8px; margin-left: auto; }
.proj-body { overflow: hidden; transition: max-height .3s ease; }
.proj-body.collapsed { max-height: 0 !important; }
.session-item { padding: 10px 12px 10px 26px; border-radius: 6px; cursor: pointer; transition: background .15s; margin-bottom: 1px; border-left: 3px solid transparent; }
.session-item:hover { background: var(--hover); }
.session-item.active { background: var(--active); border-left-color: var(--accent); }
.session-item .sess-title { font-size: 12px; font-weight: 600; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: flex; align-items: center; gap: 2px; }
.session-item .sess-title .title-text { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; min-width: 0; }
.session-item .edit-btn { font-size: 10px; opacity: 0; cursor: pointer; padding: 2px 4px; border-radius: 3px; border: none; background: transparent; color: var(--text2); flex-shrink: 0; transition: opacity .15s; }
.session-item:hover .edit-btn { opacity: .6; }
.session-item .edit-btn:hover { opacity: 1 !important; color: var(--accent); background: var(--hover); }
.sess-title-edit { font-size: 11px; font-weight: 600; padding: 2px 4px; border: 1px solid var(--accent); border-radius: 4px; background: var(--card-bg); color: var(--text); outline: none; width: 100%; box-sizing: border-box; }
.session-item .sess-meta { font-size: 10px; color: var(--text2); display: flex; gap: 6px; }
.session-item .sess-id { font-family: 'SF Mono','Consolas',monospace; font-size: 9px; color: var(--text2); opacity: .5; display: flex; align-items: center; gap: 4px; }
.session-item .copy-id-btn { font-size: 10px; padding: 0 4px; border: 1px solid var(--border); border-radius: 3px; background: transparent; cursor: pointer; opacity: 0; transition: opacity .15s; color: var(--text2); line-height: 1.4; }
.session-item:hover .copy-id-btn { opacity: .5; }
.session-item .copy-id-btn:hover { opacity: 1 !important; border-color: var(--accent); color: var(--accent); }

/* Iteration chain indicators */
.chain-tag { display: inline-block; font-size: 9px; padding: 1px 5px; border-radius: 6px; margin-left: 4px; background: var(--chain-bg); color: var(--chain-border); font-weight: 700; }
.chain-tag.root { background: #dbeafe; color: #2563eb; }
.chain-tag.cont { background: #fef3c7; color: #92400e; }
.chain-badge { display: inline-block; font-size: 9px; padding: 1px 4px; border-radius: 4px; background: var(--chain-bg); color: var(--chain-border); margin-right: 2px; }

/* Main area */
.main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.toolbar { padding: 12px 20px; background: var(--sidebar-bg); border-bottom: 1px solid var(--border); display: flex; gap: 8px; align-items: center; flex-shrink: 0; flex-wrap: wrap; }
.toolbar input[type="text"] { flex: 1; min-width: 150px; padding: 7px 14px; border: 1px solid var(--border); border-radius: 20px; font-size: 13px; background: var(--bg); color: var(--text); outline: none; }
.toolbar input[type="text"]:focus { border-color: var(--accent); }
.toolbar button, .toolbar select { padding: 6px 14px; border: 1px solid var(--border); border-radius: 20px; font-size: 12px; cursor: pointer; background: var(--card-bg); color: var(--text); transition: all .15s; white-space: nowrap; }
.toolbar button:hover { border-color: var(--accent); color: var(--accent); }
.toolbar button.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.toolbar .divider { width: 1px; height: 20px; background: var(--border); margin: 0 4px; }
.toolbar .badge { font-size: 11px; color: var(--text2); background: var(--bg); padding: 4px 10px; border-radius: 12px; }
.empty-state { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--text2); font-size: 15px; text-align: center; }
#chatArea { flex: 1; overflow-y: auto; padding: 20px; }

/* Chain panel */
.chain-panel { padding: 10px 20px; background: var(--chain-bg); border-bottom: 1px solid var(--chain-border); display: none; font-size: 12px; }
.chain-panel.visible { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.chain-panel .chain-link { cursor: pointer; color: var(--accent); text-decoration: underline; font-weight: 600; }
.chain-panel .chain-arrow { color: var(--chain-border); font-weight: 700; }

/* Message filter states */
.turn.hidden-by-filter { display: none !important; }
.turn.filtered-collapsed { opacity: .3; margin-bottom: 2px; }
.turn.filtered-collapsed .prompt-bar { padding: 4px 12px; font-size: 10px; cursor: pointer; }
.turn.filtered-collapsed .body { display: none; }
.turn.filtered-collapsed .chevron { display: none; }
.turn.filtered-collapsed .bookmark-btn { display: none; }
.turn.filtered-collapsed .avatar { width: 18px; height: 18px; font-size: 10px; }
.turn.artifact-highlight { border-left: 3px solid #f59e0b; }
/* Top bar sections: artifacts & references */
.top-bar-section { background: var(--card-bg); border-bottom: 1px solid var(--border); }
.top-bar-header { display: flex; align-items: center; gap: 6px; padding: 6px 20px; cursor: pointer; user-select: none; font-size: 12px; }
.top-bar-header:hover { opacity: .7; }
.top-bar-header .top-bar-chevron { font-size: 10px; transition: transform .3s; }
.top-bar-section.collapsed .top-bar-header .top-bar-chevron { transform: rotate(-90deg); }
.top-bar-content { padding: 4px 20px 8px 20px; display: flex; gap: 6px; align-items: center; flex-wrap: wrap; font-size: 12px; }
.top-bar-section.collapsed .top-bar-content { display: none; }
.top-bar-title { font-weight: 700; }
.top-bar-count { font-size: 10px; opacity: .5; }
.top-bar-empty { color: var(--text2); font-size: 11px; padding: 2px 0; }
.art-link { cursor: pointer; color: var(--accent); text-decoration: none; font-size: 11px; padding: 2px 6px; border-radius: 4px; background: #dbeafe; }
.art-link:hover { text-decoration: underline; opacity: .8; }
.ref-link { cursor: pointer; color: #059669; text-decoration: none; font-size: 11px; padding: 2px 6px; border-radius: 4px; background: #d1fae5; }
.ref-link:hover { text-decoration: underline; opacity: .8; }
.ref-url { cursor: pointer; color: #7c3aed; text-decoration: none; font-size: 11px; padding: 2px 6px; border-radius: 4px; background: #ede9fe; }
.ref-url:hover { text-decoration: underline; opacity: .8; }
.copy-path-btn { font-size: 10px; padding: 1px 4px; border: 1px solid var(--border); border-radius: 3px; background: var(--card-bg); cursor: pointer; opacity: .4; }
.copy-path-btn:hover { opacity: 1; }
/* Missing file markers */
.art-link.missing, .ref-link.missing { background: #fee2e2; color: #991b1b; cursor: default; text-decoration: line-through; }
.art-link.missing:hover, .ref-link.missing:hover { opacity: 1; }
[data-theme="dark"] .art-link.missing, [data-theme="dark"] .ref-link.missing { background: #3b1a1a; color: #f87171; }
/* Tag cloud collapse */
.tag-cloud-header { display: flex; align-items: center; justify-content: space-between; cursor: pointer; user-select: none; padding: 2px 0; }
.tag-cloud-header .tag-cloud-chevron { font-size: 10px; transition: transform .3s; opacity: .5; margin-left: auto; }
.tag-cloud.collapsed .tag-cloud-chips { display: none; }
.tag-cloud.collapsed .tag-cloud-chevron { transform: rotate(-90deg); }
.tag-cloud-chips { display: flex; flex-wrap: wrap; gap: 4px; }

/* Agent graph view */
#agentGraphView { flex: 1; overflow: auto; position: relative; background: var(--bg); }
.graph-toolbar { position: sticky; top: 0; z-index: 10; display: flex; gap: 6px; padding: 8px 16px; background: var(--card-bg); border-bottom: 1px solid var(--border); align-items: center; }
.graph-toolbar button { padding: 5px 12px; border: 1px solid var(--border); border-radius: 16px; font-size: 12px; cursor: pointer; background: var(--card-bg); color: var(--text); transition: all .15s; }
.graph-toolbar button:hover { border-color: var(--accent); color: var(--accent); }
.graph-toolbar button.active { background: var(--accent); color: #fff; border-color: var(--accent); }
#graphCanvas { padding: 20px; min-height: 100%; }
/* Tree view */
.tree-node { position: relative; padding-left: 28px; margin: 3px 0; }
.tree-node::before { content: ''; position: absolute; left: 8px; top: 0; bottom: 0; width: 2px; background: var(--border); }
.tree-node:last-child::before { height: 14px; }
.tree-node::after { content: ''; position: absolute; left: 8px; top: 14px; width: 16px; height: 2px; background: var(--border); }
.tree-card { display: inline-block; padding: 8px 14px; border-radius: 10px; background: var(--card-bg); border: 1px solid var(--border); cursor: pointer; transition: all .15s; min-width: 180px; }
.tree-card:hover { border-color: var(--accent); box-shadow: 0 2px 8px rgba(0,0,0,.08); }
.tree-card.root { border-color: var(--accent); border-width: 2px; background: var(--active); }
.tree-card.agent { border-left: 4px solid #f59e0b; }
.tree-card .tc-label { font-size: 13px; font-weight: 600; margin-bottom: 2px; }
.tree-card .tc-type { font-size: 10px; color: var(--text2); }
.tree-card .tc-time { font-size: 9px; color: var(--text2); margin-top: 2px; }
.tree-card .tc-duration { font-size: 9px; color: var(--accent); margin-left: 4px; }
.tree-children { margin-left: 4px; }
.tree-children.collapsed { display: none; }
.tree-toggle { position: absolute; left: 2px; top: 10px; width: 14px; height: 14px; border-radius: 50%; background: var(--card-bg); border: 1px solid var(--border); cursor: pointer; z-index: 2; font-size: 8px; line-height: 12px; text-align: center; color: var(--text2); }
.tree-toggle:hover { border-color: var(--accent); color: var(--accent); }
/* Flow view */
.flow-svg { width: 100%; }
.flow-node { cursor: pointer; }
.flow-node rect { fill: var(--card-bg); stroke: var(--border); stroke-width: 1.5; rx: 8; }
.flow-node.root rect { stroke: var(--accent); stroke-width: 2.5; fill: var(--active); }
.flow-node.agent rect { stroke: #f59e0b; stroke-width: 1.5; }
.flow-node text { fill: var(--text); font-size: 12px; }
.flow-node .f-title { font-weight: 600; font-size: 13px; }
.flow-node .f-meta { font-size: 10px; fill: var(--text2); }
.flow-edge { stroke: var(--border); stroke-width: 1.5; fill: none; marker-end: url(#arrowhead); }
.flow-edge.result { stroke: #10b981; stroke-dasharray: 4 2; }
/* Mind map view */
.mind-svg { width: 100%; }
.mind-node { cursor: pointer; }
.mind-node circle { fill: var(--card-bg); stroke: var(--border); stroke-width: 2; }
.mind-node.root circle { fill: var(--accent); stroke: var(--accent); }
.mind-node.agent circle { stroke: #f59e0b; fill: #fef3c7; }
.mind-node text { fill: var(--text); font-size: 11px; text-anchor: middle; }
.mind-node .m-title { font-weight: 600; font-size: 12px; }
.mind-edge { stroke: var(--border); stroke-width: 1.2; fill: none; }
.graph-empty { text-align: center; padding: 80px 20px; color: var(--text2); font-size: 14px; }
[data-theme="dark"] .tree-card.agent { border-left-color: #d97706; }
.phase-block { margin-bottom: 20px; border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
.phase-header { padding: 10px 16px; background: var(--proj-header-bg); cursor: pointer; display: flex; align-items: center; gap: 8px; user-select: none; font-size: 13px; font-weight: 600; transition: background .15s; }
.phase-header:hover { background: var(--hover); }
.phase-body { padding: 10px 8px 10px 14px; }
.phase-body.collapsed { display: none; }
.batch-group { margin: 4px 0; border: 1px dashed #f59e0b; border-radius: 8px; overflow: hidden; }
.batch-header { padding: 6px 12px; background: #fef3c7; cursor: pointer; display: flex; align-items: center; gap: 6px; font-size: 11px; font-weight: 600; color: #92400e; user-select: none; transition: background .15s; }
.batch-header:hover { background: #fde68a; }
.batch-body { padding: 4px 0; }
.batch-body.collapsed { display: none; }
[data-theme="dark"] .batch-group { border-color: #d97706; }
[data-theme="dark"] .batch-header { background: #2a2010; color: #f59e0b; }
[data-theme="dark"] .batch-header:hover { background: #3b2a10; }
[data-theme="dark"] .flow-node.batch rect { stroke: #d97706; }
[data-theme="dark"] .flow-node.agent rect { stroke: #d97706; }
[data-theme="dark"] .mind-node.agent circle { stroke: #d97706; fill: #2a2010; }
.turn .prompt-bar { display: flex; align-items: flex-start; gap: 10px; padding: 12px 16px; cursor: pointer; user-select: none; transition: background .15s; border-radius: 12px; }
.turn[data-kind="tool"] .prompt-bar { background: var(--tool-bg); border-left: 3px solid #94a3b8; border-radius: 12px; }
.turn[data-kind="dispatch"] .prompt-bar { background: var(--tool-bg); border-left: 3px solid #f59e0b; border-radius: 8px 12px 12px 4px; }
.turn[data-kind="result"] .prompt-bar { background: var(--tool-bg); border-left: 3px solid #10b981; border-radius: 12px 8px 4px 12px; }
.turn.subagent-dispatch .prompt-bar { background: var(--tool-bg); border-left: 3px solid #f59e0b; border-radius: 8px 12px 12px 4px; }
.turn.subagent-result .prompt-bar { background: var(--tool-bg); border-left: 3px solid #10b981; border-radius: 12px 8px 4px 12px; }
.turn.subagent-mixed .prompt-bar { background: var(--tool-bg); border-left: 3px solid #8b5cf6; border-radius: 12px; }
.turn .prompt-bar:hover { filter: brightness(.96); }
.user .prompt-bar { background: var(--user-bubble); color: var(--user-text); border-radius: 12px 12px 4px 12px; }
.assistant .prompt-bar { background: var(--ai-bubble); color: var(--ai-text); border-radius: 12px 12px 12px 4px; }
.prompt-bar .avatar { width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; }
.user .avatar { background: rgba(255,255,255,.2); }
.assistant .avatar { background: rgba(0,0,0,.06); }
.prompt-bar .body { flex: 1; min-width: 0; }
.prompt-bar .role-line { font-size: 10px; font-weight: 600; opacity: .7; margin-bottom: 2px; }
.prompt-bar .preview-text { font-size: 13px; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; word-break: break-word; }
.prompt-bar .preview-text.expanded { display: block; -webkit-line-clamp: unset; }
.prompt-bar .chevron { font-size: 12px; opacity: .5; flex-shrink: 0; margin-top: 6px; transition: transform .3s; }
/* Bookmark */
.bookmark-btn { font-size: 16px; flex-shrink: 0; cursor: pointer; opacity: .3; transition: all .2s; padding: 4px; margin-top: 4px; border: none; background: none; line-height: 1; }
.bookmark-btn:hover { opacity: .8; transform: scale(1.2); }
.bookmark-btn.bookmarked { opacity: 1; }
/* Favorites panel */
.fav-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 100; }
.fav-overlay.open { display: flex; align-items: center; justify-content: center; }
.fav-panel { background: var(--card-bg); border-radius: 16px; width: min(700px, 90vw); max-height: 80vh; display: flex; flex-direction: column; box-shadow: 0 8px 40px rgba(0,0,0,.3); }
.fav-panel-header { padding: 16px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
.fav-panel-header h3 { font-size: 16px; margin: 0; }
.fav-panel-header button { padding: 6px 14px; border: 1px solid var(--border); border-radius: 20px; font-size: 12px; cursor: pointer; background: var(--card-bg); color: var(--text); }
.fav-panel-header button:hover { border-color: var(--accent); color: var(--accent); }
.fav-list { flex: 1; overflow-y: auto; padding: 12px; }
.fav-item { display: flex; align-items: flex-start; gap: 10px; padding: 10px 14px; border-radius: 10px; cursor: pointer; transition: background .15s; margin-bottom: 4px; border-left: 3px solid transparent; }
.fav-item:hover { background: var(--hover); border-left-color: var(--accent); }
.fav-item .fav-icon { font-size: 20px; flex-shrink: 0; margin-top: 2px; }
.fav-item .fav-body { flex: 1; min-width: 0; }
.fav-item .fav-session { font-size: 11px; color: var(--accent); margin-bottom: 3px; }
.fav-item .fav-preview { font-size: 13px; color: var(--text); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.fav-item .fav-meta { font-size: 10px; color: var(--text2); margin-top: 2px; }
.fav-item .fav-remove { font-size: 14px; flex-shrink: 0; cursor: pointer; opacity: .2; padding: 4px; border: none; background: none; color: var(--text); }
.fav-item .fav-remove:hover { opacity: 1; color: #ef4444; }
.fav-empty { text-align: center; padding: 40px 20px; color: var(--text2); font-size: 14px; }
.turn.open .chevron { transform: rotate(180deg); }
.full-body { max-height: 0; overflow: hidden; transition: max-height .5s ease; }
.turn.open .full-body { max-height: 4000px; }
.full-body-inner { padding: 10px 16px 10px 56px; }
.full-body .text { font-size: 14px; line-height: 1.7; white-space: pre-wrap; word-break: break-word; }
.full-body .tool-line { display: inline-block; font-size: 12px; color: var(--text2); background: var(--tool-bg); padding: 2px 8px; border-radius: 5px; margin: 2px 0; font-family: 'SF Mono','Consolas',monospace; }
.no-results { text-align: center; padding: 60px 20px; color: var(--text2); }
/* Global search */
#globalSearchResults { flex: 1; overflow-y: auto; padding: 20px; }
#globalSearchResults h3 { font-size: 14px; font-weight: 700; margin-bottom: 16px; color: var(--text); }
.gs-result { padding: 12px 16px; margin-bottom: 6px; border-radius: 10px; cursor: pointer; background: var(--card-bg); border-left: 3px solid transparent; transition: all .15s; }
.gs-result:hover { background: var(--hover); border-left-color: var(--accent); }
.gs-result .gs-session { font-size: 11px; color: var(--accent); margin-bottom: 4px; font-weight: 600; }
.gs-result .gs-preview { font-size: 13px; line-height: 1.5; color: var(--text); display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.gs-result .gs-meta { font-size: 10px; color: var(--text2); margin-top: 4px; }
.gs-no-results { text-align: center; padding: 60px 20px; color: var(--text2); font-size: 14px; }
/* Search match highlight */
mark { background: #fde68a; color: #1e1e1e; border-radius: 2px; padding: 0 1px; }
[data-theme="dark"] mark { background: #854d0e; color: #fde68a; }

@media (max-width: 700px) {
  body { flex-direction: column; }
  .sidebar { width: 100%; max-height: 40vh; }
}

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
</head>
<body>

<div class="sidebar">
  <div class="sidebar-header">
    <h2>会话记录</h2>
    <input type="text" id="sessSearch" placeholder="搜索会话..." oninput="filterSessions()">
  </div>
  <div class="tag-cloud" id="tagCloud">
    <div class="tag-cloud-header" onclick="toggleTagCloud()">
      <span style="font-size:12px;font-weight:600;opacity:.6;">标签筛选</span>
      <span class="tag-cloud-chevron">▼</span>
    </div>
    <div class="tag-cloud-chips" id="tagCloudChips"></div>
  </div>
  <div class="sidebar-stats" id="sessStats"></div>
  <button class="sidebar-refresh" onclick="showRefreshModal()">&#x1F504; 全量刷新</button>
  <div class="sidebar-tabs" id="sidebarTabs">
    <button class="stab active" onclick="filterByStatus('all')" id="stabAll">全部<span class="stab-count" id="stabAllCount"></span></button>
    <button class="stab" onclick="filterByStatus('active')" id="stabActive">活跃<span class="stab-count" id="stabActiveCount"></span></button>
    <button class="stab" onclick="filterByStatus('archived')" id="stabArchived">已归档<span class="stab-count" id="stabArchCount"></span></button>
  </div>
  <div class="pin-section" id="pinSection"></div>
  <div class="session-list" id="sessList"></div>
</div>

<div class="main">
  <div class="chain-panel" id="chainPanel"></div>
  <div class="top-bar-section" id="artifactSection" style="display:none;">
    <div class="top-bar-header" onclick="toggleTopSection('artifact')">
      <span class="top-bar-title">📦 产出文件</span>
      <span class="top-bar-count" id="artifactCount">0</span>
      <span class="top-bar-chevron">▼</span>
    </div>
    <div class="top-bar-content" id="artifactContent"></div>
  </div>
  <div class="top-bar-section" id="refSection" style="display:none;">
    <div class="top-bar-header" onclick="toggleTopSection('ref')">
      <span class="top-bar-title">📖 参考资料</span>
      <span class="top-bar-count" id="refCount">0</span>
      <span class="top-bar-chevron">▼</span>
    </div>
    <div class="top-bar-content" id="refContent"></div>
  </div>
  <div class="toolbar">
    <input type="text" id="msgSearch" placeholder="全局搜索所有会话..." oninput="doSearch()">
    <select id="roleFilter" onchange="doSearch()">
      <option value="all">全部角色</option>
      <option value="user">仅提问</option>
      <option value="assistant">仅回复</option>
    </select>
    <span class="divider"></span>
    <button id="filterAllBtn" class="active" onclick="setMsgFilter('all')">全部消息</button>
    <button id="filterChatBtn" onclick="setMsgFilter('chat')">仅对话</button>
    <button id="filterToolBtn" onclick="setMsgFilter('tool')">仅工具</button>
    <span class="divider"></span>
    <button onclick="expandAll()">展开全部</button>
    <button onclick="collapseAll()">收起全部</button>
    <button onclick="expandAllProjects()">展开项目</button>
    <button onclick="collapseAllProjects()">折叠项目</button>
    <button onclick="toggleTheme()" id="themeBtn">暗色</button>
	    <button onclick="openGraphView()" id="graphViewBtn" style="display:none;font-weight:600;">🔗 关系图</button>
    <button onclick="showFavorites()" id="favBtn" style="font-weight:700;">⭐ 收藏夹 <span id="favBadge" style="font-size:10px;background:var(--accent);color:#fff;border-radius:10px;padding:1px 6px;margin-left:2px;display:none;">0</span></button>
    <span style="font-weight:700;font-size:14px;flex:0 0 auto;max-width:400px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" id="sessTitle"></span>
    <span class="badge" id="resultCount"></span>
  </div>
  <div id="chatArea">
    <div class="empty-state">← 选择左侧会话开始浏览</div>
  </div>
  <div id="globalSearchResults" style="display:none;"></div>
  <div id="agentGraphView" style="display:none;">
    <div class="graph-toolbar">
      <button onclick="switchGraphMode('tree')" id="graphTreeBtn" class="active">树状图</button>
      <span style="flex:1;"></span>
      <button onclick="closeGraphView()">返回对话</button>
    </div>
    <div id="graphCanvas"></div>
  </div>
</div>

<!-- Favorites overlay -->
<div class="fav-overlay" id="favOverlay" onclick="if(event.target===this)hideFavorites()">
  <div class="fav-panel">
    <div class="fav-panel-header">
      <h3>⭐ 收藏夹</h3>
      <button onclick="copyAllBookmarks()" title="复制全部收藏到剪贴板" style="margin-right:8px;">📋 批量复制</button>
      <button onclick="hideFavorites()">关闭 ✕</button>
    </div>
    <div class="fav-list" id="favList"></div>
  </div>
</div>

<script>
const ALL_SESSIONS = __ALL_DATA__;
const ITERATIONS = __ITER_DATA__;
let currentSession = null;

function esc(s) {
  if (!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function escAttr(s) {
  return esc(s).replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}
function shortPreview(text, max) {
  max = max || 150;
  return text.length > max ? esc(text.substring(0, max)) + '...' : esc(text);
}
function fmtContent(text) {
  return text.split('\n').map(line => {
    let e = esc(line);
    if (e.match(/^\[(🔧|工具)/)) return '<span class="tool-line">'+e+'</span>';
    if (e.match(/^\[📥 子Agent返回\]/)) return '<span class="tool-line" style="border-left:3px solid #10b981">'+e+'</span>';
    return e;
  }).join('\n');
}

// Build iteration lookup
function buildIterLookup() {
  let lookup = {}; // sessionId -> { chainId, order, role, parentId }
  if (ITERATIONS && ITERATIONS.chains) {
    for (let [cid, chain] of Object.entries(ITERATIONS.chains)) {
      for (let s of chain.sessions || []) {
        lookup[s.id] = {
          chainId: cid,
          order: s.order,
          role: s.role,
          parentId: s.parent || '',
          chainSessions: (chain.sessions || []).map(x => x.id)
        };
      }
    }
  }
  return lookup;
}
const ITER_LOOKUP = buildIterLookup();

// Build sidebar with project grouping
// initSidebar moved after v3 definitions

// ── Tag cloud ──
let activeTag = '';
function buildTagCloud() {
  let counts = {};
  ALL_SESSIONS.forEach(s => {
    (s.tags || []).forEach(t => {
      let key = t[0] + '·' + t[1];
      counts[key] = (counts[key] || 0) + 1;
    });
  });
  let sorted = Object.entries(counts).sort((a,b) => b[1]-a[1] || a[0].localeCompare(b[0]));
  let chips = document.getElementById('tagCloudChips');
  chips.innerHTML = '<span class="tag-chip active" onclick="filterByTag(\'\')" id="tagAll">全部<span class="tag-count">' + ALL_SESSIONS.length + '</span></span>' +
    sorted.map(([tag, n]) =>
      '<span class="tag-chip" onclick="filterByTag(\'' + tag.replace(/'/g, "\\'") + '\')">' + esc(tag) + '<span class="tag-count">' + n + '</span></span>'
    ).join('');
}
function toggleTagCloud() {
  document.getElementById('tagCloud').classList.toggle('collapsed');
}
function filterByTag(tag) {
  activeTag = tag;
  document.querySelectorAll('.tag-chip').forEach(c => c.classList.remove('active'));
  if (!tag) {
    document.getElementById('tagAll').classList.add('active');
  } else {
    document.querySelectorAll('.tag-chip').forEach(c => { if (c.textContent.startsWith(tag)) c.classList.add('active'); });
  }
  document.querySelectorAll('.session-item').forEach(el => {
    let sid = el.getAttribute('data-id');
    let s = ALL_SESSIONS.find(x => x.id === sid);
    if (!tag) { el.style.display = ''; return; }
    let match = (s.tags || []).some(t => (t[0] + '·' + t[1]) === tag);
    el.style.display = match ? '' : 'none';
  });
  // Hide empty project groups
  document.querySelectorAll('.proj-group').forEach(g => {
    let visible = g.querySelectorAll('.session-item[style*="display: none"]').length < g.querySelectorAll('.session-item').length;
    g.style.display = visible ? '' : 'none';
  });
}
buildTagCloud();


// ── v3.0: 会话三维组织 ──
var currentStatus = 'all';
// ── 全量刷新 ──
function showRefreshModal() { document.getElementById('refreshModal').classList.add('open'); }
function closeRefreshModal() { document.getElementById('refreshModal').classList.remove('open'); }
function copyRefreshCmd() {
  var cmd = document.getElementById('refreshCmd').innerText;
  navigator.clipboard.writeText(cmd).then(function() {
    var btn = event.target;
    btn.textContent = '✅ 已复制!';
    setTimeout(function() { btn.textContent = '📋 复制命令'; }, 2000);
  });
}
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
  if (status === 'archived' && currentStatus === 'archived') {
    status = 'all';
    currentStatus = 'all';
  } else {
    currentStatus = status;
  }
  document.querySelectorAll('#sidebarTabs .stab').forEach(s => s.classList.remove('active'));
  document.getElementById('stab' + status.charAt(0).toUpperCase() + status.slice(1)).classList.add('active');
  rebuildSidebar();
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

  }

  // Update counts
  let totalArchived = getArchived().length;
  document.getElementById('stabAllCount').textContent = ALL_SESSIONS.length;
  document.getElementById('stabActiveCount').textContent = ALL_SESSIONS.length - totalArchived;
  document.getElementById('stabArchCount').textContent = totalArchived;

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


(function initSidebar() {
  rebuildSidebar();
  updateFavBadge();
})();

function collapseAllProjects() {
  document.querySelectorAll('.proj-body').forEach(b => {
    b.classList.add('collapsed');
    b.style.maxHeight = '0';
  });
  document.querySelectorAll('.proj-header .icon').forEach(i => i.textContent = '▶');
}
function expandAllProjects() {
  document.querySelectorAll('.proj-body').forEach(b => {
    b.classList.remove('collapsed');
    b.style.maxHeight = b.scrollHeight + 'px';
  });
  document.querySelectorAll('.proj-header .icon').forEach(i => i.textContent = '▼');
}

function filterSessions() {
  let q = document.getElementById('sessSearch').value.trim();
  let qLower = q.toLowerCase();

  // Clear previous highlights: restore titles from data-orig-title
  document.querySelectorAll('.session-item .title-text').forEach(sp => {
    let orig = sp.getAttribute('data-orig-title');
    if (orig && sp.innerHTML !== orig) {
      sp.innerHTML = esc(orig);
    }
  });

  document.querySelectorAll('.proj-group').forEach(group => {
    let anyVisible = false;
    group.querySelectorAll('.session-item').forEach(el => {
      let txt = el.getAttribute('data-search');
      let vis = !qLower || txt.indexOf(qLower) >= 0;
      el.style.display = vis ? '' : 'none';
      if (vis) anyVisible = true;
      // Highlight keyword in title
      if (vis && q) {
        let titleSp = el.querySelector('.title-text');
        if (titleSp) {
          let orig = titleSp.getAttribute('data-orig-title') || titleSp.textContent;
          let escaped = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
          let re = new RegExp('(' + escaped + ')', 'gi');
          titleSp.innerHTML = esc(orig).replace(re, '<mark>$1</mark>');
        }
      }
    });
    group.style.display = anyVisible ? '' : 'none';
    if (anyVisible) {
      // Auto-expand groups with matches
      let body = group.querySelector('.proj-body');
      let icon = group.querySelector('.proj-header .icon');
      if (body && body.classList.contains('collapsed')) {
        body.classList.remove('collapsed');
        body.style.maxHeight = body.scrollHeight + 'px';
        if (icon) icon.textContent = '▼';
      }
    }
  });
}

function showChainPanel(sid) {
  let panel = document.getElementById('chainPanel');
  let iter = ITER_LOOKUP[sid];
  if (!iter || !iter.chainSessions || iter.chainSessions.length < 2) {
    panel.classList.remove('visible');
    panel.innerHTML = '';
    return;
  }
  let parts = iter.chainSessions.map(id => {
    let s = ALL_SESSIONS.find(x => x.id === id);
    let label = s ? (s.title || '未命名') : id.substring(0,8);
    let arrow = id === sid ? ' ◀ 当前' : '';
    return '<span class="chain-link" onclick="selectSession(\'' + id + '\')">' + esc(label) + '</span>' + arrow;
  });
  panel.innerHTML = '🔗 迭代链：' + parts.join(' <span class="chain-arrow">→</span> ');
  panel.classList.add('visible');
}

// ── Rename ──
const TITLE_KEY = 'claude-session-titles';
function getCustomTitles() { try { return JSON.parse(localStorage.getItem(TITLE_KEY) || '{}'); } catch(e) { return {}; } }
function getCustomTitle(sid) { return getCustomTitles()[sid] || ''; }
function saveCustomTitle(sid, title) { let t = getCustomTitles(); t[sid] = title; localStorage.setItem(TITLE_KEY, JSON.stringify(t)); }
function getDisplayTitle(sid, fallback) { return getCustomTitle(sid) || fallback || '未命名'; }

function startRename(sid, el, e) {
  e.stopPropagation();
  let titleSpan = el.querySelector('.title-text');
  if (!titleSpan) return;
  let currentTitle = getCustomTitle(sid) || titleSpan.getAttribute('data-orig-title') || '';
  let input = document.createElement('input');
  input.className = 'sess-title-edit';
  input.value = currentTitle;
  let save = () => {
    let newTitle = input.value.trim();
    if (newTitle && newTitle !== currentTitle) {
      saveCustomTitle(sid, newTitle);
      titleSpan.textContent = newTitle;
      titleSpan.setAttribute('data-orig-title', newTitle);
      if (currentSession && currentSession.id === sid) currentSession.title = newTitle;
    }
    input.replaceWith(titleSpan);
  };
  input.addEventListener('blur', save);
  input.addEventListener('keydown', (ev) => {
    if (ev.key === 'Enter') { input.blur(); }
    if (ev.key === 'Escape') { input.value = currentTitle; input.blur(); }
  });
  titleSpan.replaceWith(input);
  input.focus();
  input.select();
}

// ── Bookmarks ──
const BM_KEY = 'claude-session-bookmarks';
function getBookmarks() { try { return JSON.parse(localStorage.getItem(BM_KEY) || '[]'); } catch(e) { return []; } }
function saveBookmarks(arr) { localStorage.setItem(BM_KEY, JSON.stringify(arr)); }
function updateFavBadge() { let b=document.getElementById('favBadge'); let n=getBookmarks().length; b.textContent=n; b.style.display=n>0?'inline':''; }

function copyMsg(idx) {
	if (!currentSession || !currentSession.messages) return;
	var m = currentSession.messages[idx];
	if (!m) return;
	navigator.clipboard.writeText(m.text || '').then(function() {
		var btns = document.querySelectorAll('.copy-btn');
	}).catch(function() {});
	// Brief flash feedback
	var turn = document.querySelectorAll('.turn')[idx];
	if (turn) {
		var btn = turn.querySelector('.copy-btn');
		if (btn) { btn.textContent = '✓'; setTimeout(function() { btn.textContent = '📋'; }, 1000); }
	}
}

function bmClick(btn, idx) {
  if (!currentSession) return;
  let m = currentSession.messages[idx];
  if (!m) return;
  let sid = currentSession.id;
  let key = sid + '|' + idx;
  let bms = getBookmarks();
  let existing = bms.findIndex(b => b.key === key);
  if (existing >= 0) {
    bms.splice(existing, 1);
    btn.classList.remove('bookmarked'); btn.textContent = '☆';
  } else {
    bms.push({ key: key, sid: sid, idx: idx, role: m.role,
      preview: (m.text || '').substring(0, 200),
      ts: m.ts, sessionTitle: getDisplayTitle(sid, currentSession.title || '') });
    btn.classList.add('bookmarked'); btn.textContent = '★';
  }
  saveBookmarks(bms);
  updateFavBadge();
}

function isBookmarked(sid, idx) {
  return getBookmarks().some(b => b.key === (sid + '|' + idx));
}

function showFavorites() {
  let bms = getBookmarks();
  let list = document.getElementById('favList');
  if (bms.length === 0) {
    list.innerHTML = '<div class="fav-empty">还没有收藏内容<br><br>在消息旁边点击 ☆ 即可收藏</div>';
  } else {
    // Sort newest first
    bms.sort((a,b) => b.ts.localeCompare(a.ts));
    list.innerHTML = bms.map(b => {
      let icon = b.role === 'user' ? '🧑' : '🤖';
      let roleLabel = b.role === 'user' ? '提问' : '回复';
      return '<div class="fav-item" onclick="navigateToBookmark(\'' + b.sid + '\',' + b.idx + ')">' +
        '<div class="fav-icon">' + icon + '</div>' +
        '<div class="fav-body">' +
          '<div class="fav-session">' + esc(getDisplayTitle(b.sid, b.sessionTitle || '未命名')) + '</div>' +
          '<div class="fav-preview">' + esc(b.preview) + '</div>' +
          '<div class="fav-meta">' + roleLabel + ' · ' + esc(b.ts) + '</div>' +
        '</div>' +
        '<button class="fav-copy" onclick="event.stopPropagation();copyBookmarkText(\'' + b.sid + '\',' + b.idx + ')" title="复制">📋</button>' +
        '<button class="fav-remove" onclick="event.stopPropagation();removeBookmark(\'' + b.sid + '\',' + b.idx + ')" title="取消收藏">✕</button>' +
      '</div>';
    }).join('');
  }
  document.getElementById('favOverlay').classList.add('open');
}

function copyBookmarkText(sid, idx) {
  var text = '';
  var found = false;
  if (typeof ALL_SESSIONS !== 'undefined') {
    for (var si = 0; si < ALL_SESSIONS.length; si++) {
      if (ALL_SESSIONS[si].id === sid) {
        var msgs = ALL_SESSIONS[si].messages;
        if (msgs && msgs[idx]) { text = msgs[idx].text || ''; found = true; }
        break;
      }
    }
  }
  if (!found) {
    var bms = getBookmarks();
    for (var bi = 0; bi < bms.length; bi++) {
      if (bms[bi].sid === sid && bms[bi].idx === idx) { text = bms[bi].preview || ''; break; }
    }
  }
  navigator.clipboard.writeText(text).catch(function(){});
}

function copyAllBookmarks() {
  var bms = getBookmarks();
  if (bms.length === 0) return;
  var parts = [];
  for (var bi = 0; bi < bms.length; bi++) {
    var b = bms[bi];
    var text = b.preview || '';
    if (typeof ALL_SESSIONS !== 'undefined') {
      for (var si = 0; si < ALL_SESSIONS.length; si++) {
        if (ALL_SESSIONS[si].id === b.sid) {
          var msgs = ALL_SESSIONS[si].messages;
          if (msgs && msgs[b.idx]) { text = msgs[b.idx].text || ''; }
          break;
        }
      }
    }
    var role = b.role === 'user' ? '[提问]' : '[回复]';
    parts.push('=== ' + role + ' · ' + esc(b.sessionTitle || '') + ' ===\n' + text);
  }
  navigator.clipboard.writeText(parts.join('\n\n---\n\n')).catch(function(){});
  alert('已复制 ' + bms.length + ' 条收藏到剪贴板');
}

function hideFavorites() {
  document.getElementById('favOverlay').classList.remove('open');
}

function removeBookmark(sid, idx) {
  let bms = getBookmarks();
  let key = sid + '|' + idx;
  bms = bms.filter(b => b.key !== key);
  saveBookmarks(bms);
  updateFavBadge();
  showFavorites(); // refresh panel
  // Update button in current chat if visible
  let btn = document.querySelector('[data-bm-key="' + key + '"]');
  if (btn) { btn.classList.remove('bookmarked'); btn.textContent = '☆'; }
}

function navigateToBookmark(sid, idx) {
  hideFavorites();
  selectSession(sid);
  // Scroll to the bookmarked message after render
  setTimeout(() => {
    let turns = document.querySelectorAll('#chatArea .turn');
    if (turns[idx]) {
      turns[idx].scrollIntoView({ behavior: 'smooth', block: 'center' });
      // Auto-expand the target message
      if (!turns[idx].classList.contains('open')) {
        toggle(turns[idx]);
      }
      // Flash highlight
      turns[idx].style.boxShadow = '0 0 0 3px var(--accent)';
      setTimeout(() => { turns[idx].style.boxShadow = ''; }, 2000);
    }
  }, 300);
}

function selectSession(sid) {
  currentSession = ALL_SESSIONS.find(s => s.id === sid);
  if (!currentSession) return;
  // Switch from global search to chat view
  document.getElementById('globalSearchResults').style.display = 'none';
  document.getElementById('chatArea').style.display = '';
  document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
  let item = document.querySelector('[data-id="' + sid + '"]');
  if (item) item.classList.add('active');
  showChainPanel(sid);
  renderChat(currentSession.messages);
  applyMsgFilter();
  buildArtifactIndex(currentSession.artifacts);
  buildReferenceIndex(currentSession.references);
  let title = getDisplayTitle(currentSession.id, currentSession.title || '未命名');
  document.getElementById('resultCount').textContent = currentSession.msgCount + ' 条消息';
  document.getElementById('sessTitle').textContent = title;
  document.getElementById('msgSearch').value = '';
  document.getElementById('roleFilter').value = 'all';
  // Update search placeholder to indicate in-session search
  document.getElementById('msgSearch').placeholder = '在当前会话中搜索...';
  // Show/hide agent graph button
  let hasAgentTree = currentSession.agent_graph && currentSession.agent_graph.total_agents > 0;
  document.getElementById('graphViewBtn').style.display = hasAgentTree ? '' : 'none';
	// Auto-refresh graph view when switching sessions
	if (document.getElementById('agentGraphView').style.display !== 'none') {
		closeGraphView();
		setTimeout(function() { openGraphView(); }, 80);
	}
}

function renderChat(msgs) {
  let area = document.getElementById('chatArea');
  area.innerHTML = '';
  if (!msgs || msgs.length === 0) {
    area.innerHTML = '<div class="empty-state">此会话无消息</div>';
    return;
  }
  msgs.forEach((m, i) => {
    let kind = m.kind || 'text';
    let isUser = m.role === 'user';
    let isTool = (kind === 'tool' || kind === 'dispatch');
    let isResult = (kind === 'result');
    // CSS classes: .msg-text, .msg-tool, .msg-dispatch, .msg-result
    let cls = 'msg-' + kind;
    let label = isUser ? '💬 你' : '🤖 Claude';
    let avatar = isUser ? '🧑' : '🤖';
    let colorClass = '';
    if (kind === 'text') {
      // natural conversation
      label = isUser ? '💬 你' : '🤖 Claude';
      colorClass = isUser ? 'user' : 'assistant';
    } else if (kind === 'tool') {
      label = '🔧 工具调用';
      avatar = '⚙️';
      colorClass = '';
      if (isUser) label = '🔧 你调用工具';
    } else if (kind === 'dispatch') {
      label = '📤 派发子Agent';
      avatar = '📤';
      colorClass = 'subagent-dispatch';
    } else if (kind === 'result') {
      label = '📥 返回结果';
      avatar = '📥';
      colorClass = 'subagent-result';
    }
    let div = document.createElement('div');
    div.className = 'turn ' + colorClass;
    div.setAttribute('data-kind', kind);
    div.setAttribute('data-role', m.role);
    div.setAttribute('data-text', m.text.toLowerCase());
    let startOpen = (kind === 'text' && isUser);
    let bmKey = currentSession.id + '|' + i;
    let bmClass = isBookmarked(currentSession.id, i) ? ' bookmarked' : '';
    let bmStar = isBookmarked(currentSession.id, i) ? '★' : '☆';
    div.innerHTML =
      '<div class="prompt-bar" onclick="toggle(this.parentElement)">' +
        '<div class="avatar">'+avatar+'</div>' +
        '<div class="body">' +
          '<div class="role-line">'+label+' · #'+(i+1)+' · '+esc(m.ts)+'</div>' +
          '<div class="preview-text'+(startOpen?' expanded':'')+'">'+shortPreview(m.text)+'</div>' +
        '</div>' +
        '<button class="bookmark-btn'+bmClass+'" data-bm-key="'+bmKey+'" data-bm-idx="'+i+'" onclick="event.stopPropagation();bmClick(this,'+i+')" title="收藏">'+bmStar+'</button>' +
        '<button class="copy-btn" onclick="event.stopPropagation();copyMsg('+i+')" title="复制此条消息">📋</button>' +
        '<div class="chevron">▼</div>' +
      '</div>' +
      '<div class="full-body"><div class="full-body-inner"><div class="text">'+fmtContent(m.text, kind)+'</div></div></div>';
    if (startOpen) setTimeout(() => {
      let fb = div.querySelector('.full-body');
      if (fb) fb.style.maxHeight = fb.scrollHeight + 'px';
    }, 50);
    area.appendChild(div);
  });
}

function toggle(el) {
  let wasOpen = el.classList.contains('open');
  el.classList.toggle('open');
  let fb = el.querySelector('.full-body');
  let preview = el.querySelector('.preview-text');
  if (!wasOpen) {
    fb.style.maxHeight = fb.scrollHeight + 'px';
    preview.classList.add('expanded');
  } else {
    fb.style.maxHeight = '0';
    setTimeout(() => preview.classList.remove('expanded'), 300);
  }
}
function expandAll() {
  document.querySelectorAll('.turn').forEach(t => {
    t.classList.add('open');
    let fb = t.querySelector('.full-body');
    if (fb) fb.style.maxHeight = fb.scrollHeight + 'px';
    let pv = t.querySelector('.preview-text');
    if (pv) pv.classList.add('expanded');
  });
}
function collapseAll() {
  document.querySelectorAll('.turn').forEach(t => {
    t.classList.remove('open');
    let fb = t.querySelector('.full-body');
    if (fb) fb.style.maxHeight = '0';
    setTimeout(() => { let pv=t.querySelector('.preview-text'); if(pv)pv.classList.remove('expanded'); }, 300);
  });
}
function doSearch() {
  let q = document.getElementById('msgSearch').value.trim();
  let role = document.getElementById('roleFilter').value;

  // Clear previous highlights
  clearSearchHighlights();

  // No session selected → global search mode
  if (!currentSession) {
    if (q) {
      globalSearch(q);
    } else {
      document.getElementById('globalSearchResults').style.display = 'none';
      document.getElementById('chatArea').style.display = '';
    }
    return;
  }

  // In-session search
  document.getElementById('globalSearchResults').style.display = 'none';
  document.getElementById('chatArea').style.display = '';

  let qLower = q.toLowerCase();
  let vis = 0, total = 0;
  document.querySelectorAll('#chatArea .turn').forEach(t => {
    if (t.classList.contains('hidden-by-filter')) return;
    total++;
    let r = t.getAttribute('data-role');
    let txt = t.getAttribute('data-text') || '';
    let ok = (role === 'all' || r === role) && (!qLower || txt.indexOf(qLower) >= 0);
    t.style.display = ok ? '' : 'none';
    if (ok && qLower) {
      vis++;
      highlightTurn(t, q);
    }
  });
  document.getElementById('resultCount').textContent =
    q ? vis + ' / ' + total + ' 条匹配' : total + ' 条消息';
}

function clearSearchHighlights() {
  document.querySelectorAll('#chatArea .turn').forEach(t => {
    let orig = t.getAttribute('data-orig-preview');
    if (orig !== null) {
      t.querySelector('.preview-text').innerHTML = orig;
      t.removeAttribute('data-orig-preview');
    }
    let origBody = t.getAttribute('data-orig-body');
    if (origBody !== null) {
      let fb = t.querySelector('.full-body .text');
      if (fb) fb.innerHTML = origBody;
      t.removeAttribute('data-orig-body');
    }
  });
}

function highlightTurn(t, rawQuery) {
  let preview = t.querySelector('.preview-text');
  let bodyText = t.querySelector('.full-body .text');
  // Save originals first
  if (!t.hasAttribute('data-orig-preview')) {
    t.setAttribute('data-orig-preview', preview.innerHTML);
  }
  if (bodyText && !t.hasAttribute('data-orig-body')) {
    t.setAttribute('data-orig-body', bodyText.innerHTML);
  }
  // Escape regex special chars but keep the query as literal text
  let escaped = rawQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  let re = new RegExp('(' + escaped + ')', 'gi');
  preview.innerHTML = preview.innerHTML.replace(re, '<mark>$1</mark>');
  if (bodyText) {
    bodyText.innerHTML = bodyText.innerHTML.replace(re, '<mark>$1</mark>');
  }
}

function globalSearch(q) {
  let area = document.getElementById('chatArea');
  let resultsDiv = document.getElementById('globalSearchResults');
  area.style.display = 'none';
  resultsDiv.style.display = '';
  resultsDiv.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text2);">搜索中...</div>';

  // Use setTimeout to let UI update, then search
  setTimeout(() => {
    let qLower = q.toLowerCase();
    let hits = [];
    ALL_SESSIONS.forEach(s => {
      (s.messages || []).forEach((m, i) => {
        let txt = (m.text || '').toLowerCase();
        if (txt.indexOf(qLower) >= 0) {
          hits.push({
            sid: s.id,
            sessionTitle: getDisplayTitle(s.id, s.title || '未命名'),
            idx: i,
            role: m.role,
            kind: m.kind || 'text',
            ts: m.ts || '',
            text: m.text || '',
          });
        }
      });
    });

    // Limit results
    let totalHits = hits.length;
    if (hits.length > 200) hits = hits.slice(0, 200);

    if (hits.length === 0) {
      resultsDiv.innerHTML = '<div class="gs-no-results">未找到包含 "' + esc(q) + '" 的消息</div>';
      return;
    }

    let html = '<h3>全局搜索 "' + esc(q) + '" — ' + totalHits + ' 条结果</h3>';
    hits.forEach(h => {
      let preview = h.text;
      let maxLen = 200;
      if (preview.length > maxLen) {
        // Find the match position and center the snippet around it
        let pos = preview.toLowerCase().indexOf(qLower);
        if (pos < 0) pos = 0;
        let start = Math.max(0, pos - 80);
        let end = Math.min(preview.length, pos + q.length + 120);
        preview = (start > 0 ? '...' : '') + preview.slice(start, end) + (end < preview.length ? '...' : '');
      }
      // Highlight
      let escaped = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      let re = new RegExp('(' + escaped + ')', 'gi');
      preview = esc(preview).replace(re, '<mark>$1</mark>');

      let icon = h.role === 'user' ? '💬' : '🤖';
      let kindLabel = h.kind === 'text' ? '' : ' [' + ({tool:'工具',dispatch:'派发',result:'返回'}[h.kind] || h.kind) + ']';

      html += '<div class="gs-result" onclick="jumpToMsg(\'' + h.sid + '\',' + h.idx + ')">' +
        '<div class="gs-session">' + esc(h.sessionTitle) + kindLabel + '</div>' +
        '<div class="gs-preview">' + icon + ' ' + preview + '</div>' +
        '<div class="gs-meta">' + esc(h.ts) + '</div>' +
      '</div>';
    });
    if (totalHits > 200) {
      html += '<div class="gs-no-results" style="padding:20px;">...另有 ' + (totalHits - 200) + ' 条结果未显示，请缩小搜索范围</div>';
    }
    resultsDiv.innerHTML = html;
  }, 10);
}

function jumpToMsg(sid, idx) {
  // Hide global search, show chat area
  document.getElementById('globalSearchResults').style.display = 'none';
  document.getElementById('chatArea').style.display = '';
  selectSession(sid);
  // After render, scroll to the message and flash
  setTimeout(() => {
    let turns = document.querySelectorAll('#chatArea .turn');
    if (turns[idx]) {
      if (!turns[idx].classList.contains('open')) {
        toggle(turns[idx]);
      }
      turns[idx].scrollIntoView({ behavior: 'smooth', block: 'center' });
      turns[idx].style.boxShadow = '0 0 0 3px var(--accent)';
      setTimeout(() => { turns[idx].style.boxShadow = ''; }, 2500);
    }
  }, 400);
}

function copySid(sid, btn) {
  navigator.clipboard.writeText(sid).then(() => {
    let orig = btn.textContent;
    btn.textContent = '✓';
    setTimeout(() => { btn.textContent = orig; }, 1500);
  }).catch(() => {});
}

function toggleTheme() {
  let html = document.documentElement;
  let btn = document.getElementById('themeBtn');
  if (html.getAttribute('data-theme')==='dark') {
    html.setAttribute('data-theme','light'); btn.textContent='暗色';
  } else {
    html.setAttribute('data-theme','dark'); btn.textContent='亮色';
  }
  localStorage.setItem('sess-viewer-theme', html.getAttribute('data-theme'));
}

// ── Message filter ──
let msgFilter = 'chat'; // default: only conversations
function setMsgFilter(mode) {
  msgFilter = mode;
  ['filterAllBtn','filterChatBtn','filterToolBtn'].forEach(id => document.getElementById(id).classList.remove('active'));
  document.getElementById(mode==='all'?'filterAllBtn':mode==='chat'?'filterChatBtn':'filterToolBtn').classList.add('active');
  applyMsgFilter();
}
function applyMsgFilter() {
  document.querySelectorAll('#chatArea .turn').forEach(t => {
    let kind = t.getAttribute('data-kind') || 'text';
    if (msgFilter === 'chat') {
      // Only show real conversation (text messages)
      if (kind !== 'text') { t.classList.add('hidden-by-filter'); }
      else { t.classList.remove('hidden-by-filter'); }
    } else if (msgFilter === 'tool') {
      // Only show tools, dispatches, and results
      if (kind === 'text') { t.classList.add('hidden-by-filter'); }
      else { t.classList.remove('hidden-by-filter'); }
    } else {
      t.classList.remove('hidden-by-filter');
    }
  });
}

// ── Artifact & Reference index ──
function buildArtifactIndex(arts) {
  let sec = document.getElementById('artifactSection');
  let content = document.getElementById('artifactContent');
  let count = document.getElementById('artifactCount');
  if (!arts || arts.length === 0) { sec.style.display = 'none'; return; }
  sec.style.display = '';
  count.textContent = '(' + arts.length + ')';
  content.innerHTML = arts.map(a => {
    let cls = a.exists ? 'art-link' : 'art-link missing';
    let icon = a.exists ? '' : '⚠️ ';
    let isLocal = !/^https?:\/\//i.test(a.path);
    let title = (a.exists ? '打开: ' : '⚠ 文件已移动或删除: ') + escAttr(a.path);
    if (isLocal) {
      let fileUrl = 'file:///' + a.path.replace(/\\/g,'/').replace(/^([A-Za-z]):/, '/$1:');
      return '<span class="' + cls + '" onclick="' + (a.exists ? 'window.open(\'' + fileUrl.replace(/'/g,"\\'") + '\')' : '') + '" title="' + title + '">' + icon + esc(a.name) + '</span>';
    } else {
      return '<span class="' + cls + '" onclick="window.open(\'' + a.path.replace(/'/g,"\\'") + '\')" title="' + title + '">' + icon + esc(a.name) + '</span>';
    }
  }).join('');
}

function buildReferenceIndex(refs) {
  let sec = document.getElementById('refSection');
  let content = document.getElementById('refContent');
  let count = document.getElementById('refCount');
  if (!refs || (refs.files.length === 0 && refs.urls.length === 0 && refs.searches.length === 0)) {
    sec.style.display = 'none'; return;
  }
  sec.style.display = '';
  let total = refs.files.length + refs.urls.length + refs.searches.length;
  count.textContent = '(' + total + ')';
  let parts = [];
  refs.files.forEach(f => {
    let fp = f.path || f;
    let exists = f.exists !== false;
    let name = fp.replace(/\\/g,'/').split('/').pop();
    let cls = exists ? 'ref-link' : 'ref-link missing';
    let icon = exists ? '📄 ' : '⚠️ ';
    let title = (exists ? '打开: ' : '⚠ 文件已移动或删除: ') + escAttr(fp);
    let fileUrl = 'file:///' + fp.replace(/\\/g,'/').replace(/^([A-Za-z]):/, '/$1:');
    let onclick = exists ? 'window.open(\'' + fileUrl.replace(/'/g,"\\'") + '\')' : '';
    parts.push('<span class="' + cls + '" onclick="' + onclick + '" title="' + title + '">' + icon + esc(name) + '</span><span class="copy-path-btn" onclick="event.stopPropagation();copyPath(\'' + fp.replace(/\\/g,'\\\\').replace(/'/g,"\\'") + '\')" title="复制路径">📋</span>');
  });
  refs.urls.forEach(url => {
    let label = url.replace(/^https?:\/\//, '').split('/')[0] + '/...';
    parts.push('<span class="ref-url" onclick="window.open(\'' + url.replace(/'/g,"\\'") + '\')" title="打开: ' + escAttr(url) + '">🔗 ' + esc(label) + '</span>');
  });
  refs.searches.forEach(q => {
    parts.push('<span class="ref-url" title="搜索: ' + escAttr(q) + '" style="background:#fef3c7;color:#92400e;cursor:default;">🔍 ' + esc(q.length > 40 ? q.slice(0,40)+'...' : q) + '</span>');
  });
  content.innerHTML = parts.join('');
}

function copyPath(path) {
  navigator.clipboard.writeText(path).then(() => {}).catch(() => {});
  // Brief visual feedback handled by button hover style
}

function toggleTopSection(kind) {
  let sec = document.getElementById(kind === 'artifact' ? 'artifactSection' : 'refSection');
  sec.classList.toggle('collapsed');
}

function scrollToMsg(idx) {
  let turns = document.querySelectorAll('#chatArea .turn');
  if (turns[idx]) { turns[idx].scrollIntoView({ behavior: 'smooth', block: 'center' }); }
}

(function() {
  let s = localStorage.getItem('sess-viewer-theme');
  if (s==='dark') {
    document.documentElement.setAttribute('data-theme','dark');
    document.getElementById('themeBtn').textContent='亮色';
  }
  document.addEventListener('keydown', function(e) {
    if (e.target.tagName==='INPUT') return;
    if (e.key==='Escape') { collapseAll(); hideFavorites(); }
  });
  updateFavBadge();
  // Init message filter to default "仅对话"
  document.getElementById('filterAllBtn').classList.remove('active');
  document.getElementById('filterChatBtn').classList.add('active');
})();

// ═══════════════════════════════════════════
// Agent relationship graph view (v2 - phase-aware)
// ═══════════════════════════════════════════
let currentGraphMode = 'tree';

function openGraphView() {
	var ag = currentSession && currentSession.agent_graph;
	if (!ag || !ag.tree || !ag.tree.children || ag.tree.children.length === 0) return;
	document.getElementById('chatArea').style.display = 'none';
	document.getElementById('globalSearchResults').style.display = 'none';
	document.getElementById('artifactSection').style.display = 'none';
	document.getElementById('refSection').style.display = 'none';
	document.getElementById('agentGraphView').style.display = '';
	buildAgentGraph();
}

function closeGraphView() {
	document.getElementById('agentGraphView').style.display = 'none';
	document.getElementById('chatArea').style.display = '';
	if (currentSession) {
		buildArtifactIndex(currentSession.artifacts);
		buildReferenceIndex(currentSession.references);
	}
}

function switchGraphMode(mode) {
	buildAgentGraph();
}

function buildAgentGraph() {
	var ag = currentSession.agent_graph;
	var canvas = document.getElementById('graphCanvas');
	if (!ag || !ag.tree || !ag.tree.children || ag.tree.children.length === 0) {
		canvas.innerHTML = '<div class="graph-empty">此会话没有子Agent调度记录</div>';
		return;
	}
	renderTreeView(ag);
}

// ── Tree View with phases and batches ──
function renderTreeView(ag) {
	var canvas = document.getElementById('graphCanvas');
	canvas.innerHTML = '';

	var summary = document.createElement('div');
	summary.style.cssText = 'padding:8px 0 12px 0;font-size:13px;color:var(--text2);flex-shrink:0;';
	summary.textContent = ag.total_agents + ' 个子Agent · ' + (ag.phases ? ag.phases.length : 0) + ' 个阶段';
	canvas.appendChild(summary);

	var phases = ag.phases || [];
	if (phases.length === 0) {
		var col = makePhaseColumn({id:'phase-0',label:'全部Agent',ts:'',agent_count:ag.total_agents,batches:[]}, 0, ag, true);
		canvas.appendChild(col);
		return;
	}

	var scrollWrap = document.createElement('div');
	scrollWrap.className = 'graph-hscroll';
	scrollWrap.style.cssText = 'display:flex;gap:16px;overflow-x:auto;padding:0 8px 16px 8px;align-items:flex-start;';

	phases.forEach(function(phase, seqIdx) {
		var actualPi = parseInt(phase.id.split("-")[1]);
		scrollWrap.appendChild(makePhaseColumn(phase, actualPi, ag, false, seqIdx));
	});

	canvas.appendChild(scrollWrap);
}

function makePhaseColumn(phase, pi, ag, isFallback, displayIdx) {
	var col = document.createElement('div');
	col.className = 'phase-col';
	col.style.cssText = 'min-width:260px;max-width:330px;flex-shrink:0;border:1px solid var(--border);border-radius:10px;overflow:hidden;background:var(--card-bg);';

	var ph = document.createElement('div');
	ph.className = 'phase-col-header';
	ph.style.cssText = 'padding:10px 12px;background:var(--proj-header-bg);font-size:12px;font-weight:600;cursor:pointer;user-select:none;display:flex;align-items:center;gap:6px;';
	var label = esc(phase.label || '');
	var timeStr = phase.ts ? phase.ts.substring(11,16) : '';
	ph.innerHTML = '<span class="ph-chevron" style="font-size:9px;">▼</span> 📍 '+(isFallback?'全部Agent':('阶段'+((displayIdx !== undefined ? displayIdx : pi) + 1)))+' <span style="font-size:10px;opacity:.5;">'+esc(timeStr)+' · '+phase.agent_count+' agents</span>';
	ph.title = label;

	var pbody = document.createElement('div');
	pbody.className = 'phase-col-body';
	pbody.style.cssText = 'padding:8px 6px;max-height:65vh;overflow-y:auto;';

	ph.onclick = function() {
		var chev = this.querySelector('.ph-chevron');
		if (pbody.classList.contains('ph-collapsed')) {
			pbody.classList.remove('ph-collapsed');
			pbody.style.display = '';
			chev.textContent = '▼';
		} else {
			pbody.classList.add('ph-collapsed');
			pbody.style.display = 'none';
			chev.textContent = '▶';
		}
	};

	var phaseAgents = [];
	for (var nid in ag.node_map) {
		var n = ag.node_map[nid];
		if (n.phase_idx === pi) phaseAgents.push(n);
	}
	phaseAgents.sort(function(a,b){ return (a.dispatch_ts||'').localeCompare(b.dispatch_ts||''); });

	if (phaseAgents.length === 0) {
		pbody.innerHTML = '<div style="color:var(--text2);font-size:11px;padding:8px;">无Agent</div>';
	} else {
		var i = 0;
		var firstCard = true;
		while (i < phaseAgents.length) {
			var a = phaseAgents[i];
			if (a.batch_id) {
				var batchMembers = [];
				var bid = a.batch_id;
				while (i < phaseAgents.length && phaseAgents[i].batch_id === bid) {
					batchMembers.push(phaseAgents[i]);
					i++;
				}
				if (!firstCard) {
					var s1 = document.createElement('div');
					s1.className = 'agent-sep';
					s1.style.cssText = 'text-align:center;color:var(--text2);font-size:11px;padding:2px 0;';
					s1.textContent = '↓';
					pbody.appendChild(s1);
				}
				pbody.appendChild(buildBatchGroup(batchMembers));
				firstCard = false;
			} else {
				if (!firstCard) {
					var s2 = document.createElement('div');
					s2.className = 'agent-sep';
					s2.style.cssText = 'text-align:center;color:var(--text2);font-size:11px;padding:2px 0;';
					s2.textContent = '↓';
					pbody.appendChild(s2);
				}
				pbody.appendChild(buildAgentCard(a));
				firstCard = false;
				i++;
			}
		}
	}

	col.appendChild(ph);
	col.appendChild(pbody);
	return col;
}

function buildBatchGroup(members) {
	var wrap = document.createElement('div');
	wrap.className = 'graph-batch';
	wrap.style.cssText = 'border:1px dashed #f59e0b;border-radius:8px;margin:4px 0;overflow:hidden;';

	var MAX_VISIBLE = 10;
	var needsFold = members.length > MAX_VISIBLE;

	var head = document.createElement('div');
	head.className = 'graph-batch-head';
	head.style.cssText = 'padding:5px 8px;background:#fef3c7;cursor:pointer;font-size:10px;font-weight:600;color:#92400e;display:flex;align-items:center;gap:4px;user-select:none;';
	var slabel = esc(members[0].label.substring(0,30));
	head.innerHTML = '<span class="bt-chevron" style="font-size:8px;">▼</span> ⚡ 并行 ×'+members.length+' <span style="opacity:.5;font-weight:400;">'+slabel+'...</span>';

	var body = document.createElement('div');
	body.className = 'graph-batch-body';
	body.style.cssText = 'padding:3px 4px;';

	head.onclick = function(e) {
		e.stopPropagation();
		var chev = this.querySelector('.bt-chevron');
		if (body.classList.contains('bt-collapsed')) {
			body.classList.remove('bt-collapsed');
			body.style.display = '';
			chev.textContent = '▼';
			if (this._showBtn) this._showBtn.style.display = '';
		} else {
			body.classList.add('bt-collapsed');
			body.style.display = 'none';
			chev.textContent = '▶';
			if (this._showBtn) this._showBtn.style.display = 'none';
		}
	};

	var visibleCount = needsFold ? Math.min(MAX_VISIBLE, Math.floor(members.length * 0.6)) : members.length;
	for (var vi = 0; vi < visibleCount; vi++) {
		body.appendChild(buildAgentCard(members[vi]));
	}

	if (needsFold) {
		var hidden = members.length - visibleCount;
		var showBtn = document.createElement('div');
		showBtn.style.cssText = 'text-align:center;padding:4px 0 2px 0;cursor:pointer;font-size:10px;color:var(--accent);';
		showBtn.textContent = '展开剩余 ' + hidden + ' 个 ▾';
		var expanded = false;
		showBtn.onclick = function(e) {
			e.stopPropagation();
			if (!expanded) {
				for (var ri = visibleCount; ri < members.length; ri++) {
					body.insertBefore(buildAgentCard(members[ri]), showBtn);
				}
				showBtn.textContent = '收起 ▴';
			} else {
				while (body.children[visibleCount] && body.children[visibleCount] !== showBtn) {
					body.removeChild(body.children[visibleCount]);
				}
				showBtn.textContent = '展开剩余 ' + hidden + ' 个 ▾';
			}
			expanded = !expanded;
		};
		body.appendChild(showBtn);
		head._showBtn = showBtn;
	}

	wrap.appendChild(head);
	wrap.appendChild(body);
	return wrap;
}

function buildAgentCard(node) {
	var card = document.createElement('div');
	card.className = 'agent-mini-card';
	card.style.cssText = 'padding:6px 8px;margin:2px 0;border-radius:6px;background:var(--bg);border:1px solid var(--border);cursor:pointer;font-size:11px;transition:border-color .2s;';
	card.onmouseenter = function() { this.style.borderColor = 'var(--accent)'; };
	card.onmouseleave = function() { this.style.borderColor = 'var(--border)'; };

	var icon = '🤖';
	if (node.type === 'Explore') icon = '🔍';
	else if (node.type === 'Plan') icon = '📐';
	else if (node.type === 'general-purpose') icon = '🛠️';

	var label = esc(node.label);
	var shortLabel = label.length > 38 ? label.substring(0,38)+'...' : label;
	var duration = '';
	if (node.dispatch_ts && node.result_ts) {
		try {
			var st = new Date(node.dispatch_ts.replace(' ','T'));
			var et = new Date(node.result_ts.replace(' ','T'));
			var sec = Math.round((et - st) / 1000);
			if (sec >= 0) duration = (sec >= 60 ? Math.floor(sec/60)+'m'+(sec%60)+'s' : sec+'s');
		} catch(e) {}
	}
	var timeInfo = node.dispatch_ts ? node.dispatch_ts.substring(11,16) : '';
	if (node.result_ts) timeInfo += '→' + node.result_ts.substring(11,16);
	if (duration) timeInfo += ' | ' + duration;

	card.innerHTML =
		'<div style="display:flex;align-items:flex-start;gap:4px;">' +
		'<span style="font-size:12px;flex-shrink:0;">'+icon+'</span>' +
		'<div style="flex:1;min-width:0;">' +
		'<div style="font-weight:600;line-height:1.3;word-break:break-all;">'+shortLabel+'</div>' +
		'<div style="color:var(--text2);font-size:9px;margin-top:2px;">'+esc(node.type||'')+' | '+esc(timeInfo)+'</div>' +
		'</div></div>';

	card.onclick = function(e) {
		e.stopPropagation();
		alert('Agent: ' + node.label + '\nType: ' + (node.type || 'N/A') + '\nDispatch: ' + (node.dispatch_ts || '?') + '\nReturn: ' + (node.result_ts || '?'));
	};
	return card;
}

	</script>
	</script></script>
</script>
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
<div class="refresh-modal" id="refreshModal" onclick="if(event.target===this)closeRefreshModal()">
  <div class="refresh-modal-content">
    <h3>&#x1F504; 全量刷新</h3>
    <p>在终端中运行以下命令，完成后刷新本页面即可看到最新数据：</p>
    <pre id="refreshCmd">python ~/.claude/shared-scripts/session/export-all-html.py</pre>
    <div class="btn-row">
      <button class="btn-copy" onclick="copyRefreshCmd()">📋 复制命令</button>
      <button class="btn-close" onclick="closeRefreshModal()">关闭</button>
    </div>
  </div>
</div>
</body>
</html>'''


# ── Auto-classification rules ──
# Format: (一级标签, 二级标签, [title关键词...], [content关键词...])
CLASSIFY_RULES = [
    # 对话元分析
    ('对话元分析', '功能开发', ['会话管理', '管理中心', '对话管理', 'cc会话', 'claude code', 'session', '计划管理'], []),
    ('对话元分析', '数据提取', ['提示词提取', '元分析', '提取对话'], []),
    ('对话元分析', '模式分析', ['模式分析', '对话分析'], []),
    ('对话元分析', '报告生成', ['报告', '汇总统计'], []),
    ('对话元分析', '回顾总结', ['回顾总结', 'cc使用', '使用调查'], []),
    # Agent系统
    ('Agent系统', '多Agent调度', ['agent架构', 'agent调度', 'swarm', 'dispatch', '多agent', '子agent', 'agent系统', 'agent分析', 'agent间隙', 'agent开发'], []),
    ('Agent系统', '并行处理', ['并行处理', '并发'], []),
    ('Agent系统', '窗口管理', ['窗口管理', 'workspace'], []),
    ('Agent系统', '自动化设计', ['自动化', 'automation', '全自动', '自动部署'], []),
    # AI工具配置
    ('AI工具配置', '学习探索', ['skill', '插件', 'plugin', 'mcp', '怎么用', '如何使用'], []),
    ('AI工具配置', '故障排查', ['token', '优化', '报错', 'error', 'bug', '修复', 'fix', '排查', '延迟', '加速', '慢'], []),
    ('AI工具配置', '功能开发', ['skill开发', '功能开发', '功能实现'], []),
    ('AI工具配置', '脚本编写', ['脚本', 'script'], []),
    # 社交情感分析
    ('社交情感分析', '人物分析', ['微信聊天', '聊天记录', '聊天分析', '好友分析', '社交分析', '性格分析'], []),
    ('社交情感分析', '策略制定', ['恋爱策略', '追求', '军师', 'simp', '童锦程'], []),
    ('社交情感分析', '对话转录', ['语音转录', '转文字'], []),
    ('社交情感分析', '关系追踪', ['关系追踪'], []),
    # 内容创作
    ('内容创作', 'PPT生成', ['ppt', '幻灯片', 'slide', '演示'], []),
    ('内容创作', '文档撰写', ['文档', '撰写', 'markdown', 'readme', '文章', '写作', '教程', '指南'], []),
    ('内容创作', '排版美化', ['排版', '美化', '字体', '样式', '设计'], []),
    ('内容创作', '格式转换', ['格式转换', '导出'], []),
    # 知识管理
    ('知识管理', '笔记整理', ['obsidian', '笔记整理', '整理笔记', '笔记归类'], []),
    ('知识管理', '文件归类', ['桌面整理', '整理文件', 'organize desktop', '文件分类', '整理桌面', '桌面文件', '文件整理'], []),
    ('知识管理', '格式转换', ['格式转换', '转成markdown'], []),
    # 编程排错
    ('编程排错', '环境配置', ['环境配置', '安装', 'setup', 'install', 'steam'], []),
    ('编程排错', '错误诊断', ['error', 'bug', 'debug', '报错', '出错', '失败', '排错', '打不开', '连不上'], []),
    ('编程排错', '工具安装', ['update', '更新', '升级', '版本', 'github check', '下载'], []),
    # 科研任务
    ('科研任务', '代码调试', ['科研', '门老师', 'debug', '调试'], []),
    ('科研任务', '环境搭建', ['docker', '环境', '搭建', '服务器'], []),
    ('科研任务', '数据处理', ['fits', 'astronomy', '数据处理', '数据分析'], []),
    ('科研任务', '文献阅读', ['论文', '文献', 'paper'], []),
    # 音视频处理
    ('音视频处理', '下载', ['下载视频', 'download', 'youtube', 'bilibili'], []),
    ('音视频处理', '转文字', ['转文字', '字幕', 'transcribe', 'bcut'], []),
    ('音视频处理', '内容总结', ['视频总结', 'summarize'], []),
    ('音视频处理', '批量处理', ['批量', 'batch'], []),
    # 知识星球运营
    ('知识星球运营', '内容发布', ['知识星球', 'zsxq', '发布', 'publish'], []),
    ('知识星球运营', '内容删除', ['删除文章', 'delete'], []),
    ('知识星球运营', '平台研究', ['知识星球', '星球平台'], []),
    ('知识星球运营', '自动化', ['自动化', '自动发布'], []),
    # 网盘下载
    ('网盘下载', '资源下载', ['夸克', '网盘', 'zlib', '下载书', 'download file', '资源下载'], []),
]


def classify_session(title, first_msg=''):
    """Auto-classify a session into 1-3 tags (一级·二级) based on keyword matching."""
    text = ((title or '') + ' ' + (first_msg or '')).lower()
    scored = []
    seen_pairs = set()

    for cat1, cat2, title_kw, content_kw in CLASSIFY_RULES:
        score = 0
        for kw in title_kw:
            if kw.lower() in text:
                score += 3
        for kw in content_kw:
            if kw.lower() in text:
                score += 1
        if score <= 0:
            continue
        pair = (cat1, cat2)
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        scored.append((cat1, cat2, score))

    scored.sort(key=lambda x: x[2], reverse=True)
    top = scored[:3]

    if not top:
        return [('其他', '未分类')]

    result = []
    seen_cat1 = set()
    for cat1, cat2, _ in top:
        if cat1 not in seen_cat1 or len(result) < 3:
            result.append((cat1, cat2))
            seen_cat1.add(cat1)

    return result[:3]


def _parse_ts(raw):
    """Parse ISO timestamp and convert to local time (UTC+8)."""
    try:
        s = raw.strip()
        # Handle formats: "2026-05-15T11:00:00Z", "2026-05-15T11:00:00.000Z", "2026-05-15T11:00:00+00:00"
        if s.endswith('Z'):
            s = s[:-1] + '+00:00'
        dt = datetime.datetime.fromisoformat(s)
        # Convert to UTC+8 (Asia/Shanghai)
        tz_shanghai = datetime.timezone(datetime.timedelta(hours=8))
        if dt.tzinfo is None:
            # Naive datetime — assume UTC, then convert
            dt = dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz_shanghai)
        else:
            # Timezone-aware — convert to UTC+8
            dt = dt.astimezone(tz_shanghai)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return raw[:19].replace('T', ' ')


def _norm_proj(name, base):
    """Normalize project name to consistent case by checking on-disk directory name."""
    try:
        on_disk = os.path.join(base, name)
        if os.path.isdir(on_disk):
            return os.path.basename(on_disk)
    except Exception:
        pass
    return name


def extract_messages(jsonl_path):
    """Extract user/assistant messages from a JSONL file.

    Each JSONL message is split into separate entries per content block type:
      - kind='text'   : pure user/assistant text (the real conversation)
      - kind='tool'   : a tool invocation (Bash, Read, Write, Edit, Skill...)
      - kind='dispatch': spawning a sub-agent (Agent/Task)
      - kind='result'  : tool_result / sub-agent return
    """
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    msgs = []
    for line in lines:
        try:
            obj = json.loads(line)
            typ = obj.get('type')
            msg = obj.get('message')
            if typ not in ('user', 'assistant') or not msg:
                continue
            role = msg['role']
            raw_ts = obj.get('timestamp', '')
            ts = _parse_ts(raw_ts)
            # Collect entries from this message
            entries = []
            text_buf = []
            for c in msg.get('content', []):
                ct = c.get('type', '')
                if ct == 'text':
                    text_buf.append(c['text'])
                elif ct == 'tool_use':
                    # Flush pending text
                    if text_buf:
                        entries.append({'ts': ts, 'role': role, 'text': '\n'.join(text_buf).strip(), 'kind': 'text'})
                        text_buf = []
                    name = c.get('name', '?')
                    inp = c.get('input', {})
                    if name in ('Read', 'Write', 'Edit'):
                        label = f'{name}: {inp.get("file_path","")}'
                    elif name == 'Bash':
                        label = f'Bash: {inp.get("command","")[:120]}'
                    elif name == 'Skill':
                        label = f'Skill: {inp.get("skill","")}'
                    elif name == 'Agent':
                        st = inp.get('subagent_type', '')
                        desc = inp.get('description', '')
                        label = f'派发子Agent [{st}]: {desc}'
                        entries.append({'ts': ts, 'role': role, 'text': label, 'kind': 'dispatch'})
                        continue
                    elif name == 'Task':
                        desc = inp.get('description', '')
                        label = f'派发任务: {desc}'
                        entries.append({'ts': ts, 'role': role, 'text': label, 'kind': 'dispatch'})
                        continue
                    entries.append({'ts': ts, 'role': role, 'text': label, 'kind': 'tool'})
                elif ct == 'tool_result':
                    if text_buf:
                        entries.append({'ts': ts, 'role': role, 'text': '\n'.join(text_buf).strip(), 'kind': 'text'})
                        text_buf = []
                    res_texts = []
                    for rc in c.get('content', []):
                        if isinstance(rc, dict) and rc.get('type') == 'text':
                            res_texts.append(rc['text'])
                        elif isinstance(rc, str):
                            res_texts.append(rc)
                    if res_texts:
                        res_combined = '\n'.join(res_texts).strip()
                        if res_combined:
                            MAX_RESULT = 500
                            if len(res_combined) > MAX_RESULT:
                                res_combined = res_combined[:MAX_RESULT] + f'...\n（共{len(res_combined)}字符，已截断）'
                            entries.append({'ts': ts, 'role': role, 'text': res_combined, 'kind': 'result'})
            # Flush remaining text
            if text_buf:
                entries.append({'ts': ts, 'role': role, 'text': '\n'.join(text_buf).strip(), 'kind': 'text'})
            msgs.extend(entries)
        except Exception:
            pass
    return msgs


def extract_references(jsonl_path):
    """Extract files/URLs the Agent referenced (Read/WebFetch/WebSearch).
    Checks os.path.exists() for local files so the UI can mark missing ones."""
    files = []
    urls = []
    searches = []
    seen_files = set()
    seen_urls = set()
    seen_searches = set()
    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    msg = obj.get('message')
                    if not msg:
                        continue
                    for c in msg.get('content', []):
                        if c.get('type') != 'tool_use':
                            continue
                        name = c.get('name', '')
                        inp = c.get('input', {})
                        if name == 'Read':
                            fp = inp.get('file_path', '')
                            if fp and fp not in seen_files:
                                seen_files.add(fp)
                                files.append({'path': fp, 'exists': os.path.exists(fp)})
                        elif name == 'WebFetch':
                            url = inp.get('url', '') or inp.get('urls', '')
                            if isinstance(url, list):
                                for u in url:
                                    if u and u not in seen_urls:
                                        seen_urls.add(u)
                                        urls.append(u)
                            elif url and url not in seen_urls:
                                seen_urls.add(url)
                                urls.append(url)
                        elif name == 'WebSearch':
                            q = inp.get('query', '')
                            if q and q not in seen_searches:
                                seen_searches.add(q)
                                searches.append(q)
                except Exception:
                    pass
    except Exception:
        pass
    return {'files': files, 'urls': urls, 'searches': searches}


def extract_artifacts(msgs):
    """Extract generated file paths from tool-call messages and check existence."""
    arts = []
    seen = set()
    file_re = re.compile(r'(?:Write|Edit|Bash):\s*([^\s"]+\.(?:pptx?|pdf|md|py|js|html|css|json|txt|png|jpg|svg|zip|skill))', re.IGNORECASE)
    for m in msgs:
        for match in file_re.finditer(m.get('text', '')):
            path = match.group(1)
            if path not in seen:
                seen.add(path)
                arts.append({
                    'path': path,
                    'name': path.replace('\\', '/').split('/')[-1],
                    'exists': os.path.exists(path),
                })
    return arts


def extract_agent_graph(jsonl_path):
    """Parse Agent/Task dispatch hierarchy from JSONL into phase-aware graph.

    Returns dict with 'phases' list and 'tree', or None if no sub-agents.
    Phases are separated by user messages. Within each phase, parallel siblings
    (same parent, sharing a common description prefix >= 10 chars) are grouped into batches.
    """
    import datetime as _dt
    nodes = []
    pending = {}
    user_msgs = []  # [(ts, text_preview), ...]
    last_phase = -1

    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue

                ts = _parse_ts(obj.get('timestamp', ''))
                otype = obj.get('type', '')

                # Track user messages for phase boundaries
                if otype == 'user':
                    c2 = obj.get('message', {}).get('content', [])
                    if isinstance(c2, list):
                        for cc in c2:
                            if isinstance(cc, dict) and cc.get('type') == 'text':
                                txt = cc.get('text', '').strip()
                                if txt and '<ide_opened_file>' not in txt and not txt.startswith('File ') and not txt.startswith('Base directory') and not txt.startswith('Continue from'):
                                    user_msgs.append((ts, txt[:100].replace('\n', ' ').replace('\r', '')))
                                    last_phase = len(user_msgs) - 1
                                    break
                    continue

                msg = obj.get('message')
                if not msg:
                    continue
                content = msg.get('content', [])
                if isinstance(content, str):
                    continue
                for c in content:
                    if not isinstance(c, dict):
                        continue
                    ct = c.get('type', '')
                    if ct == 'tool_use':
                        name = c.get('name', '')
                        if name in ('Agent', 'Task'):
                            inp = c.get('input', {})
                            nid = f'agent-{len(nodes)}'
                            node = {
                                'id': nid,
                                'parent_id': 'root',
                                'label': (inp.get('description') or name)[:120],
                                'type': inp.get('subagent_type', ''),
                                'dispatch_ts': ts,
                                'result_ts': None,
                                'phase_idx': max(last_phase, 0),
                                'batch_id': '',
                                'children': [],
                            }
                            nodes.append(node)
                            pending[c.get('id', '')] = node
                    elif ct == 'tool_result':
                        tid = c.get('tool_use_id', '')
                        if tid in pending:
                            pending[tid]['result_ts'] = ts
    except Exception:
        pass

    if not nodes:
        return None

    # Build tree
    tree = {'id': 'root', 'label': '主对话', 'type': 'root', 'dispatch_ts': '', 'result_ts': '', 'phase_idx': -1, 'batch_id': '', 'children': []}
    node_map = {'root': tree}
    for n in nodes:
        node_map[n['id']] = n
    for n in nodes:
        pid = n.get('parent_id', 'root')
        parent = node_map.get(pid, tree)
        parent.setdefault('children', []).append(n)

    def _common_prefix_len(a, b):
        """Return length of common prefix between two strings."""
        max_len = min(len(a), len(b))
        for i in range(max_len):
            if a[i] != b[i]:
                return i
        return max_len

    # Detect batches: consecutive siblings sharing >= 3 prefix chars
    MIN_COMMON_PREFIX = 3
    for nid, parent_node in node_map.items():
        kids = parent_node.get('children', [])
        if len(kids) < 2:
            continue
        kids_sorted = sorted(kids, key=lambda x: x.get('dispatch_ts', ''))
        batch_idx = 0
        i = 0
        while i < len(kids_sorted):
            cluster = [kids_sorted[i]]
            j = i + 1
            while j < len(kids_sorted):
                if _common_prefix_len(kids_sorted[j-1]['label'], kids_sorted[j]['label']) >= MIN_COMMON_PREFIX:
                    cluster.append(kids_sorted[j])
                    j += 1
                else:
                    break
            if len(cluster) >= 2:
                bid = f'{nid}-batch-{batch_idx}'
                for cn in cluster:
                    cn['batch_id'] = bid
                batch_idx += 1
            i = j if j > i + 1 else i + 1

    # Build phase list
    phase_map = {}
    for n in nodes:
        pi = n.get('phase_idx', 0)
        if pi not in phase_map:
            phase_map[pi] = []
        phase_map[pi].append(n)

    phases = []
    for pi in sorted(phase_map.keys()):
        pnodes = phase_map[pi]
        um = user_msgs[pi] if pi < len(user_msgs) else ('', '')
        # Collect batch info for this phase
        phase_batches = {}
        for n in pnodes:
            bid = n.get('batch_id', '')
            if bid:
                if bid not in phase_batches:
                    phase_batches[bid] = {'id': bid, 'count': 0, 'sample_label': n['label'][:50]}
                phase_batches[bid]['count'] += 1
        phases.append({
            'id': f'phase-{pi}',
            'label': um[1][:80] if um[1] else '初始阶段',
            'ts': um[0] if um[0] else '',
            'agent_count': len(pnodes),
            'batches': [v for v in phase_batches.values() if v['count'] >= 2],
        })

    return {
        'total_agents': len(nodes),
        'phases': phases,
        'tree': tree,
        'node_map': {n['id']: n for n in nodes},
    }


def extract_agent_tree(jsonl_path):
    """Backward-compat wrapper. Returns the tree portion of the agent graph."""
    g = extract_agent_graph(jsonl_path)
    if g is None:
        return None
    return g['tree']


def _scan_title_from_file(path):
    """Scan a single JSONL file for custom-title, ai-title, and first user message."""
    custom_title = None
    ai_title = None
    first_msg = None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    t = obj.get('type', '')
                    if t == 'custom-title' and obj.get('customTitle'):
                        custom_title = obj['customTitle'].strip()
                    elif t == 'ai-title' and obj.get('aiTitle'):
                        ai_title = obj['aiTitle'].strip()
                    elif not first_msg and t == 'user':
                        content = obj.get('message', {}).get('content', [])
                        for c in content:
                            if isinstance(c, dict) and c.get('type') == 'text' and c.get('text'):
                                first_msg = c['text'].strip().replace('#', '').strip()
                                break
                    if custom_title and ai_title and first_msg:
                        break
                except Exception:
                    pass
    except Exception:
        pass
    return custom_title, ai_title, first_msg


def get_session_title(jsonl_path, msgs):
    """Extract title: custom-title > ai-title > first user message > fallback.

    Also checks the project-root-level JSONL for the same session ID, since
    custom-title may exist in a smaller root copy while messages are in a subfolder.
    """
    custom_title, ai_title, first_msg = _scan_title_from_file(jsonl_path)

    # If no custom/ai title found, check root-level JSONL for same session ID
    if not custom_title and not ai_title:
        try:
            parent = os.path.dirname(jsonl_path)
            sid = os.path.basename(jsonl_path)
            root_jsonl = os.path.join(os.path.dirname(parent), sid)
            if os.path.isfile(root_jsonl) and root_jsonl != jsonl_path:
                ct, at, _ = _scan_title_from_file(root_jsonl)
                if ct:
                    custom_title = ct
                if at:
                    ai_title = at
        except Exception:
            pass

    # Fall back to messages list if JSONL scan didn't find a user message
    if not first_msg:
        for m in msgs:
            if m['role'] == 'user':
                first_msg = m['text'].strip().replace('#', '').strip()
                break

    title = custom_title or ai_title or first_msg or '未命名会话'
    if len(title) > 80:
        title = title[:80] + '...'
    return title


def load_iterations():
    """Load iteration chain data."""
    path = os.path.expanduser('~/.claude/projects/session-iterations.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'chains': {}, 'pending_bridges': {}}


def scan_all_sessions():
    """Scan all Claude Code project directories for JSONL files."""
    base = os.path.expanduser('~/.claude/projects')
    if not os.path.isdir(base):
        return []

    sessions = []
    seen = {}  # sid -> (file_path, file_size)

    # First pass: find the best JSONL file for each session (largest wins)
    for root, dirs, files in os.walk(base):
        for fname in files:
            if not fname.endswith('.jsonl'):
                continue
            full = os.path.join(root, fname)
            sid = fname.replace('.jsonl', '')

            norm = full.replace('\\', '/')
            if '/subagents/' in norm:
                continue

            try:
                size = os.path.getsize(full)
            except Exception:
                continue

            if size < 200:
                continue

            if sid in seen:
                prev_path, prev_size = seen[sid]
                if size > prev_size:
                    seen[sid] = (full, size)
            else:
                seen[sid] = (full, size)

    for full, _ in seen.values():
        try:
            rel = os.path.relpath(full, base)
            parts = rel.replace('\\', '/').split('/')
            proj = _norm_proj(parts[0], base)
            subfolder = '/'.join(parts[1:-1]) if len(parts) > 2 else ''
            sid = os.path.basename(full).replace('.jsonl', '')
            stat = os.stat(full)
            if stat.st_size < 200:
                continue
            msgs = extract_messages(full)
            if not msgs:
                continue
            title = get_session_title(full, msgs)
            date = msgs[-1]['ts'][:19] if msgs else '?'
            first_user = ''
            for m in msgs:
                if m['role'] == 'user':
                    first_user = m['text']
                    break
            tags = classify_session(title, first_user)
            refs = extract_references(full)
            arts = extract_artifacts(msgs)
            agent_graph = extract_agent_graph(full)
            display_title = title
            if subfolder:
                display_title = f'[{subfolder}] {title}'

            sessions.append({
                'id': sid,
                'title': display_title,
                'date': date,
                'project': proj,
                'msgCount': len(msgs),
                'messages': msgs,
                'tags': tags,
                'references': refs,
                'artifacts': arts,
                'agent_graph': agent_graph,
                'agent_tree': agent_graph['tree'] if agent_graph else None,
            })
        except Exception as e:
            print(f'  skip {os.path.basename(full).replace(".jsonl", "")}: {e}')
            continue

    sessions.sort(key=lambda s: s['date'], reverse=True)
    return sessions


CACHE_PATH = os.path.expanduser('~/.claude/shared-scripts/session/_cache.json')


def _session_from_jsonl(full, sid, proj, subfolder):
    """Extract session data from a single JSONL file. Returns dict or None."""
    try:
        stat = os.stat(full)
        if stat.st_size < 200:
            return None
        msgs = extract_messages(full)
        if not msgs:
            return None
        title = get_session_title(full, msgs)
        date = msgs[-1]['ts'][:19] if msgs else '?'
        first_user = ''
        for m in msgs:
            if m['role'] == 'user':
                first_user = m['text']
                break
        tags = classify_session(title, first_user)
        refs = extract_references(full)
        arts = extract_artifacts(msgs)
        agent_graph = extract_agent_graph(full)
        display_title = title
        if subfolder:
            display_title = f'[{subfolder}] {title}'
        return {
            'id': sid,
            'title': display_title,
            'date': date,
            'project': proj,
            'msgCount': len(msgs),
            'messages': msgs,
            'tags': tags,
            'references': refs,
            'artifacts': arts,
            'agent_graph': agent_graph,
            'agent_tree': agent_graph['tree'] if agent_graph else None,
        }
    except Exception:
        return None


def quick_update():
    """Read stdin for session_id, update only that session from cache, regenerate HTML."""
    raw = sys.stdin.buffer.read().decode('utf-8')
    data = json.loads(raw)
    sid = data.get('session_id', '')
    jsonl_path = data.get('transcript_path', '')
    cwd = os.path.basename(data.get('cwd', ''))

    if not sid or not jsonl_path or not os.path.isfile(jsonl_path):
        # Fall back to full scan
        return False

    # Load cache
    sessions = []
    if os.path.isfile(CACHE_PATH):
        try:
            with open(CACHE_PATH, 'r', encoding='utf-8') as f:
                sessions = json.load(f)
        except Exception:
            sessions = []

    # Determine project from jsonl path
    base = os.path.expanduser('~/.claude/projects')
    rel = os.path.relpath(jsonl_path, base)
    parts = rel.replace('\\', '/').split('/')
    proj = _norm_proj(parts[0], base) if parts else cwd
    subfolder = '/'.join(parts[1:-1]) if len(parts) > 2 else ''

    # Update or insert this session
    new_data = _session_from_jsonl(jsonl_path, sid, proj, subfolder)
    if not new_data:
        return False

    found = False
    for i, s in enumerate(sessions):
        if s.get('id') == sid:
            sessions[i] = new_data
            found = True
            break
    if not found:
        sessions.append(new_data)

    # Sort by date desc
    sessions.sort(key=lambda s: s.get('date', ''), reverse=True)

    # Save cache
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, ensure_ascii=False)

    return sessions


def main():
    out_dir = 'E:/Claude Code'
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'CC会话管理中心.html')
    sessions = None

    if '--quick' in sys.argv:
        sessions = quick_update()

    if not sessions:
        print('Scanning sessions...')
        sessions = scan_all_sessions()
        # Save cache for future quick updates
        try:
            with open(CACHE_PATH, 'w', encoding='utf-8') as f:
                json.dump(sessions, f, ensure_ascii=False)
        except Exception:
            pass

    if not sessions:
        print('No sessions found.')
        sys.exit(1)

    total_msgs = sum(s['msgCount'] for s in sessions)
    print(f'Found {len(sessions)} sessions, {total_msgs} total messages')

    iterations = load_iterations()

    data_json = json.dumps(sessions, ensure_ascii=False)
    data_json = data_json.replace('</script>', '<\\/script>')
    data_json = data_json.replace('</Script>', '<\\/Script>')
    data_json = data_json.replace('</SCRIPT>', '<\\/SCRIPT>')

    iter_json = json.dumps(iterations, ensure_ascii=False)

    # Split at placeholders instead of str.replace — the latter corrupts 18MB+ strings
    pos_all = HTML_TEMPLATE.find('__ALL_DATA__')
    pos_iter = HTML_TEMPLATE.find('__ITER_DATA__')
    html = (HTML_TEMPLATE[:pos_all] + data_json +
            HTML_TEMPLATE[pos_all + 13:pos_iter] + iter_json +
            HTML_TEMPLATE[pos_iter + 14:])

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    size_kb = os.path.getsize(out_path) / 1024
    chain_count = len(iterations.get('chains', {}))
    pending_count = len(iterations.get('pending_bridges', {}))
    print(f'Done: {out_path} ({size_kb:.0f} KB)')
    print(f'Iteration chains: {chain_count}, pending bridges: {pending_count}')


if __name__ == '__main__':
    main()
