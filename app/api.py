import asyncio
import json
import logging
from datetime import datetime
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal, get_session
from app.models import Patient
from app.schemas import (
    AppointmentCreate,
    AppointmentOut,
    ChatRequest,
    ChatResponse,
    OutboundCallRequest,
    PatientCreate,
    SlotOut,
)
from app.services.agent import respond
from app.services.booking import (
    BookingError,
    book_appointment,
    cancel_appointment,
    list_available_slots,
)
from app.services.cartesia import CartesiaClient, CartesiaNotConfigured

router = APIRouter(prefix="/api/v1")
log = logging.getLogger(__name__)


@router.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now().astimezone().isoformat()}


@router.post("/patients", status_code=201)
async def create_patient(data: PatientCreate, session: AsyncSession = Depends(get_session)):
    p = Patient(**data.model_dump())
    session.add(p)
    try:
        await session.commit()
        await session.refresh(p)
    except Exception as e:
        await session.rollback()
        raise HTTPException(409, "Phone already registered") from e
    return {
        "id": p.id,
        "full_name": p.full_name,
        "phone": p.phone,
        "consent_to_call": p.consent_to_call,
    }


@router.get("/slots", response_model=list[SlotOut])
async def slots(
    department: str | None = None,
    doctor: str | None = None,
    limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
):
    return await list_available_slots(session, department, doctor, limit)


@router.post("/appointments", response_model=AppointmentOut, status_code=201)
async def create_appointment(data: AppointmentCreate, session: AsyncSession = Depends(get_session)):
    try:
        return await book_appointment(session, **data.model_dump())
    except BookingError as e:
        raise HTTPException(409, str(e)) from e


@router.post("/appointments/{appointment_id}/cancel", response_model=AppointmentOut)
async def cancel(appointment_id: UUID, session: AsyncSession = Depends(get_session)):
    try:
        return await cancel_appointment(session, appointment_id)
    except BookingError as e:
        raise HTTPException(404, str(e)) from e


@router.post("/chat", response_model=ChatResponse)
async def chat(data: ChatRequest, session: AsyncSession = Depends(get_session)):
    conv, turn, result, latency = await respond(
        session, data.message, data.conversation_id, data.channel
    )
    return ChatResponse(
        conversation_id=conv.id,
        turn_id=turn,
        answer=result.answer,
        citations=result.citations,
        requires_human=result.requires_human,
        emergency=result.emergency,
        latency_ms=latency,
    )


@router.post("/telephony/outbound")
async def outbound(
    data: OutboundCallRequest, request: Request, session: AsyncSession = Depends(get_session)
):
    if data.patient_id:
        p = await session.get(Patient, data.patient_id)
        if not p or not p.consent_to_call:
            raise HTTPException(403, "Patient consent is required")
    try:
        return await CartesiaClient().place_call(
            data.to_number, {"purpose": data.purpose, "patient_id": str(data.patient_id or "")}
        )
    except (CartesiaNotConfigured, PermissionError) as e:
        raise HTTPException(503, str(e)) from e


@router.post("/telephony/events")
async def telephony_event(request: Request):
    # Configure Cartesia to send call lifecycle events here; persist only non-sensitive metadata.
    payload = await request.json()
    log.info(
        "telephony_event",
        extra={"event_type": payload.get("type"), "call_id": payload.get("call_id")},
    )
    return {"received": True}


@router.websocket("/voice")
async def voice(ws: WebSocket):
    await ws.accept()
    cartesia = CartesiaClient()
    stt = None
    conversation_id = None
    final_parts = []
    try:
        stt = await cartesia.stt_connect()
        await ws.send_json(
            {
                "type": "ready",
                "input": {"encoding": "pcm_s16le", "sample_rate": 16000},
                "output": {
                    "encoding": "pcm_s16le",
                    "sample_rate": cartesia.s.cartesia_tts_sample_rate,
                },
            }
        )

        async def read_stt():
            nonlocal conversation_id, final_parts
            async for raw in stt:
                event = json.loads(raw)
                if event.get("type") == "transcript":
                    await ws.send_json(
                        {
                            "type": "transcript",
                            "text": event.get("text", ""),
                            "is_final": event.get("is_final", False),
                        }
                    )
                    if event.get("is_final"):
                        final_parts.append(event.get("text", ""))
                elif event.get("type") == "flush_done":
                    transcript = "".join(final_parts).strip()
                    final_parts = []
                    if not transcript:
                        continue
                    async with SessionLocal() as session:
                        conv, turn, result, latency = await respond(
                            session, transcript, conversation_id, "web"
                        )
                        conversation_id = conv.id
                    await ws.send_json(
                        {
                            "type": "assistant",
                            "text": result.answer,
                            "conversation_id": str(conversation_id),
                            "turn_id": turn,
                            "citations": result.citations,
                            "latency_ms": latency,
                        }
                    )
                    async for chunk in cartesia.tts_chunks(result.answer):
                        await ws.send_bytes(chunk)
                    await ws.send_json({"type": "audio_end", "turn_id": turn})

        reader = asyncio.create_task(read_stt())
        while True:
            msg = await ws.receive()
            if msg.get("bytes") is not None:
                await stt.send(msg["bytes"])
            elif msg.get("text"):
                cmd = json.loads(msg["text"])
                if cmd.get("type") == "end_turn":
                    await stt.send("finalize")
                elif cmd.get("type") == "interrupt":
                    await ws.send_json({"type": "interrupted"})
                elif cmd.get("type") == "close":
                    break
        reader.cancel()
    except WebSocketDisconnect:
        pass
    except CartesiaNotConfigured as e:
        await ws.send_json({"type": "error", "message": str(e)})
    except Exception:
        log.exception("voice websocket failed")
        await ws.send_json({"type": "error", "message": "Voice service failed"})
    finally:
        if stt:
            try:
                await stt.send("close")
                await stt.close()
            except Exception:
                pass
