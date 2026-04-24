"""
ThirdEye — Pydantic Models
All request/response schemas and internal data models.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Request Models ──

class PersonCreate(BaseModel):
    """Request model for creating a new person search profile."""
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    description: Optional[str] = None
    last_known_location: Optional[str] = None
    last_known_lat: Optional[float] = None
    last_known_lng: Optional[float] = None
    contact_info: Optional[str] = None


class SightingSubmit(BaseModel):
    """Request model for submitting a crowdsource sighting."""
    location: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    description: Optional[str] = None


# ── Response Models ──

class PersonResponse(BaseModel):
    """Response model for a person profile."""
    id: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    description: Optional[str] = None
    last_known_location: Optional[str] = None
    last_known_lat: Optional[float] = None
    last_known_lng: Optional[float] = None
    status: str = "active"
    current_radius: float = 1.0
    epicenter_lat: Optional[float] = None
    epicenter_lng: Optional[float] = None
    share_token: Optional[str] = None
    photos: list[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_scan_at: Optional[str] = None
    total_matches: int = 0


class MatchResponse(BaseModel):
    """Response model for a match record."""
    id: str
    person_id: str
    source: str
    url: Optional[str] = None
    image_url: Optional[str] = None
    similarity: float
    confidence_label: str
    location: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    raw_text: Optional[str] = None
    reviewed: bool = False
    confirmed: bool = False
    created_at: Optional[str] = None


class LocationResponse(BaseModel):
    """Response model for a location point."""
    id: str
    person_id: str
    location: str
    lat: float
    lng: float
    source: Optional[str] = None
    confidence: Optional[float] = None
    timestamp: str


class MapData(BaseModel):
    """Response model for map view data."""
    epicenter: Optional[dict] = None
    radius_miles: float = 1.0
    pins: list[dict] = []
    cameras: list[dict] = []
    path: list[dict] = []


class StatsResponse(BaseModel):
    """Response model for dashboard stats."""
    status: str = "active"
    total_matches: int = 0
    high_confidence_matches: int = 0
    sources_checked: int = 0
    current_radius: float = 1.0
    time_running_hours: float = 0
    next_scan_in_minutes: float = 0
    last_scan_at: Optional[str] = None


# ── Internal Models ──

class SearchResult(BaseModel):
    """Internal model returned by all search workers."""
    source: str
    url: Optional[str] = None
    image_url: Optional[str] = None
    timestamp: Optional[datetime] = None
    location: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    raw_text: Optional[str] = None
    similarity: float = 0.0
    confidence_label: str = "DISCARD"
    image_data: Optional[bytes] = None  # Raw image bytes for face matching


class PersonProfile(BaseModel):
    """Internal model passed to search workers."""
    id: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    description: Optional[str] = None
    last_known_location: Optional[str] = None
    last_known_lat: Optional[float] = None
    last_known_lng: Optional[float] = None
    photos: list[str] = []
    embeddings: list = []
    current_radius: float = 1.0
    epicenter_lat: Optional[float] = None
    epicenter_lng: Optional[float] = None


class AlertPayload(BaseModel):
    """Internal model for alert data."""
    confidence: float
    label: str
    source: str
    location: Optional[str] = None
    timestamp: str
    image_url: Optional[str] = None
    post_url: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    person_name: Optional[str] = None
    match_id: Optional[str] = None


# ── WebSocket Event Models ──

class WSEvent(BaseModel):
    """WebSocket event pushed to frontend."""
    event: str  # new_match, radius_expanded, scan_complete, alert_sent
    data: dict = {}
