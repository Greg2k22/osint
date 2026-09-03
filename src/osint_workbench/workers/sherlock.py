from osint_workbench.domain.models import NormalizedFinding


class SherlockWorker:
    name = "sherlock"

    def build_command(self, target: str) -> list[str]:
        return ["sherlock", target, "--print-found"]

    def parse_output(self, text: str) -> list[NormalizedFinding]:
        findings: list[NormalizedFinding] = []
        for line in text.splitlines():
            value = line.strip()
            if value.startswith("http://") or value.startswith("https://"):
                findings.append(
                    NormalizedFinding(
                        entity_type="account",
                        value=value,
                        source=value,
                        tool=self.name,
                    )
                )
        return findings
