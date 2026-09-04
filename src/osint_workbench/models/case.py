from pydantic import BaseModel


class CaseMeta(BaseModel):
    case_id: str
    type: str
    target: str
    mode: str
    status: str
