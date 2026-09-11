import json
import uuid
from urllib.parse import urlencode

import httpx
import websockets

from app.config import get_settings


class CartesiaNotConfigured(RuntimeError):
    pass


class CartesiaClient:
    def __init__(self):
        self.s = get_settings()

    def _key(self) -> str:
        if not self.s.cartesia_api_key:
            raise CartesiaNotConfigured("Set CARTESIA_API_KEY")
        return self.s.cartesia_api_key

    def _headers(self) -> dict[str, str]:
        return {"X-API-Key": self._key(), "Cartesia-Version": self.s.cartesia_version}

    async def stt_connect(self):
        query = urlencode(
            {
                "model": self.s.cartesia_stt_model,
                "encoding": "pcm_s16le",
                "sample_rate": 16000,
                "cartesia_version": self.s.cartesia_version,
                "keyterm": ["cardiology", "dermatology", "appointment"],
            },
            doseq=True,
        )
        return await websockets.connect(
            f"wss://api.cartesia.ai/stt/websocket?{query}",
            additional_headers={"X-API-Key": self._key()},
            max_size=8_000_000,
        )

    async def tts_chunks(self, text: str):
        uri = f"wss://api.cartesia.ai/tts/websocket?cartesia_version={self.s.cartesia_version}"
        async with websockets.connect(
            uri, additional_headers={"X-API-Key": self._key()}, max_size=8_000_000
        ) as ws:
            context_id = str(uuid.uuid4())
            await ws.send(
                json.dumps(
                    {
                        "model_id": self.s.cartesia_tts_model,
                        "transcript": text,
                        "voice": {"id": self.s.cartesia_voice_id},
                        "output_format": {
                            "container": "raw",
                            "encoding": "pcm_s16le",
                            "sample_rate": self.s.cartesia_tts_sample_rate,
                        },
                        "locale": self.s.cartesia_locale,
                        "context_id": context_id,
                        "continue": False,
                        "add_timestamps": True,
                        "generation_config": {"emotion": "calm", "speed": 1.0},
                    }
                )
            )
            async for raw in ws:
                msg = json.loads(raw)
                if msg.get("type") == "chunk" and msg.get("data"):
                    import base64

                    yield base64.b64decode(msg["data"])
                elif msg.get("type") in {"done", "error"}:
                    if msg.get("type") == "error":
                        raise RuntimeError(msg.get("message", "Cartesia TTS error"))
                    break

    async def place_call(self, to_number: str, metadata: dict):
        if not self.s.allow_outbound_calls:
            raise PermissionError("Outbound calls disabled; set ALLOW_OUTBOUND_CALLS=true")
        if not self.s.cartesia_agent_id or not self.s.cartesia_from_number_id:
            raise CartesiaNotConfigured("Set CARTESIA_AGENT_ID and CARTESIA_FROM_NUMBER_ID")
        payload = {
            "from_number_id": self.s.cartesia_from_number_id,
            "agent_id": self.s.cartesia_agent_id,
            "ringing_timeout_seconds": 30,
            "outbound_calls": [{"to_number": to_number, "metadata": metadata}],
        }
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                "https://api.cartesia.ai/agents/calls",
                headers={**self._headers(), "Content-Type": "application/json"},
                json=payload,
            )
            r.raise_for_status()
            return r.json()
