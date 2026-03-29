"""Poll templates API — CRUD for reusable poll configurations."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_family_context
from app.db import get_db_session
from app.models import User
from app.models.poll_template import PollTemplate
from app.schemas.poll_template import PollTemplateCreate, PollTemplateResponse
from app.services.permissions import permissions

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
async def list_templates(
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """List available poll templates (built-in + family custom)."""
    family_id = user.active_family_id

    result = await db.execute(
        select(PollTemplate)
        .where(
            or_(
                PollTemplate.is_builtin.is_(True),
                PollTemplate.family_id == family_id,
            )
        )
        .order_by(PollTemplate.is_builtin.desc(), PollTemplate.name)
    )
    templates = result.scalars().all()

    return {"templates": [PollTemplateResponse.from_model(t) for t in templates]}


@router.post("", status_code=201)
async def create_template(
    data: PollTemplateCreate,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a custom poll template for the current family."""
    family_id = user.active_family_id or ""

    # Only admins can create templates
    is_admin = await permissions.is_family_admin(db, user, family_id)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Only family admins can create poll templates")

    template = PollTemplate(
        family_id=family_id,
        name=data.name,
        description=data.description,
        options_json=json.dumps(data.options),
        allow_multiple=data.allow_multiple,
        is_builtin=False,
        created_by_id=user.id,
    )
    db.add(template)
    await db.flush()

    return PollTemplateResponse.from_model(template)


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete a custom poll template. Built-in templates cannot be deleted."""
    result = await db.execute(select(PollTemplate).where(PollTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if template.is_builtin:
        raise HTTPException(status_code=400, detail="Cannot delete built-in templates")

    if template.family_id != user.active_family_id:
        raise HTTPException(status_code=404, detail="Template not found")

    is_admin = await permissions.is_family_admin(db, user, user.active_family_id or "")
    if not is_admin:
        raise HTTPException(status_code=403, detail="Only family admins can delete poll templates")

    await db.delete(template)
