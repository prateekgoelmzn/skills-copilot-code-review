"""
Announcement endpoints for the High School Management System API
"""

from datetime import date
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementPayload(BaseModel):
    message: str = Field(..., min_length=1, max_length=280)
    expiration_date: str
    start_date: Optional[str] = None


def _require_teacher(teacher_username: Optional[str]) -> Dict[str, Any]:
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Authentication required")

    return teacher


def _parse_iso_date(value: Optional[str], field_name: str, required: bool = False) -> Optional[str]:
    if value is None or value == "":
        if required:
            raise HTTPException(status_code=400, detail=f"{field_name} is required")
        return None

    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must use YYYY-MM-DD format"
        ) from exc


def _normalize_payload(payload: AnnouncementPayload) -> Dict[str, Optional[str]]:
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    start_date = _parse_iso_date(payload.start_date, "start_date")
    expiration_date = _parse_iso_date(payload.expiration_date, "expiration_date", required=True)

    if start_date and start_date > expiration_date:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be after expiration_date"
        )

    return {
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date,
    }


def _announcement_status(start_date: Optional[str], expiration_date: str) -> str:
    today = date.today().isoformat()
    if expiration_date < today:
        return "expired"
    if start_date and start_date > today:
        return "scheduled"
    return "active"


def _serialize_announcement(document: Dict[str, Any]) -> Dict[str, Any]:
    start_date = document.get("start_date")
    expiration_date = document["expiration_date"]
    return {
        "id": document["_id"],
        "message": document["message"],
        "start_date": start_date,
        "expiration_date": expiration_date,
        "status": _announcement_status(start_date, expiration_date),
    }


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get announcements that are active today."""
    today = date.today().isoformat()
    query = {
        "expiration_date": {"$gte": today},
        "$or": [
            {"start_date": None},
            {"start_date": {"$exists": False}},
            {"start_date": {"$lte": today}},
        ],
    }

    announcements = announcements_collection.find(query).sort([
        ("expiration_date", 1),
        ("_id", 1),
    ])

    return [_serialize_announcement(announcement) for announcement in announcements]


@router.get("/manage", response_model=List[Dict[str, Any]])
def get_all_announcements(teacher_username: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """Get all announcements for management purposes. Requires teacher authentication."""
    _require_teacher(teacher_username)

    announcements = announcements_collection.find().sort([
        ("expiration_date", 1),
        ("start_date", 1),
        ("_id", 1),
    ])
    return [_serialize_announcement(announcement) for announcement in announcements]


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_announcement(payload: AnnouncementPayload, teacher_username: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Create a new announcement. Requires teacher authentication."""
    _require_teacher(teacher_username)
    document = {
        "_id": uuid4().hex,
        **_normalize_payload(payload),
    }
    announcements_collection.insert_one(document)
    return _serialize_announcement(document)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementPayload,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Update an announcement. Requires teacher authentication."""
    _require_teacher(teacher_username)
    updated_fields = _normalize_payload(payload)

    result = announcements_collection.update_one(
        {"_id": announcement_id},
        {"$set": updated_fields}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    document = announcements_collection.find_one({"_id": announcement_id})
    if not document:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return _serialize_announcement(document)


@router.delete("/{announcement_id}", response_model=Dict[str, str])
def delete_announcement(announcement_id: str, teacher_username: Optional[str] = Query(None)) -> Dict[str, str]:
    """Delete an announcement. Requires teacher authentication."""
    _require_teacher(teacher_username)

    result = announcements_collection.delete_one({"_id": announcement_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted"}