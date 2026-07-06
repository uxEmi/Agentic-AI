from pydantic import BaseModel


class Finding(BaseModel):
    file: str
    line: int
    severity: str
    category: str
    message: str


class ReviewResult(BaseModel):
    summary: str
    findings: list[Finding]
