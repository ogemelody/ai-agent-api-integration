from __future__ import annotations
import shutil, subprocess
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Preflight:
    xcodebuild: str | None; developer_dir: str | None; identities: int; simulator_available: bool
    @property
    def full_xcode_selected(self) -> bool:
        return bool(self.developer_dir and self.developer_dir.endswith("/Contents/Developer"))

    @property
    def ready_for_device_build(self) -> bool:
        return bool(self.xcodebuild and self.full_xcode_selected and self.identities)

def preflight() -> Preflight:
    xcodebuild = shutil.which("xcodebuild"); developer_dir = None
    if xcodebuild:
        result = subprocess.run(["xcode-select", "-p"], text=True, capture_output=True)
        developer_dir = result.stdout.strip() if result.returncode == 0 else None
    result = subprocess.run(["security", "find-identity", "-v", "-p", "codesigning"], text=True, capture_output=True)
    identities = 0
    for line in result.stdout.splitlines():
        if "valid identities found" in line: identities = int(line.split()[0])
    return Preflight(xcodebuild, developer_dir, identities, shutil.which("simctl") is not None)

def build(project: Path) -> None:
    state = preflight()
    if not state.ready_for_device_build: raise RuntimeError("Xcode/signing preflight is not ready; no build was started")
    subprocess.run(["xcodebuild", "-project", str(project), "-scheme", project.stem, "build"], check=True)
