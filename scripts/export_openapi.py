"""Xuất đặc tả OpenAPI JSON từ các router và schema của ứng dụng."""

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "docs" / "openapi.json"


def main() -> None:
    """Ghi OpenAPI hiện tại vào tệp JSON có thể xem trực tiếp trên GitHub."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from business_layer.main import app

    specification = app.openapi()
    OUTPUT_PATH.write_text(
        json.dumps(specification, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Đã xuất {len(specification['paths'])} đường dẫn API: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
