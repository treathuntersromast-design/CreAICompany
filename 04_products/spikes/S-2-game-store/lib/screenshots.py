"""スクリーンショット読み込みユーティリティ。

実 PNG を扱う場合は base64 化して Claude Vision に渡せる形式を作る。
重量回避のため、MVP では `descriptions.json`（各スクショの説明テキスト）から
読み込むパスも提供する。
"""

from __future__ import annotations

import base64
import json
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Screenshot:
    """スクリーンショット 1 枚分のメタデータ。"""

    screenshot_id: str
    description: str
    file_path: Optional[Path] = None
    media_type: Optional[str] = None
    base64_data: Optional[str] = None

    def has_image(self) -> bool:
        return self.base64_data is not None

    def to_text_summary(self) -> str:
        return f"[{self.screenshot_id}] {self.description}"

    def to_vision_block(self) -> dict:
        """Anthropic Messages API の image block を返す。"""
        if not self.has_image():
            raise ValueError(
                f"Screenshot {self.screenshot_id} has no image data; "
                "cannot convert to vision block."
            )
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": self.media_type,
                "data": self.base64_data,
            },
        }


def load_from_descriptions_json(path: Path) -> list[Screenshot]:
    """descriptions.json から Screenshot のリストを読み込む。

    フォーマット:
        {"screenshots": [{"id": "dummy_001", "description": "..."}, ...]}
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("screenshots", [])
    return [
        Screenshot(screenshot_id=item["id"], description=item["description"])
        for item in items
    ]


def load_from_directory(directory: Path) -> list[Screenshot]:
    """ディレクトリ内の画像ファイルを Screenshot として読み込む。

    Vision に渡すため base64 化する。説明は空文字列。
    """
    screenshots: list[Screenshot] = []
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    for file_path in sorted(directory.iterdir()):
        if file_path.suffix.lower() not in exts:
            continue
        media_type, _ = mimetypes.guess_type(file_path.name)
        if media_type is None:
            media_type = "image/png"
        data = base64.standard_b64encode(file_path.read_bytes()).decode("utf-8")
        screenshots.append(
            Screenshot(
                screenshot_id=file_path.stem,
                description="",
                file_path=file_path,
                media_type=media_type,
                base64_data=data,
            )
        )
    return screenshots


def load_screenshots(source: Path) -> list[Screenshot]:
    """source が JSON ならテキスト記述から、ディレクトリなら画像から読み込む。"""
    if source.is_file() and source.suffix == ".json":
        return load_from_descriptions_json(source)
    if source.is_dir():
        # descriptions.json が同居していれば優先
        desc_file = source / "dummy_descriptions.json"
        if desc_file.exists():
            return load_from_descriptions_json(desc_file)
        return load_from_directory(source)
    raise FileNotFoundError(f"Screenshot source not found: {source}")
