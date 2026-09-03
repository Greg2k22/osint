from osint_workbench.domain.models import ExecutionMode, RunRequest


class PolicyViolation(ValueError):
    """Raised when an execution request violates safety policy."""


def validate_execution_policy(request: RunRequest) -> None:
    if request.mode is ExecutionMode.PASSIVE:
        return
    if request.active_authorized is not True:
        raise PolicyViolation("ACTIVE mode requires explicit authorization")
    if not request.active_scope or not request.active_scope.strip():
        raise PolicyViolation("ACTIVE mode requires an explicit non-empty scope")
