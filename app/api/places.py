import logging
import math
from types import SimpleNamespace
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    AlertCreate,
    AlertList,
    AlertOut,
    EvaluateOut,
    ObservationList,
    ObservationOut,
    PlaceCreate,
    PlaceList,
    PlaceOut,
    RefreshOut,
)
from app.core.config import get_settings
from app.db.models import Alert, Observation, Place
from app.db.session import get_session
from app.services.weather_client import WeatherClient

logger = logging.getLogger(__name__)
router = APIRouter(tags=["places"])

_OPS = {
    "lt": lambda value, threshold: value < threshold,
    "gt": lambda value, threshold: value > threshold,
    "lte": lambda value, threshold: value <= threshold,
    "gte": lambda value, threshold: value >= threshold,
}


def _place_name(body: PlaceCreate, geo_name: str | None) -> str:
    if body.name and body.name.strip():
        return body.name.strip()
    if geo_name:
        return geo_name
    if body.city and body.city.strip():
        return body.city.strip()
    return f"{body.latitude},{body.longitude}"


async def _resolve_coords(body: PlaceCreate) -> tuple[float, float, str | None]:
    lookup = (body.city or body.name or "").strip()
    if body.latitude is not None and body.longitude is not None and not (body.city or "").strip():
        return float(body.latitude), float(body.longitude), None
    if not lookup:
        return float(body.latitude), float(body.longitude), None
    settings = get_settings()
    geo = await WeatherClient(settings).geocode_city(lookup)
    return float(geo["latitude"]), float(geo["longitude"]), geo.get("name")


def _metric_value(obs: Observation, metric: str) -> float | None:
    if metric == "temperature":
        return obs.temperature
    if metric == "windspeed":
        return obs.windspeed
    return None


def _alert_triggered(alert: Alert, obs: Observation) -> bool:
    if not alert.enabled:
        return False
    value = _metric_value(obs, alert.metric)
    if value is None:
        return False
    op = _OPS.get(alert.operator)
    return bool(op and op(value, alert.threshold))


@router.post("/places", status_code=201, response_model=PlaceOut)
async def create_place(body: PlaceCreate, session: AsyncSession = Depends(get_session)):
    try:
        lat, lon, geo_name = await _resolve_coords(body)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except httpx.HTTPError as e:
        logger.exception("Upstream geocoding provider error")
        raise HTTPException(status_code=502, detail="Upstream geocoding provider error") from e
    place = Place(name=_place_name(body, geo_name), latitude=lat, longitude=lon)
    session.add(place)
    await session.commit()
    await session.refresh(place)
    return place


@router.get("/places", response_model=PlaceList)
async def list_places(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Place).order_by(Place.created_at.desc()))
    return PlaceList(places=list(result.scalars().all()))


@router.get("/places/{place_id}", response_model=PlaceOut)
async def get_place(place_id: UUID, session: AsyncSession = Depends(get_session)):
    place = await session.get(Place, place_id)
    if place is None:
        raise HTTPException(status_code=404, detail="Place not found")
    return place


@router.delete("/places/{place_id}", status_code=204)
async def delete_place(place_id: UUID, session: AsyncSession = Depends(get_session)):
    place = await session.get(Place, place_id)
    if place is None:
        raise HTTPException(status_code=404, detail="Place not found")
    await session.delete(place)
    await session.commit()


@router.post("/places/{place_id}/refresh", response_model=RefreshOut)
async def refresh_place(place_id: UUID, session: AsyncSession = Depends(get_session)):
    place = await session.get(Place, place_id)
    if place is None:
        raise HTTPException(status_code=404, detail="Place not found")
    settings = get_settings()
    try:
        data = await WeatherClient(settings).current_weather(place.latitude, place.longitude)
    except httpx.HTTPError as e:
        logger.exception("Upstream weather provider error")
        raise HTTPException(status_code=502, detail="Upstream weather provider error") from e
    current = data.get("current_weather") or {}
    obs = Observation(
        place_id=place.id,
        temperature=current.get("temperature"),
        windspeed=current.get("windspeed"),
        weathercode=current.get("weathercode"),
    )
    session.add(obs)
    await session.commit()
    await session.refresh(obs)
    alerts = (await session.execute(select(Alert).where(Alert.place_id == place.id))).scalars().all()
    triggered = []
    for alert in alerts:
        item = AlertOut.model_validate(alert)
        item.triggered = _alert_triggered(alert, obs)
        if item.triggered:
            triggered.append(item)
    return RefreshOut(observation=obs, triggered_alerts=triggered)


@router.get("/places/{place_id}/history", response_model=ObservationList)
async def place_history(
    place_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    place = await session.get(Place, place_id)
    if place is None:
        raise HTTPException(status_code=404, detail="Place not found")
    result = await session.execute(
        select(Observation).where(Observation.place_id == place_id).order_by(Observation.fetched_at.desc()).limit(limit)
    )
    return ObservationList(observations=list(result.scalars().all()))


@router.post("/alerts", status_code=201, response_model=AlertOut)
async def create_alert(body: AlertCreate, session: AsyncSession = Depends(get_session)):
    place = await session.get(Place, body.place_id)
    if place is None:
        raise HTTPException(status_code=404, detail="Place not found")
    alert = Alert(
        place_id=body.place_id,
        metric=body.metric,
        operator=body.operator,
        threshold=body.threshold,
        enabled=body.enabled,
    )
    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return alert


@router.get("/alerts", response_model=AlertList)
async def list_alerts(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Alert).order_by(Alert.created_at.desc()))
    return AlertList(alerts=list(result.scalars().all()))


def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    rlat1, rlon1, rlat2, rlon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return 2 * 6371000 * math.asin(min(1.0, math.sqrt(a)))


@router.get("/alerts/evaluate", response_model=EvaluateOut)
async def evaluate_alerts(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_m: float = Query(default=5000, ge=100, le=50000),
    session: AsyncSession = Depends(get_session),
):
    settings = get_settings()
    try:
        data = await WeatherClient(settings).current_weather(latitude, longitude)
    except httpx.HTTPError as e:
        logger.exception("Upstream weather provider error")
        raise HTTPException(status_code=502, detail="Upstream weather provider error") from e
    current = data.get("current_weather") or {}
    obs = SimpleNamespace(
        temperature=current.get("temperature"),
        windspeed=current.get("windspeed"),
        weathercode=current.get("weathercode"),
    )
    places = list((await session.execute(select(Place))).scalars().all())
    nearby = [place for place in places if _distance_m(latitude, longitude, place.latitude, place.longitude) <= radius_m]
    nearby_ids = {place.id for place in nearby}
    alerts = list((await session.execute(select(Alert).where(Alert.enabled.is_(True)))).scalars().all())
    triggered = []
    for alert in alerts:
        if alert.place_id not in nearby_ids:
            continue
        item = AlertOut.model_validate(alert)
        item.triggered = _alert_triggered(alert, obs)
        if item.triggered:
            triggered.append(item)
    return EvaluateOut(current_weather=current, triggered_alerts=triggered, nearby_places=nearby)
