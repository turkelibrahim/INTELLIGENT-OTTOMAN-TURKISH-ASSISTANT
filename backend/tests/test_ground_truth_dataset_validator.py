import importlib.util
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "validate_ground_truth_dataset.py"
SPEC = importlib.util.spec_from_file_location("ground_truth_validator", SCRIPT_PATH)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


METADATA_HEADER = (
    "page_id,source_document,title,approximate_year,page_number,print_or_handwriting,"
    "typography,image_quality,degradation_type,dpi,rights_or_ownership,annotator,reviewer,notes\n"
)


def make_input_root(tmp_path: Path) -> Path:
    input_root = tmp_path / "input"
    (input_root / "images").mkdir(parents=True)
    (input_root / "transcriptions").mkdir()
    (input_root / "metadata.csv").write_text(METADATA_HEADER, encoding="utf-8")
    return input_root


def write_png(path: Path, size=(1200, 1200), color=(255, 255, 255)) -> None:
    Image.new("RGB", size, color).save(path, dpi=(300, 300))


def add_metadata_row(input_root: Path, page_id: str, source="doc-a", split: str | None = None) -> None:
    header = METADATA_HEADER.strip()
    row = f"{page_id},{source},Title,1900,1,print,nesih,good,none,300,user-owned,annotator,reviewer,notes\n"
    if split is not None:
        header = header + ",split"
        row = row.strip() + f",{split}\n"
    (input_root / "metadata.csv").write_text(header + "\n" + row, encoding="utf-8")


def test_no_data_is_blocked_and_not_failed(tmp_path):
    input_root = make_input_root(tmp_path)

    result = validator.validate_dataset(input_root)

    assert result.status == "BLOCKED_USER_DATA_REQUIRED"
    assert result.errors == []
    assert result.manifest["page_count"] == 0


def test_valid_matching_pair_passes(tmp_path):
    input_root = make_input_root(tmp_path)
    write_png(input_root / "images" / "page_001.png")
    (input_root / "transcriptions" / "page_001.gt.txt").write_text(
        "\u062f\u0648\u0644\u062a \u0639\u0644\u064a\u0647 \u0639\u062b\u0645\u0627\u0646\u064a\u0647\n",
        encoding="utf-8",
    )
    add_metadata_row(input_root, "page_001")

    result = validator.validate_dataset(input_root)

    assert result.status == "PASS"
    assert result.manifest["page_count"] == 1
    assert result.manifest["verified_line_count"] == 1


def test_unmatched_files_fail(tmp_path):
    input_root = make_input_root(tmp_path)
    (input_root / "transcriptions" / "page_999.gt.txt").write_text("\u0627\u0644\u0641\n", encoding="utf-8")

    result = validator.validate_dataset(input_root)

    assert result.status == "FAIL"
    assert any(issue.code == "IMAGE_MISSING" for issue in result.errors)


def test_invalid_utf8_transcription_fails(tmp_path):
    input_root = make_input_root(tmp_path)
    write_png(input_root / "images" / "page_001.png")
    (input_root / "transcriptions" / "page_001.gt.txt").write_bytes(b"\xff\xfe\x00")
    add_metadata_row(input_root, "page_001")

    result = validator.validate_dataset(input_root)

    assert result.status == "FAIL"
    assert any(issue.code == "TRANSCRIPTION_ENCODING" for issue in result.errors)


def test_low_resolution_warns(tmp_path):
    input_root = make_input_root(tmp_path)
    write_png(input_root / "images" / "page_001.png", size=(600, 800))
    (input_root / "transcriptions" / "page_001.gt.txt").write_text("\u0627\u0644\u0641\n", encoding="utf-8")
    add_metadata_row(input_root, "page_001")

    result = validator.validate_dataset(input_root)

    assert result.status == "PASS"
    assert any(issue.code == "LOW_RESOLUTION_DIMENSIONS" for issue in result.warnings)


def test_duplicate_image_hash_fails(tmp_path):
    input_root = make_input_root(tmp_path)
    write_png(input_root / "images" / "page_001.png")
    write_png(input_root / "images" / "page_002.png")
    (input_root / "transcriptions" / "page_001.gt.txt").write_text("\u0627\u0644\u0641\n", encoding="utf-8")
    (input_root / "transcriptions" / "page_002.gt.txt").write_text("\u0628\u0627\n", encoding="utf-8")
    (input_root / "metadata.csv").write_text(
        METADATA_HEADER
        + "page_001,doc-a,Title,1900,1,print,nesih,good,none,300,user-owned,a,r,\n"
        + "page_002,doc-b,Title,1900,2,print,nesih,good,none,300,user-owned,a,r,\n",
        encoding="utf-8",
    )

    result = validator.validate_dataset(input_root)

    assert result.status == "FAIL"
    assert any(issue.code == "DUPLICATE_IMAGE" for issue in result.errors)


def test_split_leakage_fails_when_duplicate_hash_crosses_splits(tmp_path):
    input_root = make_input_root(tmp_path)
    write_png(input_root / "images" / "page_001.png")
    write_png(input_root / "images" / "page_002.png")
    (input_root / "transcriptions" / "page_001.gt.txt").write_text("\u0627\u0644\u0641\n", encoding="utf-8")
    (input_root / "transcriptions" / "page_002.gt.txt").write_text("\u0628\u0627\n", encoding="utf-8")
    header = METADATA_HEADER.strip() + ",split\n"
    (input_root / "metadata.csv").write_text(
        header
        + "page_001,doc-a,Title,1900,1,print,nesih,good,none,300,user-owned,a,r,,dev\n"
        + "page_002,doc-a,Title,1900,2,print,nesih,good,none,300,user-owned,a,r,,test\n",
        encoding="utf-8",
    )

    result = validator.validate_dataset(input_root)

    assert result.status == "FAIL"
    assert any(issue.code == "SPLIT_LEAKAGE" for issue in result.errors)


def test_assisted_annotation_draft_blocks_final_quality_metrics(tmp_path):
    input_root = make_input_root(tmp_path)
    write_png(input_root / "images" / "page_001.png")
    (input_root / "transcriptions" / "page_001.gt.txt").write_text("\u0627\u0644\u0641\n", encoding="utf-8")
    header = METADATA_HEADER.strip() + ",annotation_status,human_verified\n"
    (input_root / "metadata.csv").write_text(
        header
        + "page_001,doc-a,Title,1900,1,print,nesih,good,none,300,user-owned,a,PENDING_HUMAN_REVIEW,,ASSISTED_ANNOTATION_DRAFT,false\n",
        encoding="utf-8",
    )

    result = validator.validate_dataset(input_root)

    assert result.status == "BLOCKED_HUMAN_REVIEW_REQUIRED"
    assert any(issue.code == "HUMAN_REVIEW_REQUIRED" for issue in result.warnings)
