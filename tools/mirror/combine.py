"""Merge the per-job manifests into mirror-out/manifest.json (previous OK entries win)."""
import glob, json, os, sys
out = sys.argv[1]
old = {}
p = os.path.join(out, "manifest.json")
if os.path.exists(p):
    old = {e["url"]: e for e in json.load(open(p))}
for f in sorted(glob.glob(os.path.join(out, "manifest-*.json"))):
    for e in json.load(open(f)):
        if not old.get(e["url"], {}).get("ok"):
            old[e["url"]] = e
    os.remove(f)
json.dump(list(old.values()), open(p, "w"), ensure_ascii=False, indent=1)
print(sum(e.get("ok", False) for e in old.values()), "ok of", len(old))
