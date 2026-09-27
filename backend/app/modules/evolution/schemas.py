from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

Step = Literal["preparation", "procedure", "final_control"]
Response = Literal["yes", "no", "observation"]


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
    control_completed: bool = False
    notes: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def unfinished_needs_notes(self):
        if not self.control_completed and not (self.notes or "").strip():
            raise ValueError("Session notes are required when control is not completed")
        return self


class EvolutionEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    patient_id: UUID
    work_item_id: UUID
    plan_item_id: UUID
    recorded_by: UUID
    created_at: datetime
    control_completed: bool | None
    answers: list[ChecklistAnswer]
    notes: str | None
