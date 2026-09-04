from __future__ import annotations


def graph_response(rows: list[dict], *, allowed_confidence: set[str], limit: int = 500) -> dict:
    limit = max(1, min(int(limit), 500))
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    truncated = False

    for row in rows:
        confidence = str(row.get('confidence', '')).upper()
        if confidence not in allowed_confidence:
            continue
        from_id = f"{row['from_type']}:{row['from_value']}"
        to_id = f"{row['to_type']}:{row['to_value']}"
        needed = [nid for nid in (from_id, to_id) if nid not in nodes]
        if len(nodes) + len(needed) > limit:
            truncated = True
            continue
        nodes.setdefault(from_id, {'id': from_id, 'type': row['from_type'], 'label': row['from_value']})
        nodes.setdefault(to_id, {'id': to_id, 'type': row['to_type'], 'label': row['to_value']})
        edges.append({
            'id': f"{from_id}|{row['relation']}|{to_id}",
            'source': from_id,
            'target': to_id,
            'type': row['relation'],
            'confidence': confidence,
            'sources': row.get('sources', []) or [],
        })
    return {'nodes': list(nodes.values()), 'edges': edges, 'truncated': truncated, 'limit': limit}
