from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.import_vital_animations_media import (
    build_mp4_index,
    extract_zip_safely,
    find_mp4,
    iter_metadata_records,
    load_mapping,
    normalize_name,
)


def test_normalize_name_matches_display_variants() -> None:
    assert normalize_name("Rear Delt Fly (Reverse Pec Deck)") == "rear delt fly reverse pec deck"


def test_metadata_reader_and_nearby_mp4_selection(tmp_path: Path) -> None:
    package = tmp_path / "Free50"
    media = package / "Free50"
    media.mkdir(parents=True)
    metadata = package / "exercises.json"
    metadata.write_text('[{"id":"0054","name":"barbell back squat"}]', encoding="utf-8")
    nearby = media / "0054.mp4"
    duplicate = tmp_path / "samples" / "0054.mp4"
    duplicate.parent.mkdir()
    nearby.touch()
    duplicate.touch()

    records = list(iter_metadata_records(tmp_path))
    index = build_mp4_index(tmp_path)

    assert records[0][1]["id"] == "0054"
    assert find_mp4(metadata, "0054", index) == nearby


def test_mapping_requires_string_object(tmp_path: Path) -> None:
    valid = tmp_path / "valid.json"
    valid.write_text('{"0054":"Barbell Back Squat"}', encoding="utf-8")
    invalid = tmp_path / "invalid.json"
    invalid.write_text('["Barbell Back Squat"]', encoding="utf-8")

    assert load_mapping(valid) == {"0054": "Barbell Back Squat"}
    with pytest.raises(SystemExit, match="JSON object"):
        load_mapping(invalid)


def test_zip_extraction_rejects_path_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.zip"
    destination = tmp_path / "destination"
    destination.mkdir()
    with ZipFile(archive, "w") as package:
        package.writestr("../outside.txt", "unsafe")

    with pytest.raises(SystemExit, match="Unsafe archive entry"):
        extract_zip_safely(archive, destination)

    assert not (tmp_path / "outside.txt").exists()
