"""Export the validated, merged collection for the static public site."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Noemorph'))
from backend.catalog import CatalogRepository
snapshot = CatalogRepository(ROOT / 'Noemorph/data/catalog.json')._load_if_changed()
out = Path(__file__).parent / 'dist/catalog.json'
out.write_text(json.dumps({'metadata': snapshot.metadata, 'records': snapshot.records}, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
print(f'Exported {len(snapshot.records)} records to {out}')
