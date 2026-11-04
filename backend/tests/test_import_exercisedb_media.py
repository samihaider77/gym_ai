from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.import_exercisedb_media import (
    build_asset_index,
    extract_zip_safely,
    find_best_gif,
    iter_metadata_records,
    normalize_name,
)


def test_normalize_name_matches_display_variants() -> None:
    assert normalize_name("  Barbell Bench-Press ") == "barbell bench press"
    assert normalize_name("45° Side Bend") == "45 side bend"


def test_find_best_gif_prefers_exact_then_nearest_resolution(tmp_path: Path) -> None:
    metadata = tmp_path / "0025.json"
    metadata.write_text('{"id":"0025","name":"barbell bench press"}', encoding="utf-8")
    gif_360 = tmp_path / "0025-360.gif"
    gif_1080 = tmp_path / "0025-1080.gif"
    gif_360.touch()
    gif_1080.touch()
    index = build_asset_index(tmp_path)

    assert find_best_gif(metadata, "0025", 360, index) == gif_360
    assert find_best_gif(metadata, "0025", 720, index) == gif_1080


def test_metadata_reader_supports_json_object_arrays(tmp_path: Path) -> None:
    metadata = tmp_path / "exercises.json"
    metadata.write_text(
        '[{"id":"0025","name":"barbell bench press"},'
        '{"id":"0001","name":"3/4 sit-up"}]',
        encoding="utf-8",
    )

    records = list(iter_metadata_records([metadata]))

    assert [record[1]["id"] for record in records] == ["0025", "0001"]
    assert all(record[2] is None for record in records)


def test_zip_extraction_rejects_path_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.zip"
    destination = tmp_path / "destination"
    destination.mkdir()
    with ZipFile(archive, "w") as package:
        package.writestr("../outside.txt", "unsafe")

    with pytest.raises(SystemExit, match="Unsafe archive entry"):
        extract_zip_safely(archive, destination)

    assert not (tmp_path / "outside.txt").exists()
