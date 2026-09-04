from osint_workbench.services.scoring import confidence_for, independent_source_groups


def test_confidence_uses_independent_source_groups():
    assert confidence_for(set()) == "SEED"
    assert confidence_for({"bbot"}) == "LOW"
    assert confidence_for({"bbot", "subfinder"}) == "MEDIUM"
    assert confidence_for({"bbot", "subfinder", "theharvester"}) == "HIGH"


def test_bbot_modules_collapse_to_one_source_group():
    groups = independent_source_groups(["bbot:crt_db", "bbot:urlscan", "subfinder", "target"])
    assert groups == {"bbot", "subfinder"}
