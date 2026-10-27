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

@dataclass(frozen=True)
class DevicePreflight:
    xcode_ready: bool
    signing_ready: bool
    connected_devices: tuple[str, ...]

    @property
    def ready_for_install(self) -> bool:
        return self.xcode_ready and self.signing_ready and bool(self.connected_devices)

def preflight() -> Preflight:
    xcodebuild = shutil.which("xcodebuild"); developer_dir = None
    if xcodebuild:
        result = subprocess.run(["xcode-select", "-p"], text=True, capture_output=True)
        developer_dir = result.stdout.strip() if result.returncode == 0 else None
    result = subprocess.run(["security", "find-identity", "-v", "-p", "codesigning"], text=True, capture_output=True)
    identities = 0
    for line in result.stdout.splitlines():
        if "valid identities found" in line: identities = int(line.split()[0])
    simulator_available = shutil.which("simctl") is not None
    if not simulator_available and xcodebuild:
        simulator_available = subprocess.run(["xcrun", "--find", "simctl"], capture_output=True).returncode == 0
    return Preflight(xcodebuild, developer_dir, identities, simulator_available)

def _run(project: Path, action: str) -> None:
    if not project.exists(): raise FileNotFoundError(f"project does not exist: {project}")
    state = preflight()
    if not state.ready_for_device_build: raise RuntimeError("Xcode/signing preflight is not ready; no build was started")
    subprocess.run(["xcodebuild", "-project", str(project), "-scheme", project.stem, action], check=True)

def build(project: Path) -> None:
    _run(project, "build")

def test(project: Path) -> None:
    _run(project, "test")

def device_preflight() -> DevicePreflight:
    state = preflight()
    devices: tuple[str, ...] = ()
    if state.full_xcode_selected:
        result = subprocess.run(["xcrun", "xctrace", "list", "devices"], text=True, capture_output=True)
        if result.returncode == 0:
            devices = tuple(line.strip() for line in result.stdout.splitlines() if "iPhone" in line and "Simulator" not in line)
    return DevicePreflight(state.full_xcode_selected, bool(state.identities), devices)
