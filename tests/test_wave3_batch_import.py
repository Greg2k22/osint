from osint_workbench.services.batch_import import build_case_statements


def test_batch_import_uses_unwind_and_excludes_low():
    case = {'case_id':'c1','type':'DOMAIN','target':'example.org','path':'/tmp/c1'}
    records = [
        {'type':'DOMAIN','value':'example.org','host':'example.org','confidence':'SEED','sources':['target'],'resolved_ips':[]},
        {'type':'HOST','value':'www.example.org','host':'www.example.org','confidence':'HIGH','sources':['bbot','subfinder','theharvester'],'resolved_ips':['192.0.2.1']},
        {'type':'HOST','value':'old.example.org','host':'old.example.org','confidence':'LOW','sources':['bbot'],'resolved_ips':[]},
    ]
    statements = build_case_statements(case, records)
    text = '\n'.join(statements)
    assert 'UNWIND' in text
    assert 'www.example.org' in text
    assert 'old.example.org' not in text
    assert text.count('UNWIND') == 2
    assert text.count('www.example.org') == 2
