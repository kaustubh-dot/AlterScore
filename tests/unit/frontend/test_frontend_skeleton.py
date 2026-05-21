import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIR = REPO_ROOT / "frontend"


def test_frontend_package_json_has_expected_scripts_and_dependencies() -> None:
    package_json = json.loads((FRONTEND_DIR / "package.json").read_text())

    assert package_json["name"] == "alterscore-frontend"
    assert package_json["private"] is True
    assert {"dev", "build", "preview"}.issubset(package_json["scripts"])
    expected_dependencies = {
        "@react-three/drei",
        "@react-three/fiber",
        "@react-three/postprocessing",
        "framer-motion",
        "gsap",
        "html2canvas",
        "lenis",
        "react",
        "react-dom",
        "react-router-dom",
        "three",
    }
    expected_dev_dependencies = {"vite", "@vitejs/plugin-react"}

    assert expected_dependencies.issubset(package_json["dependencies"])
    assert expected_dev_dependencies.issubset(package_json["devDependencies"])


def test_frontend_entry_files_exist() -> None:
    expected_files = [
        FRONTEND_DIR / "index.html",
        FRONTEND_DIR / "vite.config.js",
        FRONTEND_DIR / "src" / "main.jsx",
        FRONTEND_DIR / "src" / "App.jsx",
        FRONTEND_DIR / "src" / "styles" / "index.css",
        REPO_ROOT / "README.md",
    ]

    assert all(path.is_file() for path in expected_files)
