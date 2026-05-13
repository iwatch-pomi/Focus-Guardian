"""Activity classifiers.

- LocalActivityClassifier: Moondream2 (HuggingFace) による完全ローカル推論（デフォルト）
  transformers + torch を使用。初回はモデル (~4GB) を自動ダウンロード。
  以降はオフラインで動作。
- ActivityClassifier: Claude Vision API（APIキーがある場合のフォールバック）
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

from ..api.config import settings
from ..sensing.snapshot import ActivityReading

if TYPE_CHECKING:
    from PIL.Image import Image

logger = logging.getLogger(__name__)

_CLASSIFY_QUESTION = (
    "Look at this image and classify the person's activity. "
    "Return ONLY a JSON object with these exact fields: "
    '{"activity_category": one of ["deep_work","shallow_work","communication","break","distracted","away","unknown"], '
    '"focus_level": integer 1-5, '
    '"confidence": float 0.0-1.0, '
    '"energy_focus": float 0.0-100.0, '
    '"energy_fatigue": float 0.0-100.0, '
    '"notes": string max 60 chars}. '
    "deep_work=focused on screen/reading, shallow_work=email/admin, "
    "communication=call/meeting, break=resting/eating, "
    "distracted=phone/social media, away=empty desk."
)

_FALLBACK = {
    "activity_category": "unknown",
    "focus_level": 3,
    "confidence": 0.0,
    "energy_focus": 50.0,
    "energy_fatigue": 50.0,
    "notes": "classification unavailable",
}


def _parse(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    start, end = raw.find("{"), raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]
    return json.loads(raw)


def _to_reading(data: dict) -> ActivityReading:
    return ActivityReading(
        activity_category=data.get("activity_category", "unknown"),
        focus_level=int(data.get("focus_level", 3)),
        confidence=float(data.get("confidence", 0.0)),
        energy_focus=float(data.get("energy_focus", 50.0)),
        energy_fatigue=float(data.get("energy_fatigue", 50.0)),
        notes=data.get("notes", ""),
    )


class LocalActivityClassifier:
    """Moondream2 (vikhyatk/moondream2) によるオンデバイス推論。

    transformers + torch を使用。インターネット・APIキー不要。
    初回のみ HuggingFace からモデルをダウンロードしてローカルキャッシュ。
    """

    _model = None
    _tokenizer = None

    def _load(self) -> None:
        if LocalActivityClassifier._model is not None:
            return
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError:
            raise RuntimeError(
                "transformers がインストールされていません。\n"
                "次のコマンドでインストールしてください:\n"
                "  backend\\.venv\\Scripts\\pip install transformers"
            )
        logger.info("Moondream2 モデルをロード中 (初回は数分かかります)...")
        model_id = "vikhyatk/moondream2"
        revision = "2024-08-26"
        LocalActivityClassifier._model = AutoModelForCausalLM.from_pretrained(
            model_id, trust_remote_code=True, revision=revision
        )
        LocalActivityClassifier._tokenizer = AutoTokenizer.from_pretrained(
            model_id, revision=revision
        )
        logger.info("Moondream2 ロード完了")

    async def classify(self, image: "Image") -> ActivityReading:
        await asyncio.to_thread(self._load)
        try:
            enc = LocalActivityClassifier._model.encode_image(image)
            answer = LocalActivityClassifier._model.answer_question(
                enc, _CLASSIFY_QUESTION, LocalActivityClassifier._tokenizer
            )
            data = _parse(answer)
        except Exception as exc:
            logger.warning("LocalClassifier failed (%s), using fallback", exc)
            data = _FALLBACK
        return _to_reading(data)


class ActivityClassifier:
    """Claude Vision API を使ったクラウド推論（APIキーが必要）。"""

    def __init__(self) -> None:
        import anthropic
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def classify(self, image: "Image") -> ActivityReading:
        from ..privacy.processor import encode_for_api

        b64 = encode_for_api(image)
        try:
            response = await self._client.messages.create(
                model="claude-opus-4-7",
                max_tokens=256,
                system=[{"type": "text", "text": _CLASSIFY_QUESTION,
                          "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {
                        "type": "base64", "media_type": "image/jpeg", "data": b64}},
                    {"type": "text", "text": "Classify this snapshot."},
                ]}],
            )
            data = _parse(response.content[0].text)
        except Exception as exc:
            logger.warning("CloudClassifier failed (%s), using fallback", exc)
            data = _FALLBACK
        return _to_reading(data)


def get_classifier():
    if settings.use_local_model:
        logger.info("分類モード: ローカル (Moondream2)")
        return LocalActivityClassifier()
    if not settings.anthropic_api_key:
        logger.warning("APIキー未設定のためローカルモードにフォールバック")
        return LocalActivityClassifier()
    logger.info("分類モード: Claude Vision API")
    return ActivityClassifier()
