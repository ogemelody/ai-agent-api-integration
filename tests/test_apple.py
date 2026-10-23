from apple.core import Preflight, build, test as run_tests
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
