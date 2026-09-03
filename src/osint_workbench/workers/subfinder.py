import json

from osint_workbench.domain.models import NormalizedFinding


class SubfinderWorker:
    name = "subfinder"

    def build_command(self, target: str) -> list[str]:
        return ["subfinder", "-d", target, "-json", "-silent"]

    def parse_output(self, text: str) -> list[NormalizedFinding]:
        findings: list[NormalizedFinding] = []
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            host = payload.get("host")
            if not host:
                continue
            source = payload.get("source") or "subfinder"
            findings.append(
                NormalizedFinding(
                    entity_type="subdomain",
                    value=host,
                    source=str(source),
                    tool=self.name,
                    attributes=payload,
                )
            )
        return findings
