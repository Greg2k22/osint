from osint_workbench.services.graph_service import graph_response


def test_graph_response_deduplicates_nodes_and_filters_confidence():
    rows = [
        {'from_type':'Domain','from_value':'example.org','relation':'HAS_HOST','to_type':'Host','to_value':'www.example.org','confidence':'HIGH','sources':['bbot','subfinder','theharvester']},
        {'from_type':'Domain','from_value':'example.org','relation':'HAS_HOST','to_type':'Host','to_value':'old.example.org','confidence':'LOW','sources':['bbot']},
        {'from_type':'Host','from_value':'www.example.org','relation':'RESOLVES_TO','to_type':'IP','to_value':'192.0.2.1','confidence':'MEDIUM','sources':['bbot','subfinder']},
    ]
    result = graph_response(rows, allowed_confidence={'HIGH','MEDIUM'}, limit=500)
    assert {n['id'] for n in result['nodes']} == {'Domain:example.org','Host:www.example.org','IP:192.0.2.1'}
    assert len(result['edges']) == 2


def test_graph_response_enforces_limit():
    rows = [
        {'from_type':'Domain','from_value':'example.org','relation':'HAS_HOST','to_type':'Host','to_value':f'h{i}.example.org','confidence':'HIGH','sources':['x','y','z']}
        for i in range(10)
    ]
    result = graph_response(rows, allowed_confidence={'HIGH'}, limit=3)
    assert len(result['nodes']) <= 3
    assert result['truncated'] is True
