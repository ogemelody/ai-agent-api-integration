from generator.core import generate

def test_generator_creates_swiftui_sources(tmp_path):
    files = generate("DemoApp", tmp_path)
    assert {p.name for p in files} == {"DemoAppApp.swift", "ContentView.swift", "README.md", "project.yml"}
    assert "@main" in (tmp_path / "DemoApp" / "DemoAppApp.swift").read_text()
    project = (tmp_path / "DemoApp" / "project.yml").read_text()
    assert "PRODUCT_BUNDLE_IDENTIFIER: com.imessageagent.DemoApp" in project
