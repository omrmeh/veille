import glob
import os
import time
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen

import anthropic
import feedparser

API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=API_KEY)

FEEDS = {
    "Curated & Digests": [
        ("SANS ISC", "https://isc.sans.edu/rssfeed_full.xml"),
        ("TLDR Tech", "https://tldr.tech/tech/rss"),
        ("TLDR AI", "https://tldr.tech/ai/rss"),
        ("TLDR Cybersecurity", "https://tldr.tech/cybersecurity/rss"),
        ("TLDR DevOps & Cloud", "https://tldr.tech/devops/rss"),
    ],
    "Géopolitique — Occident & Académique": [
        ("Foreign Affairs", "https://www.foreignaffairs.com/rss.xml"),
        ("Chatham House", "https://www.chathamhouse.org/path/whatsnew.xml"),
        ("IFRI", "https://www.ifri.org/fr/rss.xml"),
        (
            "IFRI Moyen-Orient",
            "https://www.ifri.org/fr/rss/actualites/moyen-orient-maghreb",
        ),
        ("Stimson Center", "https://www.stimson.org/feed/"),
        (
            "Brookings Middle East",
            "https://www.brookings.edu/topic/middle-east-north-africa/feed/",
        ),
        ("IISS Analysis", "https://www.iiss.org/rss/analysis"),
        (
            "Atlantic Council IranSource",
            "https://www.atlanticcouncil.org/commentary/iransource/feed/",
        ),
        ("Diploweb", "https://www.diploweb.com/spip.php?page=backend"),
        ("Le Grand Continent", "https://legrandcontinent.eu/fr/feed/"),
        (
            "Les Clés du Moyen-Orient",
            "https://www.lesclesdumoyenorient.com/spip.php?page=backend",
        ),
        ("Politico Europe", "https://www.politico.eu/feed/"),
        (
            "Courrier International",
            "https://www.courrierinternational.com/feed/all/rss.xml",
        ),
    ],
    "Géopolitique — Global South & Iran": [
        ("Al Jazeera Middle East", "https://www.aljazeera.com/xml/rss/all.xml"),
        ("Tehran Times", "https://www.tehrantimes.com/rss"),
        ("The Cradle", "https://thecradle.co/feed"),
        ("SCMP Middle East", "https://www.scmp.com/rss/318208/feed"),
        ("South Asian Voices", "https://southasianvoices.org/feed/"),
        ("International Crisis Group", "https://www.crisisgroup.org/rss.xml"),
    ],
    "Cyber — Gouvernance & Policy": [
        ("The Record", "https://therecord.media/feed/"),
        ("CyberScoop", "https://cyberscoop.com/feed/"),
        (
            "IFRI Datasphère",
            "https://www.ifri.org/fr/rss/actualites/geopolitique-datasphere",
        ),
        ("CFR Cyber", "https://www.cfr.org/rss/topics/cybersecurity"),
        ("DiploFoundation", "https://www.diplomacy.edu/feed/"),
        (
            "France Diplomatie Numérique",
            "https://www.diplomatie.gouv.fr/fr/spip.php?page=backend&id_rubrique=11736",
        ),
    ],
    "Tech — AWS & Cloud": [
        ("AWS What's New", "https://aws.amazon.com/new/feed/"),
        ("AWS Blog", "https://aws.amazon.com/blogs/aws/feed/"),
        ("AWS Architecture Blog", "https://aws.amazon.com/blogs/architecture/feed/"),
        ("AWS Security Blog", "https://aws.amazon.com/blogs/security/feed/"),
        ("Last Week in AWS", "https://www.lastweekinaws.com/feed/"),
        ("Cloud Security Alliance", "https://cloudsecurityalliance.org/blog/rss/"),
        ("MIT Technology Review", "https://www.technologyreview.com/feed/"),
        ("Hacker News", "https://hnrss.org/frontpage"),
        ("The Verge", "https://www.theverge.com/rss/index.xml"),
        ("Wired", "https://www.wired.com/feed/rss"),
    ],
    "Tech — Cybersécurité": [
        ("Krebs on Security", "https://krebsonsecurity.com/feed/"),
        ("Schneier on Security", "https://www.schneier.com/blog/index.rdf"),
        ("The Hacker News", "https://feeds.feedburner.com/TheHackersNews"),
        ("Dark Reading", "https://www.darkreading.com/rss.xml"),
        ("Bleeping Computer", "https://www.bleepingcomputer.com/feed/"),
        ("Mandiant Blog", "https://www.mandiant.com/resources/blog/rss.xml"),
        ("Unit 42 Palo Alto", "https://unit42.paloaltonetworks.com/feed/"),
        ("Microsoft Security", "https://www.microsoft.com/en-us/security/blog/feed/"),
    ],
    "IA & LLMs": [
        ("Anthropic Blog", "https://www.anthropic.com/rss.xml"),
        ("OpenAI Blog", "https://openai.com/blog/rss.xml"),
        ("Import AI", "https://jack-clark.net/feed/"),
    ],
    "Finance & Macro": [
        ("Les Echos", "https://syndication.lesechos.fr/rss/rss_la_une.xml"),
        ("FT", "https://www.ft.com/rss/home"),
        ("Bloomberg Technology", "https://feeds.bloomberg.com/technology/news.rss"),
    ],
}

CATEGORY_ICONS = {
    "Curated & Digests": "📋",
    "Géopolitique — Occident & Académique": "🎓",
    "Géopolitique — Global South & Iran": "🌍",
    "Cyber — Gouvernance & Policy": "⚖️",
    "Tech — AWS & Cloud": "☁️",
    "Tech — Cybersécurité": "🔐",
    "IA & LLMs": "🤖",
    "Finance & Macro": "📈",
}

ARTICLES_PAR_SOURCE = 4
FETCH_TIMEOUT_SECONDS = 12
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
}


def fetch_articles(feeds):
    all_articles = {}
    for category, sources in feeds.items():
        print(f"\n📡 Récupération : {category}")
        articles = []
        for name, url in sources:
            try:
                request = Request(url, headers=REQUEST_HEADERS)
                with urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
                    raw_feed = response.read()
                feed = feedparser.parse(raw_feed)
                for entry in feed.entries[:ARTICLES_PAR_SOURCE]:
                    published = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published = datetime(
                            *entry.published_parsed[:6], tzinfo=timezone.utc
                        )
                    articles.append(
                        {
                            "source": name,
                            "title": entry.get("title", "Sans titre"),
                            "summary": entry.get(
                                "summary", entry.get("description", "")
                            )[:600],
                            "link": entry.get("link", ""),
                            "published": published.strftime("%d/%m/%Y")
                            if published
                            else "Date inconnue",
                        }
                    )
                print(
                    f"  ✓ {name} — {len(feed.entries[:ARTICLES_PAR_SOURCE])} articles"
                )
            except (TimeoutError, URLError) as e:
                print(f"  ✗ {name} — Timeout/réseau : {e}")
            except Exception as e:
                print(f"  ✗ {name} — Erreur : {e}")
        all_articles[category] = articles
    return all_articles


def synthesize_category(category, articles):
    if not articles:
        return None

    articles_text = "\n\n".join(
        [
            f"[{i + 1}] {a['source']} — {a['published']}\nTitre : {a['title']}\nRésumé : {a['summary']}"
            for i, a in enumerate(articles)
        ]
    )

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1200,
        messages=[
            {
                "role": "user",
                "content": f"""Tu es un expert en veille stratégique pour un consultant cloud AWS passionné de géopolitique et cybersécurité.

Voici les derniers articles de la catégorie "{category}".

Ta mission : produire une synthèse dense et actionnable en français, structurée en deux parties séparées par "|||" :

PARTIE 1 — SYNTHÈSE (5-7 phrases) :
Résume les faits et tendances clés du jour dans cette catégorie. Regroupe les sujets connexes. Cite les sources entre parenthèses. Sois factuel et précis.

PARTIE 2 — ANALYSE & ENJEUX (6-8 phrases) :
Explique les implications stratégiques en profondeur. Pour chaque point complexe, explique les mécanismes sous-jacents comme si tu parlais à un lecteur intelligent mais non-spécialiste. Réponds à : Pourquoi c'est important ? Quels sont les acteurs en jeu ? Quelles sont les dynamiques de fond ? Quelles implications pour le cloud, la cybersécurité ou la géopolitique ? Quelles tendances de long terme cela révèle-t-il ?
Quand les sujets sont trop techniques (exploits, acronymes), prends soin d'expliquer et quand tu le juges pertinent de donner des exemples concrets, comme si tu parlais à un lecteur intelligent mais non technique.
Sélectionne les 5-8 articles les plus importants parmi ceux fournis. Ignore les articles trop anecdotiques.

Articles disponibles :
{articles_text}

Réponds UNIQUEMENT avec les deux parties séparées par |||, sans titres ni labels.""",
            }
        ],
    )

    raw = response.content[0].text
    parts = raw.split("|||")
    return {
        "synthese": parts[0].strip() if len(parts) > 0 else raw,
        "analyse": parts[1].strip() if len(parts) > 1 else "",
        "article_count": len(articles),
        "sources": list(set(a["source"] for a in articles)),
        "top_links": [(a["title"], a["link"], a["source"]) for a in articles[:6]],
    }


def generate_html(results, date_str):
    total_sources = sum(len(v["sources"]) for v in results.values() if v)

    nav_items = ""
    sections_html = ""

    for category, data in results.items():
        if not data:
            continue

        icon = CATEGORY_ICONS.get(category, "📌")
        cat_id = (
            category.lower()
            .replace(" ", "-")
            .replace("&", "and")
            .replace("—", "")
            .replace(" ", "-")
        )

        nav_items += f'<a href="#{cat_id}" class="nav-item">{icon} {category}</a>'

        links_html = ""
        for title, link, source in data["top_links"]:
            links_html += f'<a href="{link}" target="_blank" class="ref-link">↗ <span class="ref-source">[{source}]</span> {title[:80]}{"..." if len(title) > 80 else ""}</a>'

        sections_html += f"""
        <section class="cat-section" id="{cat_id}">
            <div class="cat-header">
                <span class="cat-icon">{icon}</span>
                <h2 class="cat-title">{category}</h2>
                <span class="cat-meta">{data["article_count"]} articles · {len(data["sources"])} sources</span>
            </div>
            <div class="content-grid">
                <div class="block synthese-block">
                    <div class="block-label">Synthèse</div>
                    <p>{data["synthese"]}</p>
                </div>
                <div class="block analyse-block">
                    <div class="block-label">Analyse & enjeux</div>
                    <p>{data["analyse"]}</p>
                </div>
            </div>
            <div class="refs-block">
                <div class="refs-label">Sources du jour</div>
                <div class="refs-list">{links_html}</div>
            </div>
        </section>"""

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Veille — {date_str}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=IBM+Plex+Sans:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #f5f2eb;
            --surface: #ffffff;
            --surface2: #f0ede6;
            --border: #ddd9d0;
            --accent: #1a472a;
            --accent2: #c17f24;
            --text: #1c1c1c;
            --text-muted: #666;
            --text-dim: #999;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: var(--bg); color: var(--text); font-family: 'IBM Plex Sans', sans-serif; font-weight: 300; line-height: 1.75; }}
        .header {{ background: var(--accent); color: white; padding: 2rem 3rem; display: flex; justify-content: space-between; align-items: flex-end; }}
        .header-label {{ font-size: 0.65rem; letter-spacing: 0.2em; text-transform: uppercase; opacity: 0.6; margin-bottom: 0.3rem; }}
        .header-title {{ font-family: 'Libre Baskerville', serif; font-size: 1.8rem; font-weight: 400; letter-spacing: -0.01em; }}
        .header-right {{ text-align: right; opacity: 0.7; font-size: 0.8rem; }}
        .header-nav {{ display: flex; gap: 1rem; align-items: center; margin-top: 0.5rem; justify-content: flex-end; }}
        .header-nav a {{ color: rgba(255,255,255,0.6); text-decoration: none; font-size: 0.75rem; transition: color 0.2s; }}
        .header-nav a:hover {{ color: white; }}
        .nav {{ background: var(--surface); border-bottom: 1px solid var(--border); display: flex; overflow-x: auto; scrollbar-width: none; padding: 0 2rem; position: sticky; top: 0; z-index: 100; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
        .nav::-webkit-scrollbar {{ display: none; }}
        .nav-item {{ padding: 0.9rem 1rem; font-size: 0.75rem; color: var(--text-muted); text-decoration: none; white-space: nowrap; border-bottom: 2px solid transparent; transition: all 0.2s; }}
        .nav-item:hover {{ color: var(--accent); border-bottom-color: var(--accent); }}
        .main {{ max-width: 1100px; margin: 0 auto; padding: 2.5rem 3rem; }}
        .cat-section {{ margin-bottom: 3rem; background: var(--surface); border: 1px solid var(--border); border-radius: 2px; overflow: hidden; }}
        .cat-header {{ display: flex; align-items: center; gap: 0.8rem; padding: 1rem 1.5rem; background: var(--surface2); border-bottom: 1px solid var(--border); }}
        .cat-icon {{ font-size: 1rem; }}
        .cat-title {{ font-family: 'Libre Baskerville', serif; font-size: 1rem; font-weight: 700; }}
        .cat-meta {{ margin-left: auto; font-size: 0.7rem; color: var(--text-dim); }}
        .content-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0; }}
        .block {{ padding: 1.4rem 1.5rem; }}
        .synthese-block {{ border-right: 1px solid var(--border); }}
        .analyse-block {{ background: #fffdf7; }}
        .block-label {{ font-size: 0.6rem; letter-spacing: 0.15em; text-transform: uppercase; color: var(--accent2); font-weight: 500; margin-bottom: 0.6rem; }}
        .block p {{ font-size: 0.855rem; line-height: 1.75; color: #2a2a2a; }}
        .refs-block {{ border-top: 1px solid var(--border); padding: 0.8rem 1.5rem; background: var(--surface2); }}
        .refs-label {{ font-size: 0.6rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-dim); margin-bottom: 0.5rem; }}
        .refs-list {{ display: flex; flex-wrap: wrap; gap: 0.4rem; }}
        .ref-link {{ font-size: 0.72rem; color: var(--text-muted); text-decoration: none; background: white; border: 1px solid var(--border); padding: 0.2rem 0.5rem; border-radius: 2px; transition: all 0.15s; max-width: 280px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .ref-link:hover {{ color: var(--accent); border-color: var(--accent); }}
        .ref-source {{ color: var(--accent2); font-weight: 500; }}
        .footer {{ border-top: 1px solid var(--border); padding: 1.5rem 3rem; text-align: center; font-size: 0.7rem; color: var(--text-dim); letter-spacing: 0.05em; }}
        @media (max-width: 768px) {{
            .content-grid {{ grid-template-columns: 1fr; }}
            .synthese-block {{ border-right: none; border-bottom: 1px solid var(--border); }}
            .main {{ padding: 1.5rem; }}
            .header {{ padding: 1.5rem; flex-direction: column; gap: 0.5rem; }}
        }}
    </style>
</head>
<body>
<header class="header">
    <div>
        <div class="header-label">Veille stratégique</div>
        <h1 class="header-title">Intelligence du jour</h1>
    </div>
    <div class="header-right">
        {date_str}<br>
        {total_sources} sources agrégées
        <div class="header-nav">
            <a href="index.html">← Toutes les éditions</a>
        </div>
    </div>
</header>
<nav class="nav">
    {nav_items}
</nav>
<main class="main">
    {sections_html}
</main>
<footer class="footer">
    Généré automatiquement · {date_str} · Claude Sonnet
</footer>
</body>
</html>"""


def generate_index():
    editions = sorted(glob.glob("editions/veille-*.html"), reverse=True)

    items_html = ""
    for i, path in enumerate(editions):
        filename = os.path.basename(path)
        slug = filename.replace("veille-", "").replace(".html", "")
        try:
            date_obj = datetime.strptime(slug, "%Y-%m-%d")
            label = date_obj.strftime("%A %d %B %Y").capitalize()
        except Exception:
            label = slug
        today_badge = ' <span class="today-badge">aujourd\'hui</span>' if i == 0 else ""
        items_html += f"""
        <a href="editions/{filename}" class="edition-link">
            <span class="edition-date">{label}{today_badge}</span>
            <span class="edition-arrow">→</span>
        </a>"""

    index_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Veille Stratégique — Archives</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=IBM+Plex+Sans:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #f5f2eb;
            --surface: #ffffff;
            --surface2: #f0ede6;
            --border: #ddd9d0;
            --accent: #1a472a;
            --accent2: #c17f24;
            --text: #1c1c1c;
            --text-muted: #666;
            --text-dim: #999;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: var(--bg); color: var(--text); font-family: 'IBM Plex Sans', sans-serif; font-weight: 300; min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 4rem 2rem; }}
        .header {{ text-align: center; margin-bottom: 3rem; }}
        .header-label {{ font-size: 0.65rem; letter-spacing: 0.2em; text-transform: uppercase; color: var(--accent2); margin-bottom: 0.5rem; }}
        .header-title {{ font-family: 'Libre Baskerville', serif; font-size: 2.2rem; font-weight: 400; color: var(--accent); letter-spacing: -0.02em; }}
        .header-sub {{ font-size: 0.8rem; color: var(--text-muted); margin-top: 0.5rem; }}
        .editions-list {{ width: 100%; max-width: 600px; display: flex; flex-direction: column; border: 1px solid var(--border); background: var(--surface); }}
        .edition-link {{ display: flex; align-items: center; justify-content: space-between; padding: 1.1rem 1.5rem; border-bottom: 1px solid var(--border); text-decoration: none; color: var(--text); transition: all 0.15s; }}
        .edition-link:last-child {{ border-bottom: none; }}
        .edition-link:first-child {{ background: var(--surface2); }}
        .edition-link:hover {{ background: var(--surface2); padding-left: 1.8rem; }}
        .edition-date {{ font-size: 0.9rem; }}
        .edition-arrow {{ color: var(--text-dim); transition: transform 0.15s; }}
        .edition-link:hover .edition-arrow {{ transform: translateX(4px); color: var(--accent); }}
        .today-badge {{ display: inline-block; font-size: 0.62rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent2); background: rgba(193,127,36,0.1); padding: 0.1rem 0.4rem; border-radius: 2px; margin-left: 0.5rem; vertical-align: middle; }}
        .footer {{ margin-top: 2rem; font-size: 0.7rem; color: var(--text-dim); letter-spacing: 0.05em; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-label">Archives</div>
        <h1 class="header-title">Veille Stratégique</h1>
        <p class="header-sub">{len(editions)} édition{"s" if len(editions) > 1 else ""} disponible{"s" if len(editions) > 1 else ""}</p>
    </div>
    <div class="editions-list">
        {items_html}
    </div>
    <div class="footer">Généré automatiquement · Claude Sonnet</div>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html)


def main():
    date_str = datetime.now().strftime("%d %B %Y")
    date_slug = datetime.now().strftime("%Y-%m-%d")
    output_file = f"editions/veille-{date_slug}.html"

    print("🚀 Démarrage de la veille...\n")

    os.makedirs("editions", exist_ok=True)

    all_articles = fetch_articles(FEEDS)

    results = {}
    for category, articles in all_articles.items():
        print(f"\n🤖 Synthèse : {category} ({len(articles)} articles)")
        results[category] = synthesize_category(category, articles)
        time.sleep(0.5)

    html = generate_html(results, date_str)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n✅ Veille générée → {output_file}")

    generate_index()
    print("✅ Index mis à jour → index.html")


if __name__ == "__main__":
    main()
