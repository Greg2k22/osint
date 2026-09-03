from osint_workbench.domain.models import Profile, RunRequest
from osint_workbench.domain.policy import validate_execution_policy


_PROFILE_WORKERS = {
    Profile.PERSON: ["sherlock"],
    Profile.DOMAIN: ["subfinder"],
    Profile.ORG: [],
    Profile.FULL: ["sherlock", "subfinder"],
}


def select_workers(request: RunRequest) -> list[str]:
    validate_execution_policy(request)
    return list(_PROFILE_WORKERS[request.profile])
