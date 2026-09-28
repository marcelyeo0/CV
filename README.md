# CV & LM automatisés — Marcel Yeo

Une offre d'emploi en entrée, un CV ATS et une lettre de motivation en PDF 1 page en sortie.
Le LLM **sélectionne et ordonne** des éléments de `data/catalog.yaml` ; il n'en invente aucun.
Le code rejette tout identifiant inconnu et toute techno absente du catalogue.

## Flux de données

```
                    offre.txt  ou  --url
                            │
                            ▼
                  apply/ingest.py          texte brut (>= 400 car.)
                            │
                            ▼
                  apply/analyze.py ──► LLM ──► OfferAnalysis     (analysis.json)
                            │
                            ▼
   data/catalog.yaml ──► apply/select.py ──► LLM ──► Selection   (selection.json)
                            │                          │
                            │                    cvgen/catalog.py
                            │                  validate_selection()
                            │              ids inconnus / techno hors
                            │              liste blanche -> ERREUR
                            ▼
                  apply/letter.py ──► LLM ──► LetterDraft        (lm_draft.md)
                            │              4 paragraphes, termes et chiffres
                            │              hors catalogue / offre -> retry puis ERREUR
                            │
                  ═══════ RELECTURE PAR MARCEL ═══════
                            │
                            ▼
      cvgen/render.py + cvgen/letter_render.py ──► WeasyPrint ──► CV.pdf + LM.pdf
                     (réduit jusqu'à tenir sur 1 page)
```

Deux commandes, deux temps : `prepare` s'arrête sur les JSON/MD, `render` ne produit un PDF
qu'à partir de fichiers présents sur le disque. Rien n'est généré sans relecture possible.

## Fichiers

### À modifier par toi

| Fichier | Rôle | Entrée / Sortie |
|---|---|---|
| **`data/catalog.yaml`** | Source unique de vérité : contact, disponibilité, formation, expériences, projets, compétences, langues, centres d'intérêt, et les deux sélections par défaut. | — |
| `data/lm_skeleton.md` | Squelette de la lettre : en-tête, objet, formules de politesse et quatre emplacements `{{ ... }}` remplis par le LLM. Un bloc `[À REMPLIR PAR MARCEL ...]` ajouté à la main bloque le rendu tant qu'il n'est pas remplacé. | — |
| `.env` | Ta clé Gemini. Copié depuis `.env.example`, jamais versionné. | — |
| `outputs/<dossier>/selection.json` | La sélection proposée, à relire et corriger avant rendu. | — |
| `outputs/<dossier>/lm_draft.md` | Le brouillon de lettre, à relire. Les paragraphes 3 et 4 sont à réécrire à ta main (voir plus bas). | — |

### Code — à ne pas avoir besoin de toucher

| Fichier | Rôle | Entrée → Sortie |
|---|---|---|
| `cvgen/models.py` | Schémas Pydantic (`Catalog`, `Selection`, `OfferAnalysis`, `LetterDraft`) et détection des tokens « techno-formés ». | — |
| `cvgen/catalog.py` | Charge le catalogue, construit la liste blanche des technos, valide une sélection, la résout en contenu prêt à rendre. | `catalog.yaml` → `Catalog` ; `Selection` → `ResolvedCV` |
| `cvgen/render.py` | Rend le PDF et retire les éléments les moins prioritaires jusqu'à tenir sur 1 page. | `Selection` + `Catalog` → `.pdf` + `RenderReport` |
| `cvgen/letter_render.py` | Découpe `lm_draft.md` relu en blocs et rend la lettre sur 1 page. | `lm_draft.md` → `.pdf` + `RenderReport` |
| `cvgen/templates/cv.html.j2` | Gabarit HTML du CV, autoéchappé. | contexte → HTML |
| `cvgen/templates/letter.html.j2` | Gabarit HTML de la lettre. | contexte → HTML |
| `cvgen/templates/base.css` | Charte commune CV + LM : 'Helvetica Neue', Arial, sans-serif ; ligatures désactivées, taille de base. | — |
| `apply/ingest.py` | Récupère le texte de l'offre. | fichier / stdin / URL → `str` |
| `apply/analyze.py` | Extrait les informations de l'offre. | `str` → `OfferAnalysis` |
| `apply/select.py` | Choisit projets et compétences. | `OfferAnalysis` + `Catalog` → `Selection` |
| `apply/letter.py` | Rédige les quatre paragraphes du corps de la LM, vérifie leur vocabulaire et remplit le squelette. | `OfferAnalysis` + `Selection` + `Catalog` → `LetterDraft` → `lm_draft.md` |
| `apply/llm.py` | Isole l'appel LLM derrière `LLMProvider.structured(prompt, schema, system)`. Convertit le schéma Pydantic au sous-ensemble accepté par Gemini et reprend les erreurs transitoires (503, 429, 500) avec attente croissante. | prompt + schéma → instance Pydantic |
| `main.py` | CLI `prepare` / `render`. | — |

## Installation

WeasyPrint a besoin de bibliothèques système (Pango, cairo, GDK-PixBuf).

- **Windows** : installer le runtime GTK — [gtk3-runtime installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases)
- **Debian / Ubuntu** : `sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libffi-dev`
- **macOS** : `brew install pango libffi`

```bash
python -m venv src/.venv
src/.venv/Scripts/activate    # Windows ; source src/.venv/bin/activate ailleurs
pip install -r requirements.txt
cp .env.example .env          # puis renseigner GEMINI_API_KEY
```

Clé API : https://aistudio.google.com/apikey

Variables optionnelles dans `.env` : `GEMINI_MODEL` (défaut `gemini-3.8-flash`) et
`GEMINI_TEMPERATURE` (défaut `0.2`, pour une sélection reproductible).

## Usage

```bash
# 1. analyser une offre et proposer une sélection (ne rend aucun PDF)
python main.py prepare --text offre.txt
python main.py prepare --url https://...          # best effort
pbpaste | python main.py prepare --text -         # coller directement

# -> outputs/2027-01-15_Decathlon_Data-Analyst/
#      offre.txt  analysis.json  selection.json  lm_draft.md

# 2. relire, corriger selection.json et lm_draft.md, puis rendre
python main.py render outputs/2027-01-15_Decathlon_Data-Analyst/

# régénérer les CV génériques
python main.py render --default data_analyst
python main.py render --default all
```

Si l'offre est en anglais, un avertissement s'affiche : la LM reste en français et le CV
n'est pas traduit.

Codes de sortie de `prepare` : `2` offre illisible, `3` échec d'analyse ou de sélection,
`4` échec de rédaction de la lettre — dans ce dernier cas `offre.txt`, `analysis.json` et
`selection.json` sont déjà écrits et le CV reste rendable.

## La lettre de motivation

Le LLM rédige les quatre paragraphes du corps :

1. `pourquoi_entreprise` — l'entreprise et le périmètre du poste, d'après l'offre.
2. `adequation_missions` — les missions de l'offre face aux projets de `selection.json`.
3. `motivation_personnelle` — **proposition à réécrire**.
4. `apport_parcours` — **proposition à réécrire**.

Les paragraphes 1 et 2 se déduisent de données vérifiables. Les paragraphes 3 et 4 ne
peuvent citer que des faits du catalogue (formation, expériences, projet académique,
langues, centres d'intérêt), mais le LLM ne connaît pas tes raisons réelles : il compose.
Relis-les et réécris-les avant d'envoyer, c'est ce que tu défendras en entretien.

## Ajouter un projet au catalogue

Dans `data/catalog.yaml`, sous `projets` :

```yaml
  - id: mon_projet                  # identifiant unique, snake_case
    titre: "Titre affiché sur le CV"
    dates: "Mars 2027 - En cours"
    tags: [python, nlp, api]        # servent au ciblage par le LLM
    bullets:
      - "Première puce, telle qu'elle apparaîtra."
      - "Deuxième puce."
      - "Puce alternative, angle différent."
    bullets_defaut: [0, 1]          # indices montrés par défaut
```

Le projet devient sélectionnable immédiatement, et toute techno qu'il mentionne entre dans
la liste blanche. Pour l'ajouter à un CV générique, mettre son `id` dans
`selections_par_defaut.<variante>.project_ids`.

Même principe pour une compétence, sous `competences` :

```yaml
  - {id: polars, label: "Polars", groupe: polars,
     categories: [analyse_donnees, data_engineering], tags: [polars, dataframe]}
```

`groupe` marque les équivalences : deux compétences de même `groupe` (par exemple `SQL` et
`SQL (PostgreSQL)`) ne peuvent pas apparaître ensemble dans une même catégorie.
`categories` limite les rubriques où la compétence peut être placée.

## Règles que le code fait respecter

- Un `project_id` ou un `skill_id` absent du catalogue fait échouer la génération.
- Une puce reformulée par le LLM est rejetée si elle mentionne une techno hors catalogue ou
  introduit un chiffre absent de la puce d'origine — la puce d'origine est alors conservée.
- La disponibilité (`stage de 4-6 mois`, `à partir de mars 2027`) vient du catalogue seul.
  Une tagline contenant une date est rejetée.
- 3 projets au maximum, ordonnés.
- `missing_keywords` liste les mots-clés de l'offre absents du catalogue. C'est à toi de
  décider d'ajouter la compétence, honnêtement — jamais au code.
- La lettre ne peut citer que des technos, noms propres et chiffres présents dans la
  sélection, le parcours du catalogue ou l'offre. Sinon : un retry avec l'erreur renvoyée
  au LLM, puis échec.
- Tout PDF fait 1 page ; les retraits effectués pour y arriver sont journalisés.
