from __future__ import annotations

import re
import tomllib
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "steam_workshop.toml"
TAG_PATTERN = re.compile(r"\[(/?)([a-zA-Z*][a-zA-Z0-9_]*)(?:=[^\]]*)?\]")
IMG_PATTERN = re.compile(r"\[img\](.*?)\[/img\]", re.IGNORECASE | re.DOTALL)
SELF_CLOSING_TAGS = {"*"}


def test_steam_workshop_config_loads() -> None:
    config = _load_config()
    description_path = ROOT / config["description_path"]

    assert config["max_description_bytes"] == 8000
    assert config["language"] == "english"
    assert config["format"] == "steam_bbcode"
    assert description_path.exists()
    assert description_path.is_file()
    assert description_path.is_relative_to(ROOT)
    assert config["sources"]["set_item_description"].startswith("https://partner.steamgames.com/")
    assert config["sources"]["description_limit"].startswith("https://partner.steamgames.com/")
    assert config["sources"]["formatting_help"] == (
        "https://steamcommunity.com/comment/WorkshopItem/formattinghelp"
    )
    assert "8000 bytes" in (ROOT / "steam_workshop.toml").read_text(encoding="utf-8")
    assert "BBCode-style" in config["styling"]["note"]
    assert "img" in config["styling"]["allowed_bbcode_tags"]


def test_steam_workshop_description_fits_steam_byte_limit() -> None:
    config = _load_config()
    description = _description(config)
    byte_count = len(description.encode("utf-8"))

    assert byte_count <= config["max_description_bytes"]


def test_steam_workshop_description_uses_allowed_bbcode_tags_only() -> None:
    config = _load_config()
    description = _description(config)
    allowed_tags = set(config["styling"]["allowed_bbcode_tags"])
    used_tags = {_tag_name(match) for match in TAG_PATTERN.finditer(description)}

    assert used_tags <= allowed_tags
    assert {"h1", "img", "url"} <= used_tags


def test_steam_workshop_description_has_valid_bbcode_structure() -> None:
    description = _description(_load_config())

    assert description.startswith("[h1]")
    assert "\r" not in description
    assert not _unbalanced_tags(description)


def test_steam_workshop_description_images_are_https_direct_urls() -> None:
    description = _description(_load_config())
    image_urls = [match.group(1).strip() for match in IMG_PATTERN.finditer(description)]

    assert image_urls
    for image_url in image_urls:
        parsed = urlparse(image_url)
        assert parsed.scheme == "https"
        assert parsed.netloc
        assert Path(parsed.path).suffix.lower() in {".gif", ".jpg", ".jpeg", ".png", ".webp"}


def _load_config() -> dict:
    with CONFIG_PATH.open("rb") as stream:
        return tomllib.load(stream)


def _description(config: dict) -> str:
    return (ROOT / config["description_path"]).read_text(encoding="utf-8")


def _tag_name(match: re.Match[str]) -> str:
    return match.group(2).lower()


def _unbalanced_tags(description: str) -> list[str]:
    stack: list[tuple[str, str]] = []
    errors: list[str] = []

    for match in TAG_PATTERN.finditer(description):
        closing, raw_tag = match.group(1), match.group(2)
        tag = raw_tag.lower()
        if tag in SELF_CLOSING_TAGS:
            continue
        if not closing:
            stack.append((tag, match.group(0)))
            continue
        if not stack:
            errors.append(match.group(0))
            continue
        open_tag, open_text = stack.pop()
        if open_tag != tag:
            errors.append(f"{open_text} closed by {match.group(0)}")

    errors.extend(open_text for _, open_text in stack)
    return errors
