"""
@tool:      session-track-iteration
@summary:   记录和查询 Claude Code 会话之间的迭代关系（桥接/继续）
@tags:      session, iteration, bridge, chain
@inputs:    action (str) - save|resolve|list|chain|pending
@output:    JSON 输出到 stdout

用法:
  python track-iteration.py save <parent-session-id> <bridge-text-file>
      保存桥接记录，标记 parent 有待接收的子会话
  python track-iteration.py resolve <child-session-id>
      新会话启动时调用，自动查找 pending 的 parent 并建立关系
  python track-iteration.py pending
      检查是否有待接收的桥接（返回 parent id + bridge text）
  python track-iteration.py list
      列出所有迭代链
  python track-iteration.py chain <session-id>
      查询某个会话所属的完整迭代链
"""

import json, os, sys, datetime, uuid, glob as globmod

BASE = os.path.expanduser('~/.claude/projects')
DATA_FILE = os.path.join(BASE, 'session-iterations.json')


def load():
    """Load iteration data."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'chains': {}, 'pending_bridges': {}}


def save(data):
    """Save iteration data atomically."""
    tmp = DATA_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


def get_session_title(sid):
    """Try to find a session's title from its JSONL."""
    pattern = os.path.join(BASE, '*', f'{sid}.jsonl')
    matches = globmod.glob(pattern)
    if not matches:
        # Try directory mode
        pattern = os.path.join(BASE, '*', sid, '*.jsonl')
        matches = globmod.glob(pattern)
        if not matches:
            return '未知标题'
    try:
        with open(matches[0], 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    if obj.get('type') == 'user' and obj.get('message', {}).get('role') == 'user':
                        text = ''
                        for c in obj['message'].get('content', []):
                            if c.get('type') == 'text':
                                text = c['text'].strip()
                                break
                        text = text.replace('#', '').strip()
                        return text[:60] + ('...' if len(text) > 60 else '')
                except Exception:
                    continue
    except Exception:
        pass
    return '未知标题'


def cmd_save(parent_id, bridge_file):
    """Save a bridge: parent session creates a bridge for a future child."""
    data = load()
    bridge_text = ''
    if os.path.exists(bridge_file):
        with open(bridge_file, 'r', encoding='utf-8') as f:
            bridge_text = f.read()

    bridge_id = str(uuid.uuid4())[:8]
    chain_id = None

    # Find existing chain containing parent
    for cid, chain in data['chains'].items():
        for s in chain.get('sessions', []):
            if s['id'] == parent_id:
                chain_id = cid
                break
        if chain_id:
            break

    if not chain_id:
        chain_id = str(uuid.uuid4())[:8]
        title = get_session_title(parent_id)
        data['chains'][chain_id] = {
            'id': chain_id,
            'created': datetime.datetime.now().isoformat(),
            'sessions': [{'id': parent_id, 'order': 0, 'title': title, 'role': 'root'}],
            'bridges': {}
        }

    data['pending_bridges'][parent_id] = {
        'bridge_id': bridge_id,
        'bridge_text': bridge_text,
        'chain_id': chain_id,
        'created': datetime.datetime.now().isoformat()
    }

    save(data)
    print(json.dumps({'status': 'ok', 'action': 'save', 'parent': parent_id, 'bridge_id': bridge_id, 'chain_id': chain_id}, ensure_ascii=False))


def cmd_resolve(child_id):
    """Resolve a pending bridge when a new session starts."""
    data = load()
    pending = data.get('pending_bridges', {})

    # Find any pending bridge (usually the most recent)
    if not pending:
        print(json.dumps({'status': 'no_pending'}, ensure_ascii=False))
        return

    # Use the most recently created pending bridge
    sorted_pending = sorted(pending.items(), key=lambda x: x[1].get('created', ''), reverse=True)
    parent_id, bridge_info = sorted_pending[0]

    chain_id = bridge_info['chain_id']
    title = get_session_title(child_id)

    # Add child to chain
    chain = data['chains'].get(chain_id)
    if chain:
        order = len(chain['sessions'])
        chain['sessions'].append({
            'id': child_id, 'order': order, 'title': title,
            'parent': parent_id, 'role': 'continuation'
        })
        chain['bridges'][f'{parent_id}->{child_id}'] = bridge_info['bridge_text']

    # Remove from pending
    del data['pending_bridges'][parent_id]
    save(data)

    result = {
        'status': 'resolved',
        'parent': parent_id,
        'child': child_id,
        'chain_id': chain_id,
        'bridge_text': bridge_info.get('bridge_text', '')
    }
    print(json.dumps(result, ensure_ascii=False))


def cmd_pending():
    """Check if there's a pending bridge to continue from."""
    data = load()
    pending = data.get('pending_bridges', {})
    if not pending:
        print(json.dumps({'status': 'none'}, ensure_ascii=False))
        return
    sorted_pending = sorted(pending.items(), key=lambda x: x[1].get('created', ''), reverse=True)
    parent_id, bridge_info = sorted_pending[0]
    print(json.dumps({
        'status': 'pending',
        'parent': parent_id,
        'bridge_text': bridge_info.get('bridge_text', ''),
        'chain_id': bridge_info.get('chain_id', ''),
        'created': bridge_info.get('created', '')
    }, ensure_ascii=False))


def cmd_list():
    """List all iteration chains."""
    data = load()
    chains = []
    for cid, chain in data.get('chains', {}).items():
        sessions = chain.get('sessions', [])
        chains.append({
            'id': cid,
            'created': chain.get('created', ''),
            'session_count': len(sessions),
            'sessions': [{'id': s['id'], 'order': s.get('order', 0), 'title': s.get('title', ''),
                          'role': s.get('role', ''), 'parent': s.get('parent', '')}
                         for s in sessions]
        })
    chains.sort(key=lambda c: c['created'], reverse=True)
    print(json.dumps({'status': 'ok', 'chains': chains}, ensure_ascii=False, indent=2))


def cmd_chain(session_id):
    """Show the chain containing a specific session."""
    data = load()
    for cid, chain in data.get('chains', {}).items():
        for s in chain.get('sessions', []):
            if s['id'] == session_id:
                print(json.dumps({
                    'status': 'ok',
                    'chain_id': cid,
                    'created': chain.get('created', ''),
                    'sessions': chain.get('sessions', []),
                    'bridges': chain.get('bridges', {})
                }, ensure_ascii=False, indent=2))
                return
    print(json.dumps({'status': 'not_found'}, ensure_ascii=False))


if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else 'list'
    if action == 'save' and len(sys.argv) >= 4:
        cmd_save(sys.argv[2], sys.argv[3])
    elif action == 'resolve' and len(sys.argv) >= 3:
        cmd_resolve(sys.argv[2])
    elif action == 'pending':
        cmd_pending()
    elif action == 'list':
        cmd_list()
    elif action == 'chain' and len(sys.argv) >= 3:
        cmd_chain(sys.argv[2])
    else:
        print(f'Usage: ... {action} [...]', file=sys.stderr)
        sys.exit(1)
