import subprocess
import time
from dataclasses import dataclass


class InvalidCommand(ValueError):
    pass


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    elapsed_seconds: float


def run_command(argv: list[str], timeout_seconds: int) -> CommandResult:
    if not argv:
        raise InvalidCommand("argv must not be empty")
    if timeout_seconds <= 0:
        raise InvalidCommand("timeout_seconds must be positive")
    started = time.monotonic()
    completed = subprocess.run(
        argv,
        shell=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    return CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        elapsed_seconds=time.monotonic() - started,
    )
