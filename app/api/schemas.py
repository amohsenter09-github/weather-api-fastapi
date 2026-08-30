from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class PlaceCreate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    city: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def require_name_or_coords(self):
        if (self.city or "").strip() or (self.name or "").strip():
            return self
        if self.latitude is None or self.longitude is None:
            raise ValueError("Provide name/city or latitude and longitude")
        return self


class PlaceOut(BaseModel):
    id: UUID
    name: str
    latitude: float
    longitude: float
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class PlaceList(BaseModel):
    places: list[PlaceOut]


class ObservationOut(BaseModel):
    id: UUID
    place_id: UUID
    temperature: float | None
    windspeed: float | None
    weathercode: float | None
    fetched_at: datetime

    model_config = {"from_attributes": True}


class ObservationList(BaseModel):
    observations: list[ObservationOut]


class AlertCreate(BaseModel):
    place_id: UUID
    metric: str = "temperature"
    operator: str = Field(default="lt", pattern="^(lt|gt|lte|gte)$")
    threshold: float
    enabled: bool = True


class AlertOut(BaseModel):
    id: UUID
    place_id: UUID
    metric: str
    operator: str
    threshold: float
    enabled: bool
    triggered: bool | None = None

    model_config = {"from_attributes": True}


class AlertList(BaseModel):
    alerts: list[AlertOut]


class RefreshOut(BaseModel):
    observation: ObservationOut
    triggered_alerts: list[AlertOut]


class EvaluateOut(BaseModel):
    current_weather: dict
    triggered_alerts: list[AlertOut]
    nearby_places: list[PlaceOut]
