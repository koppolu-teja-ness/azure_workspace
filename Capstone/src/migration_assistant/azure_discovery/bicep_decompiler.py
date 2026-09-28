"""Optional ARM-to-Bicep decompile helper using Azure CLI."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


def decompile_arm_template_json(template: dict, *, output_path: str) -> str | None:
    """Write ARM JSON and run `az bicep decompile`.

    Returns output path when successful, else None.
    """
    if shutil.which("az") is None:
        return None

    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory(prefix="migration-bicep-decompile-") as temp_dir:
        json_path = Path(temp_dir) / "template.json"
        json_path.write_text(json.dumps(template, indent=2), encoding="utf-8")

        completed = subprocess.run(
            [
                "az",
                "bicep",
                "decompile",
                "--file",
                str(json_path),
                "--outfile",
                str(output),
                "--only-show-errors",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0 or not output.is_file():
            return None
        return str(output)
