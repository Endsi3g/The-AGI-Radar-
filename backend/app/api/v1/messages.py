from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db
from app.models.message import Message
from app.models.interaction import Interaction
from app.models.user import User
from app.schemas.message import MessageCreate, MessageUpdate, MessageApprove, MessageReject, MessageResponse
from app.dependencies import get_current_user
from app.core.exceptions import NotFoundError, BadRequestError

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("", response_model=list[MessageResponse])
async def list_messages(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    msg_status: str | None = Query(None, alias="status"),
    channel: str | None = None,
    direction: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    filters = []
    if msg_status:
        filters.append(Message.status == msg_status)
    if channel:
        filters.append(Message.channel == channel)
    if direction:
        filters.append(Message.direction == direction)

    query = select(Message).order_by(Message.created_at.desc()).limit(limit).offset(offset)
    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    body: MessageCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    msg = Message(**body.model_dump(), created_by=current_user.id, status="pending_approval")
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Message).where(Message.id == message_id))
    msg = result.scalar_one_or_none()
    if not msg:
        raise NotFoundError("Message")
    return msg


@router.patch("/{message_id}", response_model=MessageResponse)
async def update_message(
    message_id: UUID,
    body: MessageUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Message).where(Message.id == message_id))
    msg = result.scalar_one_or_none()
    if not msg:
        raise NotFoundError("Message")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(msg, field, value)
    msg.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(msg)
    return msg


@router.post("/{message_id}/approve", response_model=MessageResponse)
async def approve_message(
    message_id: UUID,
    body: MessageApprove,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    from app.tasks.email_tasks import send_email_message
    from app.tasks.sms_tasks import send_sms_message

    result = await db.execute(select(Message).where(Message.id == message_id))
    msg = result.scalar_one_or_none()
    if not msg:
        raise NotFoundError("Message")
    if msg.status not in ("draft", "pending_approval"):
        raise BadRequestError(f"Cannot approve message with status '{msg.status}'")

    # Apply final edits if provided
    if body.body:
        msg.body = body.body
    if body.subject:
        msg.subject = body.subject

    msg.status = "approved"
    msg.approved_by = current_user.id
    msg.approved_at = datetime.now(timezone.utc)
    msg.updated_at = datetime.now(timezone.utc)

    # Log interaction
    interaction = Interaction(
        lead_id=msg.lead_id,
        user_id=current_user.id,
        message_id=msg.id,
        type=f"{msg.channel}_sent",
        notes=f"Message approuvé par {current_user.full_name}",
    )
    db.add(interaction)
    await db.commit()
    await db.refresh(msg)

    # Dispatch send task
    if msg.channel == "email":
        send_email_message.delay(str(msg.id))
    elif msg.channel == "sms":
        send_sms_message.delay(str(msg.id))

    return msg


@router.post("/{message_id}/reject", response_model=MessageResponse)
async def reject_message(
    message_id: UUID,
    body: MessageReject,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Message).where(Message.id == message_id))
    msg = result.scalar_one_or_none()
    if not msg:
        raise NotFoundError("Message")

    msg.status = "rejected"
    msg.updated_at = datetime.now(timezone.utc)

    interaction = Interaction(
        lead_id=msg.lead_id,
        user_id=current_user.id,
        message_id=msg.id,
        type="note_added",
        notes=f"Message rejeté. Raison: {body.reason or 'Non spécifiée'}",
    )
    db.add(interaction)
    await db.commit()
    await db.refresh(msg)
    return msg
