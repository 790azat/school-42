"""Download every Google Drive / Docs / OneDrive file the site links to.

Runs in GitHub Actions (the runner has open internet). Writes the files to
mirror-out/<key>/ and a manifest.json describing what happened per link.
"""
import json, os, re, sys, time, traceback, urllib.request
import gdown

OUT = "mirror-out"
UA = {"User-Agent": "Mozilla/5.0"}


def fetch(url, dest_dir, name, want=None):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        ctype = r.headers.get("Content-Type", "")
        data = r.read()
    if want and want not in ctype:
        raise RuntimeError(f"unexpected content-type {ctype!r} ({len(data)} bytes)")
    os.makedirs(dest_dir, exist_ok=True)
    path = os.path.join(dest_dir, name)
    with open(path, "wb") as f:
        f.write(data)
    return path


def listing(d):
    out = []
    for root, _, files in os.walk(d):
        for f in sorted(files):
            p = os.path.join(root, f)
            out.append({"path": os.path.relpath(p, OUT), "bytes": os.path.getsize(p)})
    return out


def direct(key, d):
    """Plain usercontent download, used when gdown's page scraping is throttled."""
    url = f"https://drive.usercontent.google.com/download?id={key}&export=download&confirm=t"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=180) as r:
        cd = r.headers.get("Content-Disposition", "")
        ctype = r.headers.get("Content-Type", "")
        data = r.read()
    if "text/html" in ctype:
        raise RuntimeError("got an HTML page instead of the file")
    m = re.search(r"filename\*=UTF-8''([^;]+)", cd) or re.search(r'filename="([^"]+)"', cd)
    name = urllib.request.unquote(m.group(1)) if m else f"{key}.bin"
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, os.path.basename(name)), "wb") as f:
        f.write(data)
    return True


def main():
    links = [l.strip() for l in open(sys.argv[1]) if l.strip()]
    chunk, of = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, 1)
    links = links[chunk::of]  # each CI job (own IP) takes a slice, so Google does not throttle
    old = {}
    mpath = os.environ.get("OLD_MANIFEST", os.path.join(OUT, "manifest.json"))
    if os.path.exists(mpath):
        old = {e["url"]: e for e in json.load(open(mpath))}
    manifest = []
    for url in links:
        if old.get(url, {}).get("ok"):
            manifest.append(old[url]); continue
        time.sleep(2)
        entry = {"url": url}
        try:
            if m := re.search(r"/folders/([\w-]+)", url):
                key = m.group(1); entry.update(kind="folder", key=key)
                d = os.path.join(OUT, key)
                files = gdown.download_folder(id=key, output=d, quiet=True, remaining_ok=True,
                                              use_cookies=False, skip_download=True)
                for f in files:
                    rel = os.path.relpath(f.local_path, d)
                    target = os.path.join(d, os.path.dirname(rel))
                    for attempt in range(2):
                        try:
                            direct(f.id, target)
                            entry.get("file_errors", {}).pop(f.path, None); break
                        except Exception as e:
                            entry.setdefault("file_errors", {})[f.path] = str(e)[:200]
                            time.sleep(10)
                    time.sleep(1)
            elif m := re.search(r"/presentation/d/e/([\w-]+)", url):
                key = m.group(1); entry.update(kind="published-slides", key=key)
                d = os.path.join(OUT, key); err = []
                for cand in (f"https://docs.google.com/presentation/d/e/{key}/pub?output=pdf",
                             f"https://docs.google.com/presentation/d/e/{key}/export/pdf",
                             f"https://docs.google.com/presentation/d/e/{key}/pub?output=pptx"):
                    try:
                        want = "pdf" if "pdf" in cand else "presentation"
                        fetch(cand, d, "slides." + ("pdf" if want == "pdf" else "pptx"), want); break
                    except Exception as e:
                        err.append(f"{cand}: {e}")
                else:
                    raise RuntimeError("; ".join(err))
            elif m := re.search(r"(?:/file/d/|/spreadsheets/d/|/document/d/)([\w-]+)", url):
                key = m.group(1); entry.update(kind="file", key=key)
                d = os.path.join(OUT, key) + "/"
                os.makedirs(d, exist_ok=True)
                ok = None
                for attempt in range(2):
                    try:
                        ok = direct(key, d); break
                    except Exception as e:
                        entry["direct_error"] = str(e)[:300]; time.sleep(10)
                if not ok:
                    # native Google Sheets/Docs: export instead
                    kind = "spreadsheets" if "spreadsheets" in url else "document"
                    fetch(f"https://docs.google.com/{kind}/d/{key}/export?format=pdf", d, "export.pdf", "pdf")
            elif "onedrive.live.com" in url:
                resid = re.search(r"resid=([^&]+)", url).group(1)
                key = "onedrive-" + re.sub(r"[^\w]", "_", urllib.request.unquote(resid)); entry.update(kind="onedrive", key=key)
                fetch(url.replace("/embed?", "/download?"), os.path.join(OUT, key), "file.bin")
            else:
                entry.update(kind="unknown"); raise RuntimeError("unrecognised link")
            entry["files"] = listing(os.path.join(OUT, entry["key"]))
            entry["ok"] = bool(entry["files"])
        except Exception as e:
            entry["ok"] = False
            entry["error"] = f"{type(e).__name__}: {e}"[:600]
            traceback.print_exc()
        if entry.get("file_errors"):
            entry["ok"] = False
        if not entry.get("ok"):
            msg = (entry.get("error") or json.dumps(entry.get("file_errors"), ensure_ascii=False))[:300]
            print(f"::warning title=mirror fail {entry.get('key', '')[:30]}::{msg}")
        print(("OK  " if entry.get("ok") else "FAIL"), url, file=sys.stderr)
        manifest.append(entry)
    os.makedirs(OUT, exist_ok=True)
    name = "manifest.json" if of == 1 else f"manifest-{chunk}.json"
    json.dump(manifest, open(os.path.join(OUT, name), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
