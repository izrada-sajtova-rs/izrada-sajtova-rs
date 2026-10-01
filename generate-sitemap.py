"""
Regenerise sitemap.xml sa stvarnim datumom poslednje izmene svake stranice
(uzetim iz fajl-sistema, umesto fiksnog/ručno unetog datuma).

Svaka stranica je navedena kao par srpska/engleska verzija, pa sitemap za
obe verzije sadrži i hreflang veze (sr, en, x-default), kako Google preporučuje
za višejezične sajtove.

Pokreni pre svakog objavljivanja sajta:
    python generate-sitemap.py
"""
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE_URL = "https://izrada-sajtova-rs.com"

# (srpska putanja, engleska putanja, prioritet)
PAGES = [
    ("/", "/en/", "1.00"),
    ("/radovi/", "/en/our-work/", "0.95"),
    ("/izrada-sajtova-cene/", "/en/web-design-pricing/", "0.90"),
    ("/izrada-sajtova/", "/en/web-development/", "0.90"),
    ("/kontakt/", "/en/contact/", "0.90"),
    ("/o-nama/", "/en/about-us/", "0.85"),
    ("/izrada-online-prodavnica/", "/en/e-commerce/", "0.80"),
    ("/redizajn-sajtova/", "/en/website-redesign/", "0.80"),
    ("/izrada-animacija/", "/en/web-animation/", "0.80"),
    ("/graficki-dizajn/", "/en/graphic-design/", "0.80"),
    ("/google-marketing/", "/en/google-ads/", "0.80"),
    ("/projekti/izrada-sajtova-katarina-ketering/", "/en/case-study/katarina-ketering-website/", "0.80"),
    ("/projekti/izrada-sajtova-exporealestate/", "/en/case-study/expo-real-estate-website/", "0.80"),
    ("/projekti/izrada-sajtova-lavandabeograd/", "/en/case-study/lavanda-beograd-website/", "0.80"),
    ("/projekti/izrada-sajtova-alfa-tim/", "/en/case-study/alfa-tim-website/", "0.80"),
    ("/projekti/izrada-sajtova-bazicolab/", "/en/case-study/bazicolab-website/", "0.80"),
    ("/projekti/izrada-sajtova-tukodi/", "/en/case-study/nekretnine-tukodi-website/", "0.80"),
    ("/projekti/izrada-sajtova-domaca-hrana/", "/en/case-study/domaca-hrana-website/", "0.80"),
    ("/projekti/izrada-sajtova-rsketering/", "/en/case-study/rs-ketering-website/", "0.80"),
    ("/projekti/izrada-sajtova-test-licnosti/", "/en/case-study/test-licnosti-website/", "0.80"),
    ("/saveti/", "/en/blog/", "0.70"),
    ("/saveti/da-li-vam-je-potreban-google-ads/", "/en/blog/do-you-need-google-ads/", "0.60"),
    ("/saveti/elementi-koji-grade-poverenje-na-sajtu/", "/en/blog/elements-that-build-website-trust/", "0.60"),
    ("/saveti/kako-izabrati-domen-i-hosting/", "/en/blog/how-to-choose-domain-and-hosting/", "0.60"),
    ("/saveti/kako-ubrzati-ucitavanje-sajta/", "/en/blog/how-to-speed-up-your-website/", "0.60"),
    ("/saveti/seo-osnove-za-male-biznise/", "/en/blog/seo-basics-for-small-businesses/", "0.60"),
    ("/saveti/kako-izmeriti-uspeh-sajta-analytics/", "/en/blog/measure-website-success-with-analytics/", "0.60"),
    ("/saveti/kako-pripremiti-sadrzaj-za-sajt/", "/en/blog/how-to-prepare-website-content/", "0.60"),
    ("/saveti/zasto-custom-sajt-umesto-wordpressa/", "/en/blog/custom-website-vs-wordpress/", "0.60"),
    ("/saveti/znaci-da-vam-je-potreban-redizajn-sajta/", "/en/blog/signs-you-need-a-website-redesign/", "0.60"),
    ("/politika-privatnosti/", "/en/privacy-policy/", "0.30"),
    ("/uslovi-koriscenja/", "/en/terms-of-use/", "0.30"),
]


def file_for(url_path: str) -> Path:
    return ROOT / url_path.strip("/") / "index.html"


def lastmod_for(file_path: Path) -> str:
    mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
    return mtime.strftime("%Y-%m-%dT%H:%M:%S+00:00")


def check_page(url_path: str) -> None:
    """Upozori ako canonical stranice ne odgovara adresi u sitemap-u ili je stranica noindex."""
    html = file_for(url_path).read_text(encoding="utf-8-sig")
    canonical = re.search(r'<link rel="canonical" href="([^"]*)"', html)
    if not canonical or canonical.group(1) != BASE_URL + url_path:
        found = canonical.group(1) if canonical else "nema"
        print(f"  UPOZORENJE: canonical za {url_path} je {found}")
    if re.search(r'<meta name="robots" content="[^"]*noindex', html):
        print(f"  UPOZORENJE: {url_path} ima noindex")


def url_entry(loc: str, sr: str, en: str, priority: str) -> str:
    return (
        "<url>\n"
        f"  <loc>{BASE_URL}{loc}</loc>\n"
        f'  <xhtml:link rel="alternate" hreflang="sr" href="{BASE_URL}{sr}"/>\n'
        f'  <xhtml:link rel="alternate" hreflang="en" href="{BASE_URL}{en}"/>\n'
        f'  <xhtml:link rel="alternate" hreflang="x-default" href="{BASE_URL}{sr}"/>\n'
        f"  <lastmod>{lastmod_for(file_for(loc))}</lastmod>\n"
        f"  <priority>{priority}</priority>\n"
        "</url>"
    )


def unlisted_pages() -> list:
    """Stranice koje postoje na disku, a nisu u PAGES (da se ne zaborave nove)."""
    listed = {file_for(p).resolve() for pair in PAGES for p in pair[:2]}
    skip = {"media", "css", "fonts", "images", "logo", "mp3", "SVG", "video", ".claude"}
    found = []
    for f in ROOT.rglob("index.html"):
        rel = f.relative_to(ROOT)
        if rel.parts[0] in skip:
            continue
        if f.resolve() not in listed:
            found.append(rel.as_posix())
    return found


def build_sitemap() -> str:
    entries = []
    for sr, en, priority in PAGES:
        for loc in (sr, en):
            if not file_for(loc).exists():
                raise FileNotFoundError(f"Stranica nije pronađena: {file_for(loc)}")
            check_page(loc)
        entries.append(url_entry(sr, sr, en, priority))
        entries.append(url_entry(en, sr, en, priority))

    body = "\n".join(entries)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n\n'
        f"{body}\n\n"
        "</urlset>\n"
    )


if __name__ == "__main__":
    sitemap = build_sitemap()
    (ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    print(f"sitemap.xml ažuriran: {len(PAGES) * 2} stranica ({len(PAGES)} srpskih + {len(PAGES)} engleskih).")
    for page in unlisted_pages():
        print(f"  NAPOMENA: {page} nije u sitemap-u - dodaj je u PAGES ako treba da se indeksira.")
