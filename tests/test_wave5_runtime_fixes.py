from pathlib import Path


def test_holehe_image_installs_requests():
    dockerfile = Path("Dockerfile.holehe").read_text()

    assert "holehe==1.61" in dockerfile
    assert "requests" in dockerfile
    assert 'ENTRYPOINT ["holehe"]' in dockerfile


def test_runner_captures_exit_code_inside_else():
    script = Path("scripts/job-runner.sh").read_text()

    assert 'else\n  CODE=$?\nfi' in script
    assert '\nfi\n\nCODE=$?\n' not in script
