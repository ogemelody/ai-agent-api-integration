from apple.core import DevicePreflight, Preflight, build, device_preflight, test as run_tests
import pytest

def test_preflight_requires_full_xcode_and_identity():
    assert Preflight("/usr/bin/xcodebuild", "/Library/Developer/CommandLineTools", 1, True).ready_for_device_build is False
    assert Preflight("/usr/bin/xcodebuild", "/Applications/Xcode.app/Contents/Developer", 1, True).ready_for_device_build is True

def test_build_and_test_refuse_before_running_xcode(monkeypatch, tmp_path):
    project = tmp_path / "Demo.xcodeproj"; project.mkdir()
    monkeypatch.setattr("apple.core.preflight", lambda: Preflight("/usr/bin/xcodebuild", "/Library/Developer/CommandLineTools", 0, False))
    called = []
    monkeypatch.setattr("apple.core.subprocess.run", lambda *args, **kwargs: called.append((args, kwargs)))
    with pytest.raises(RuntimeError, match="preflight"): build(project)
    with pytest.raises(RuntimeError, match="preflight"): run_tests(project)
    assert called == []

def test_device_install_requires_xcode_signing_and_connected_phone():
    assert DevicePreflight(True, True, ("Alice's iPhone",)).ready_for_install is True
    assert DevicePreflight(False, True, ("Alice's iPhone",)).ready_for_install is False
    assert DevicePreflight(True, True, ()).ready_for_install is False

def test_device_preflight_stays_blocked_without_full_xcode(monkeypatch):
    monkeypatch.setattr("apple.core.preflight", lambda: Preflight("/usr/bin/xcodebuild", "/Library/Developer/CommandLineTools", 0, False))
    assert device_preflight().ready_for_install is False
