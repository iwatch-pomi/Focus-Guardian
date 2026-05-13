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

_CLASSIFY_QUESTION = "What is the person in this image doing? Describe briefly."

# キーワードから行動カテゴリを推定する
_KEYWORD_MAP: list[tuple[str, list[str]]] = [
    ("away",          ["empty", "no one", "nobody", "no person", "vacant", "no human", "blank", "gray", "grey", "nothing", "no activity", "no individual", "no subject"]),
    ("distracted",    ["phone", "smartphone", "social media", "youtube", "gaming", "game", "distracted", "scrolling"]),
    ("communication", ["talking", "speaking", "meeting", "call", "video call", "conversation", "zoom", "teams"]),
    ("break",         ["eating", "drinking", "coffee", "resting", "sleeping", "stretching", "relaxing", "food", "lunch"]),
    ("deep_work",     ["coding", "programming", "writing", "reading", "studying", "focused", "working", "typing", "laptop", "computer", "screen"]),
    ("shallow_work",  ["email", "browsing", "scrolling", "admin", "calendar", "spreadsheet"]),
]

_FOCUS_LEVEL_MAP: dict[str, int] = {
    "deep_work": 5, "shallow_work": 3,
    "communication": 3, "break": 2,
    "distracted": 1, "away": 1, "unknown": 3,
}


def _classify_from_text(answer: str) -> dict:
    """モデルの自然言語回答をキーワードマッチで行動カテゴリに変換する。"""
    low = answer.lower()
    for category, keywords in _KEYWORD_MAP:
        if any(k in low for k in keywords):
            focus = _FOCUS_LEVEL_MAP[category]
            return {
                "activity_category": category,
                "focus_level": focus,
                "confidence": 0.7,
                "energy_focus": focus * 20.0,
                "energy_fatigue": max(0.0, (5 - focus) * 15.0),
                "notes": answer[:60],
            }
    return {**_FALLBACK, "notes": answer[:60] if answer else "no answer"}

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
            logger.info("Moondream2 answer: %r", answer)
            data = _classify_from_text(answer)
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
            data = _classify_from_text(response.content[0].text)
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
