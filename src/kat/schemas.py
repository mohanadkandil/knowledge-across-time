"""Validated comparison shape; literal/semantic evidence checks are separate."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Shape(BaseModel):
    model_config=ConfigDict(extra="forbid")


class Evidence(Shape):
    source_id:str=Field(min_length=1)
    quote:str=Field(min_length=1)


class Match(Shape):
    source_id:str=Field(min_length=1)
    relevance:Literal["strong","partial","uncertain"]
    explanation:str=Field(min_length=1)


class Similarity(Shape):
    claim:str=Field(min_length=1)
    evidence:list[Evidence]=Field(min_length=1)


class Difference(Shape):
    kind:Literal["language","knowledge","coverage","uncertain"]
    historical_claim:str
    modern_claim:str
    explanation:str=Field(min_length=1)
    evidence:list[Evidence]=Field(min_length=1)


class Comparison(Shape):
    matches:list[Match]
    similarities:list[Similarity]
    differences:list[Difference]
    uncertainties:list[str]
    summary:str=Field(min_length=1)

    @model_validator(mode="after")
    def unmatched_is_uncertain(self):
        if not self.matches and not self.uncertainties:
            raise ValueError("No modern match requires an explicit uncertainty explanation")
        return self
