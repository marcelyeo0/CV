# -*- coding: utf-8 -*-
"""Génère les CV (version design 2 colonnes + version ATS 1 colonne) en PDF via WeasyPrint."""

from data import (
    CONTACT, FORMATION, EXPERIENCES, PROJET_ACADEMIQUE, LANGUES, CENTRES_INTERET,
    PROFILES, ATS_DATA, GITHUB_URL, ADRESSE_ATS,
)

NAVY = "#2e3e4e"
SIDEBAR_BG = "#ededed"

# ---------------------------------------------------------------------------
# CSS partagé (variables de couleur communes aux deux styles)
# ---------------------------------------------------------------------------
BASE_CSS = f"""
@page {{ size: A4; margin: 0; }}
* {{ box-sizing: border-box; }}
body {{
    margin: 0;
    font-family: 'Helvetica Neue', Arial, sans-serif;
    color: #2b2b2b;
    font-size: 10.3px;
}}
.header {{
    background: {NAVY};
    color: #ffffff;
    padding: 26px 34px;
}}
.header .name {{
    font-size: 30px;
    font-weight: 800;
    letter-spacing: 1px;
    margin: 0 0 10px 0;
}}
.contact-row {{
    font-size: 10.5px;
}}
.contact-row span.sep {{ margin: 0 10px; opacity: .6; }}
h2.section {{
    color: {NAVY};
    font-size: 13px;
    font-weight: 800;
    letter-spacing: .3px;
    border-bottom: 1.5px solid {NAVY};
    padding-bottom: 4px;
    margin: 16px 0 10px 0;
}}
.entry {{ margin-bottom: 10px; overflow: hidden; }}
.entry-head {{ overflow: hidden; }}
.entry-title {{ font-weight: 700; }}
.entry-dates {{ font-size: 9.6px; color: #444; white-space: nowrap; float: right; margin-left: 10px; }}
.entry-etab {{ font-style: italic; font-size: 9.8px; color: #444; margin: 1px 0 3px 15px; }}
.entry-text {{ text-align: justify; line-height: 1.42; margin-left: 15px; }}
ul.bullets {{ margin: 3px 0 0 15px; padding-left: 15px; }}
ul.bullets li {{ margin-bottom: 2px; }}
.bullet-dot {{
    display: inline-block; width: 6px; height: 6px; border: 1.4px solid {NAVY};
    border-radius: 50%; margin-right: 8px;
}}
"""

# ---------------------------------------------------------------------------
# Fragments communs
# ---------------------------------------------------------------------------

def _header_html(name_html, adresse=None):
    """name_html : texte affiché en grand dans l'en-tête (nom, ou accroche pour l'ATS)."""
    adresse = adresse if adresse is not None else CONTACT["adresse"]
    return f"""
    <div class="header">
      <div class="name">{name_html}</div>
      <div class="contact-row">
        <span>{CONTACT['email']}</span><span class="sep">|</span>
        <span>{CONTACT['tel']}</span><span class="sep">|</span>
        <span>{adresse}</span>
      </div>
    </div>
    """


def _formation_html():
    rows = ""
    for f in FORMATION:
        rows += f"""
        <div class="entry">
          <div class="entry-head">
            <span class="entry-dates">{f['dates']}</span>
            <span class="entry-title"><span class="bullet-dot"></span>{f['titre']}</span>
          </div>
          <div class="entry-etab">{f['etab']}</div>
        </div>"""
    return f'<h2 class="section">FORMATION</h2>{rows}'


def _experiences_html(title="EXPERIENCES PROFESSIONNELLES"):
    rows = ""
    for e in EXPERIENCES:
        bullets = "".join(f"<li>{b}</li>" for b in e["bullets"])
        rows += f"""
        <div class="entry">
          <div class="entry-head">
            <span class="entry-dates">{e['dates']}</span>
            <span class="entry-title"><span class="bullet-dot"></span>{e['titre']}</span>
          </div>
          <div class="entry-etab">{e['etab']}</div>
          <ul class="bullets">{bullets}</ul>
        </div>"""
    return f'<h2 class="section">{title}</h2>{rows}'


def _projets_html(projets):
    rows = ""
    for p in projets:
        rows += f"""
        <div class="entry">
          <div class="entry-head">
            <span class="entry-dates">{p['dates']}</span>
            <span class="entry-title"><span class="bullet-dot"></span>{p['titre']}</span>
          </div>
          <div class="entry-text">{p['texte']}</div>
        </div>"""
    return f'<h2 class="section">PROJETS PERSONNELS</h2>{rows}'


def _projets_majeurs_html(projets, github_url):
    """Version ATS des projets personnels : décrits par tirets (comme les expériences),
    avec le lien GitHub aligné à droite sur la ligne du titre de section."""
    rows = ""
    for p in projets:
        bullets = "".join(f"<li>{b}</li>" for b in p["bullets"])
        rows += f"""
        <div class="entry">
          <div class="entry-head">
            <span class="entry-dates">{p['dates']}</span>
            <span class="entry-title"><span class="bullet-dot"></span>{p['titre']}</span>
          </div>
          <ul class="bullets">{bullets}</ul>
        </div>"""
    return f"""<h2 class="section with-link">
        <span>PROJETS MAJEURS</span>
        <a class="side-link" href="{github_url}">{github_url}</a>
      </h2>{rows}"""


def _projet_academique_html():
    rows = ""
    for p in PROJET_ACADEMIQUE:
        rows += f"""
        <div class="entry">
          <div class="entry-head">
            <span class="entry-dates">{p['dates']}</span>
            <span class="entry-title"><span class="bullet-dot"></span>{p['titre']}</span>
          </div>
          <div class="entry-text">{p['texte']}</div>
        </div>"""
    return f'<h2 class="section">PROJET ACADEMIQUE</h2>{rows}'


# ---------------------------------------------------------------------------
# Style 1 : version "design" — sidebar grise + colonne droite avec timeline
# ---------------------------------------------------------------------------

def render_design(profile: dict) -> str:
    comp_items = "".join(
        f"<li><b>{label}</b> : {value}</li>" for label, value in profile["competences"]
    )
    langues_items = "".join(f"<li>{l}</li>" for l in LANGUES)
    centres_items = "".join(f"<li>{c}</li>" for c in CENTRES_INTERET)

    css = BASE_CSS + f"""
    .body-wrap {{ display: flex; }}
    .sidebar {{ background: {SIDEBAR_BG}; width: 33%; padding: 20px 22px; }}
    .sidebar h2.section {{ font-size: 11.5px; margin-top: 14px; }}
    .sidebar h2.section:first-child {{ margin-top: 0; }}
    .sidebar p {{ text-align: justify; line-height: 1.45; }}
    .sidebar ul {{ margin: 0; padding-left: 16px; }}
    .sidebar ul li {{ margin-bottom: 5px; }}
    .content {{ width: 67%; padding: 20px 26px; }}
    """

    html = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
    <style>{css}</style></head><body>
    <div class="page">
      {_header_html(CONTACT['nom'])}
      <div class="body-wrap">
        <div class="sidebar">
          <h2 class="section">PROFIL</h2>
          <p>{profile['profil']}</p>
          <h2 class="section">COMPETENCES</h2>
          <ul>{comp_items}</ul>
          <h2 class="section">LANGUES</h2>
          <ul>{langues_items}</ul>
          <h2 class="section">CENTRES D'INTERET</h2>
          <ul>{centres_items}</ul>
        </div>
        <div class="content">
          {_formation_html()}
          {_experiences_html()}
          {_projets_html(profile['projets_personnels'])}
          {_projet_academique_html()}
        </div>
      </div>
    </div>
    </body></html>"""
    return html


# ---------------------------------------------------------------------------
# Style 2 : version "ATS" — une seule colonne, aucun élément décoratif
# ---------------------------------------------------------------------------

def render_ats(profile_key: str) -> str:
    """profile_key : 'Data_Analyst' ou 'Data_Science_IA'. Pioche dans ATS_DATA
    (pas de PROFIL, accroche en en-tête, "PROJETS MAJEURS" avec lien GitHub et
    puces, section "EXPERIENCE")."""
    ats = ATS_DATA[profile_key]

    comp_lines = "".join(
        f'<div><b>{label}</b> : {value}</div>' for label, value in ats["competences"]
    )
    langues_line = " &nbsp;•&nbsp; ".join(LANGUES)
    centres_line = " &nbsp;•&nbsp; ".join(CENTRES_INTERET)

    # Police agrandie par rapport à la base : la suppression du PROFIL et du
    # projet RAG laisse de la place, on en profite pour remplir la page.
    css = BASE_CSS + f"""
    body {{ font-size: 12.3px; }}
    .header {{ padding: 24px 34px; }}
    .header .name {{
        font-size: 16.5px;
        font-weight: 700;
        letter-spacing: 0;
        line-height: 1.35;
        margin-bottom: 11px;
    }}
    .contact-row {{ font-size: 11.8px; }}
    .content {{ padding: 16px 34px 18px 34px; }}
    .content p {{ text-align: justify; line-height: 1.42; margin: 3px 0; }}
    h2.section {{ font-size: 15px; margin: 13px 0 8px 0; }}
    h2.section.with-link {{
        display: flex;
        justify-content: space-between;
        align-items: baseline;
    }}
    h2.section.with-link .side-link {{
        font-size: 11.3px;
        font-weight: 400;
        letter-spacing: 0;
        color: {NAVY};
        text-decoration: none;
    }}
    .entry {{ margin-bottom: 9px; }}
    .entry-dates {{ font-size: 11.2px; }}
    .entry-etab {{ font-size: 11.4px; margin-bottom: 2px; }}
    ul.bullets {{ margin-top: 4px; }}
    ul.bullets li {{ margin-bottom: 4px; }}
    """

    html = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
    <style>{css}</style></head><body>
    <div class="page">
      {_header_html(ats['tagline'], adresse=ADRESSE_ATS)}
      <div class="content">
        <h2 class="section">COMPETENCES</h2>
        {comp_lines}
        {_formation_html()}
        {_experiences_html("EXPERIENCE")}
        {_projets_majeurs_html(ats['projets_majeurs'], GITHUB_URL)}
        {_projet_academique_html()}
        <h2 class="section">LANGUES</h2>
        <div>{langues_line}</div>
        <h2 class="section">CENTRES D'INTERET</h2>
        <div>{centres_line}</div>
      </div>
    </div>
    </body></html>"""
    return html


if __name__ == "__main__":
    import os
    from weasyprint import HTML

    out_dir = "../outputs"
    os.makedirs(out_dir, exist_ok=True)

    for key, profile in PROFILES.items():
        design_html = render_design(profile)
        ats_html = render_ats(key)

        design_path = f"{out_dir}/CV_Marcel_Yeo_{key}.pdf"
        ats_path = f"{out_dir}/CV_Marcel_Yeo_{key}_ATS.pdf"

        HTML(string=design_html).write_pdf(design_path)
        HTML(string=ats_html).write_pdf(ats_path)
        print("Généré :", design_path, ats_path)