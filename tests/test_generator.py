from generator.core import generate

def test_generator_creates_swiftui_sources(tmp_path):
    files = generate("DemoApp", tmp_path)
    assert {p.name for p in files} == {"DemoAppApp.swift", "ContentView.swift", "README.md"}
    assert "@main" in (tmp_path / "DemoApp" / "DemoAppApp.swift").read_text()
