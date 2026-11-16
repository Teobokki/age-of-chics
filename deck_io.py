"""Load and render a PDF or presentation for AGE OF CHICS™ BY HYPERION.

PDF pages are rendered with a bundled PDFium library (no extra tools).
Presentation files (.pptx / .ppt) are converted to PDF first, using a
converter already on the PC when one is available. Rendered page images
are cached and rebuilt when the source file's size or modified time changes.

©2026 EX Inc./HYPERION DIGITAL ©2026
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile


RENDER_DPI = 150
OPEN_FILTER = (
    "Presentations and PDF (*.pdf *.pptx *.ppt);;"
    "PDF (*.pdf);;"
    "Presentation files (*.pptx *.ppt);;"
    "All files (*.*)"
)
PDF_EXTS = (".pdf",)
PRES_EXTS = (".pptx", ".ppt")
OPEN_EXTS = PDF_EXTS + PRES_EXTS

NEED_PDF_MSG = (
    "This presentation can't be converted on this PC. "
    "Export it to PDF and open the PDF file instead."
)


class DeckError(Exception):
    """User-facing load/render failure."""

    def __init__(self, message, need_pdf=False):
        super().__init__(message)
        self.need_pdf = need_pdf


def app_data_dir():
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        home = os.environ.get("USERPROFILE") or os.path.expanduser("~")
        local = os.path.join(home, "AppData", "Local")
    path = os.path.join(local, "AGE OF CHICS")
    os.makedirs(path, exist_ok=True)
    return path


def config_path():
    return os.path.join(app_data_dir(), "config.json")


def load_config():
    try:
        with open(config_path(), encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def save_config(data):
    path = config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def get_last_file():
    p = load_config().get("last_file") or ""
    return p if isinstance(p, str) and p.strip() else ""


def set_last_file(path):
    data = load_config()
    if path:
        data["last_file"] = os.path.abspath(path)
    else:
        data.pop("last_file", None)
    save_config(data)


def file_sig(path):
    st = os.stat(path)
    mtime = int(getattr(st, "st_mtime_ns", int(st.st_mtime * 1_000_000_000)))
    return {
        "path": os.path.abspath(path),
        "mtime_ns": mtime,
        "size": int(st.st_size),
    }


def cache_dir_for(path):
    key = hashlib.sha256(os.path.abspath(path).encode("utf-8", "replace")).hexdigest()[:24]
    d = os.path.join(app_data_dir(), "cache", key)
    os.makedirs(d, exist_ok=True)
    return d


def _clear_cache_dir(cdir):
    for name in os.listdir(cdir):
        if name.startswith("page-") or name in ("converted.pdf", "meta.json"):
            try:
                os.remove(os.path.join(cdir, name))
            except Exception:
                pass


def render_pdf_pages(pdf_path, out_dir, progress=None):
    """Render each PDF page to page-001.png, … at RENDER_DPI. Returns page paths."""
    try:
        import pypdfium2 as pdfium
    except Exception as e:
        raise DeckError("The PDF renderer is missing.\n%s" % e) from e
    try:
        pdf = pdfium.PdfDocument(pdf_path)
    except Exception as e:
        raise DeckError("Could not read this PDF.\n%s" % e) from e
    try:
        n = len(pdf)
        if n < 1:
            raise DeckError("This file has no pages.")
        paths = []
        scale = RENDER_DPI / 72.0
        os.makedirs(out_dir, exist_ok=True)
        for i in range(n):
            if progress:
                progress(i, n, "Rendering page %d of %d\u2026" % (i + 1, n))
            page = pdf[i]
            try:
                pil = page.render(scale=scale).to_pil()
                if pil.mode not in ("RGB", "L"):
                    pil = pil.convert("RGB")
                fn = os.path.join(out_dir, "page-%03d.png" % (i + 1))
                pil.save(fn, "PNG")
                paths.append(fn)
            finally:
                page.close()
        if progress:
            progress(n, n, "Done")
        return paths
    finally:
        pdf.close()


def _find_soffice():
    for name in ("soffice.exe", "soffice"):
        found = shutil.which(name)
        if found and os.path.isfile(found):
            return found
    roots = []
    for env in ("PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432"):
        val = os.environ.get(env)
        if val:
            roots.append(val)
    roots.extend([r"C:\Program Files", r"C:\Program Files (x86)"])
    seen = set()
    for root in roots:
        if not root:
            continue
        norm = os.path.normcase(os.path.abspath(root))
        if norm in seen:
            continue
        seen.add(norm)
        direct = os.path.join(root, "LibreOffice", "program", "soffice.exe")
        if os.path.isfile(direct):
            return direct
        try:
            for name in os.listdir(root):
                if name.lower().startswith("libreoffice"):
                    cand = os.path.join(root, name, "program", "soffice.exe")
                    if os.path.isfile(cand):
                        return cand
        except Exception:
            pass
    return None


def _convert_with_powerpoint(src, dest):
    """Try COM automation if a presentation app that answers this call is installed."""
    try:
        import comtypes.client
    except Exception:
        return False
    src = os.path.abspath(src)
    dest = os.path.abspath(dest)
    if os.path.isfile(dest):
        try:
            os.remove(dest)
        except Exception:
            pass
    ppt = None
    pres = None
    try:
        ppt = comtypes.client.CreateObject("PowerPoint.Application")
        try:
            ppt.DisplayAlerts = 0
        except Exception:
            pass
        try:
            ppt.Visible = 0
        except Exception:
            try:
                ppt.Visible = 1
            except Exception:
                pass
        # ReadOnly=True, Untitled=False, WithWindow=False
        pres = ppt.Presentations.Open(src, True, False, False)
        pres.SaveAs(dest, 32)  # ppSaveAsPDF
        return os.path.isfile(dest) and os.path.getsize(dest) > 0
    except Exception:
        return False
    finally:
        if pres is not None:
            try:
                pres.Close()
            except Exception:
                pass
        if ppt is not None:
            try:
                ppt.Quit()
            except Exception:
                pass


def _convert_with_soffice(src, dest):
    soffice = _find_soffice()
    if not soffice:
        return False
    src = os.path.abspath(src)
    dest = os.path.abspath(dest)
    outdir = tempfile.mkdtemp(prefix="aoc-conv-")
    try:
        cmd = [
            soffice,
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            "--norestore",
            "--convert-to",
            "pdf",
            "--outdir",
            outdir,
            src,
        ]
        flags = 0
        if sys.platform == "win32":
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        try:
            subprocess.run(
                cmd,
                timeout=180,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=flags,
            )
        except TypeError:
            subprocess.run(
                cmd,
                timeout=180,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            return False
        produced = None
        base = os.path.splitext(os.path.basename(src))[0] + ".pdf"
        cand = os.path.join(outdir, base)
        if os.path.isfile(cand):
            produced = cand
        else:
            for name in os.listdir(outdir):
                if name.lower().endswith(".pdf"):
                    produced = os.path.join(outdir, name)
                    break
        if not produced or os.path.getsize(produced) < 1:
            return False
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.isfile(dest):
            try:
                os.remove(dest)
            except Exception:
                pass
        shutil.move(produced, dest)
        return os.path.isfile(dest) and os.path.getsize(dest) > 0
    finally:
        shutil.rmtree(outdir, ignore_errors=True)


def convert_presentation_to_pdf(src, dest, progress=None):
    if progress:
        progress(0, 1, "Converting presentation\u2026")
    if _convert_with_powerpoint(src, dest):
        return dest
    if _convert_with_soffice(src, dest):
        return dest
    raise DeckError(NEED_PDF_MSG, need_pdf=True)


def load_pages(source_path, progress=None):
    """Render a user file to cached page PNGs.

    Returns (page_png_paths, pdf_path, abs_source_path).
    Reuses the cache when the source path, size, and modified time match.
    """
    source_path = os.path.abspath(source_path)
    if not os.path.isfile(source_path):
        raise DeckError("The file is no longer at:\n%s" % source_path)
    ext = os.path.splitext(source_path)[1].lower()
    if ext not in OPEN_EXTS:
        raise DeckError("Open a PDF or a presentation file (.pdf, .pptx, .ppt).")

    cdir = cache_dir_for(source_path)
    meta_path = os.path.join(cdir, "meta.json")
    sig = file_sig(source_path)

    if os.path.isfile(meta_path):
        try:
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
            pages = [os.path.join(cdir, name) for name in (meta.get("pages") or [])]
            pdf_path = meta.get("pdf_path") or ""
            if (
                meta.get("sig") == sig
                and pages
                and all(os.path.isfile(p) and os.path.getsize(p) > 0 for p in pages)
                and (ext == ".pdf" or (pdf_path and os.path.isfile(pdf_path)))
            ):
                if ext == ".pdf":
                    pdf_path = source_path
                if progress:
                    progress(len(pages), len(pages), "Loaded from cache")
                return pages, pdf_path, source_path
        except DeckError:
            raise
        except Exception:
            pass

    _clear_cache_dir(cdir)

    if ext == ".pdf":
        pdf_path = source_path
    else:
        pdf_path = os.path.join(cdir, "converted.pdf")
        convert_presentation_to_pdf(source_path, pdf_path, progress=progress)

    pages = render_pdf_pages(pdf_path, cdir, progress=progress)
    meta = {
        "sig": sig,
        "pages": [os.path.basename(p) for p in pages],
        "pdf_path": pdf_path,
        "count": len(pages),
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")
    return pages, pdf_path, source_path


def write_sample_pdf(path, titles=None):
    """Write a small visually distinct test PDF (no third-party tools)."""
    if not titles:
        titles = [
            ("EXTERNAL TEST DECK", "Opened from your PC"),
            ("PAGE TWO", "Edits to this file show up after Reload"),
            ("PAGE THREE", "Remembered on the next launch"),
        ]
    width, height = 960, 540
    colors = [
        (0.07, 0.12, 0.28),
        (0.22, 0.05, 0.08),
        (0.05, 0.20, 0.12),
    ]

    def esc(s):
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    content_objs = []
    for i, (title, sub) in enumerate(titles):
        r, g, b = colors[i % len(colors)]
        stream = (
            "q %.3f %.3f %.3f rg 0 0 %d %d re f Q\n"
            "BT /F1 36 Tf 1 1 1 rg 70 330 Td (%s) Tj ET\n"
            "BT /F1 18 Tf 0.85 0.85 0.80 rg 70 280 Td (%s) Tj ET\n"
            "BT /F1 14 Tf 0.80 0.70 0.20 rg 70 80 Td (Page %d of %d) Tj ET\n"
            % (r, g, b, width, height, esc(title), esc(sub), i + 1, len(titles))
        ).encode("ascii")
        content_objs.append(stream)

    n = len(titles)
    # Object IDs: 1 catalog, 2 pages, 3 font, 4..(3+n) pages, (4+n)..(3+2n) contents
    font_id = 3
    page_ids = list(range(4, 4 + n))
    content_ids = list(range(4 + n, 4 + 2 * n))
    kids = " ".join("%d 0 R" % i for i in page_ids)
    chunks = []

    def add(obj_id, body):
        chunks.append("%d 0 obj\n%s\nendobj\n" % (obj_id, body))

    add(1, "<< /Type /Catalog /Pages 2 0 R >>")
    add(2, "<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, n))
    add(font_id, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    for pid, cid in zip(page_ids, content_ids):
        add(
            pid,
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %d %d] "
            "/Contents %d 0 R /Resources << /Font << /F1 %d 0 R >> >> >>"
            % (width, height, cid, font_id),
        )
    for cid, stream in zip(content_ids, content_objs):
        add(cid, "<< /Length %d >>\nstream\n" % len(stream) + stream.decode("ascii") + "\nendstream")

    body = "%PDF-1.4\n" + "".join(chunks)
    # xref
    # Rebuild with exact offsets
    parts = ["%PDF-1.4\n"]
    offsets = [0]
    bodies = []
    # Recreate objects in order 1..max
    objects = {
        1: "<< /Type /Catalog /Pages 2 0 R >>",
        2: "<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, n),
        3: "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
    }
    for pid, cid in zip(page_ids, content_ids):
        objects[pid] = (
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %d %d] "
            "/Contents %d 0 R /Resources << /Font << /F1 %d 0 R >> >> >>"
            % (width, height, cid, font_id)
        )
    for cid, stream in zip(content_ids, content_objs):
        objects[cid] = "<< /Length %d >>\nstream\n%s\nendstream" % (
            len(stream),
            stream.decode("ascii"),
        )
    max_id = max(objects)
    out = bytearray(b"%PDF-1.4\n")
    offs = [0]
    for i in range(1, max_id + 1):
        offs.append(len(out))
        block = "%d 0 obj\n%s\nendobj\n" % (i, objects[i])
        out.extend(block.encode("ascii"))
    xref_start = len(out)
    xref = "xref\n0 %d\n0000000000 65535 f \n" % (max_id + 1)
    for off in offs[1:]:
        xref += "%010d 00000 n \n" % off
    out.extend(xref.encode("ascii"))
    trailer = "trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        max_id + 1,
        xref_start,
    )
    out.extend(trailer.encode("ascii"))
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(out)
    return path
