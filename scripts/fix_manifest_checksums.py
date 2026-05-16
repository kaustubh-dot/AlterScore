import json
from pathlib import Path
from backend.ml.registry.production_manifest import compute_file_sha256

manifest_path = Path("models/registry/production_manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
repo_root = Path(".")

updated = False
for key, entry in manifest["artifacts"].items():
    disk_path = repo_root / entry["path"]
    if not disk_path.is_file():
        print(f"MISSING: {key} -> {disk_path}")
        continue
    actual = compute_file_sha256(disk_path)
    if actual != entry["sha256"]:
        print(f"STALE: {key}")
        print(f"  manifest: {entry['sha256']}")
        print(f"  actual:   {actual}")
        entry["sha256"] = actual
        updated = True
    else:
        print(f"OK: {key}")

if updated:
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("\nManifest updated with refreshed checksums.")
else:
    print("\nAll checksums match.")
