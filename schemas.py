from typing import Literal
from pydantic import BaseModel


class Finding(BaseModel):
    file: str
    line: int | None
    severity: Literal["info", "warning", "critical"]
    category: str
    message: str


class ReviewResult(BaseModel):
    findings: list[Finding]
