"""Event templates API — save and reuse event configurations."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_family_context
from app.db import get_db_session
from app.models import User
from app.models.event_template import EventTemplate
from app.schemas.event_template import EventTemplateCreate
from app.services.permissions import permissions

logger = logging.getLogger(__name__)

router = APIRouter()


def _template_to_dict(template: EventTemplate) -> dict:
    """Convert an event template to a response dict."""
    return {
        "id": str(template.id),
        "family_id": str(template.family_id),
        "name": template.name,
        "description": template.description,
        "template_json": template.template_json,
        "created_by_id": str(template.created_by_id) if template.created_by_id else None,
        "created_at": template.created_at.isoformat() if template.created_at else None,
    }


@router.get("")
async def list_templates(
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """List event templates for the current family."""
    family_id = user.active_family_id or ""

    result = await db.execute(
        select(EventTemplate)
        .where(EventTemplate.family_id == family_id)
        .order_by(EventTemplate.name.asc())
    )
    templates = list(result.scalars().all())

    return {"templates": [_template_to_dict(t) for t in templates]}


@router.post("", status_code=201)
async def create_template(
    data: EventTemplateCreate,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new event template. Requires family admin."""
    family_id = user.active_family_id or ""
    is_admin = await permissions.is_family_admin(db, user, family_id)
    if not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Only family admins can create event templates",
        )

    template = EventTemplate(
        family_id=family_id,
        name=data.name,
        description=data.description,
        template_json=data.template_json,
        created_by_id=user.id,
    )
    db.add(template)
    await db.flush()

    return _template_to_dict(template)


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete an event template. Requires family admin."""
    family_id = user.active_family_id or ""

    result = await db.execute(
        select(EventTemplate).where(
            EventTemplate.id == template_id,
            EventTemplate.family_id == family_id,
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    is_admin = await permissions.is_family_admin(db, user, family_id)
    if not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Only family admins can delete event templates",
        )

    await db.delete(template)
