from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.odontogram.models import DentalCondition

Step = Literal["preparation", "procedure", "final_control"]
Response = Literal["yes", "no", "observation"]
STEPS = {"preparation", "procedure", "final_control"}


class ChecklistAnswer(BaseModel):
    step: Step
    response: Response
    observation: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def require_observation_text(self):
        if self.response == "observation" and not (self.observation or "").strip():
            raise ValueError("An observation response needs explanatory text")
        return self


class EvolutionEntryCreate(BaseModel):
    answers: list[ChecklistAnswer] = Field(min_length=3, max_length=3)
    notes: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def all_steps_once(self):
        if {answer.step for answer in self.answers} != STEPS:
            raise ValueError("All three checklist steps are required once")
        return self


class EvolutionEntryRead(EvolutionEntryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    patient_id: UUID
    work_item_id: UUID
    plan_item_id: UUID
    recorded_by: UUID
    created_at: datetime


class CompleteProcedure(BaseModel):
    result_condition: DentalCondition
    result_note: str | None = Field(default=None, max_length=2000)
