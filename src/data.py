# -*- coding: utf-8 -*-
"""Contenu structuré des deux variantes de CV de Marcel Yeo."""

CONTACT = {
    "nom": "MARCEL YEO",
    "email": "marcelyeo30@gmail.com",
    "tel": "+33 7 58 02 29 81",
    "adresse": "34 Boulevard Pochet Lagaye, 63000 Clermont-Ferrand",
}

FORMATION = [
    {
        "titre": "Diplôme d'Ingénieur en Informatique",
        "dates": "2025 - En cours",
        "etab": "ISIMA – Institut Supérieur d'Informatique, de Modélisation et de leurs Applications, Clermont-Ferrand",
    },
    {
        "titre": "Classes Préparatoires Scientifiques (MPSI/MP)",
        "dates": "2023 - 2025",
        "etab": "Lycée Français Blaise Pascal, Côte d'Ivoire",
    },
    {
        "titre": "Formation Olympiades de Mathématiques",
        "dates": "2021 - 2023",
        "etab": "SMCI (Société Mathématique de Côte d'Ivoire), Côte d'Ivoire",
    },
]

EXPERIENCES = [
    {
        "titre": "Stage – Trading & Front Office",
        "dates": "Mai 2025 - Juin 2025",
        "etab": "Attijariwafa Securities West Africa | Côte d'Ivoire",
        "bullets": [
            "Traitement et suivi des ordres de bourse, analyse des flux de transactions et reporting quotidien.",
            "Participation à la relation clientèle institutionnelle et à l'organisation de l'Assemblée Générale des actionnaires.",
        ],
    },
    {
        "titre": "Trésorier – Association Gala ISIMA",
        "dates": "Mars 2026 - Mars 2027",
        "etab": "INP ISIMA | Clermont-Ferrand",
        "bullets": [
            "Gestion budgétaire, suivi financier et construction des tableaux de bord de l'association (budget ~300 participants).",
            "Coordination logistique et organisationnelle des événements, négociation et suivi contractuel des prestataires.",
        ],
    },
]

PROJET_ACADEMIQUE = [
    {
        "titre": "Jeu Vidéo IA en C – Agent Reinforcement Learning (SDL2)",
        "dates": "Juin 2026",
        "texte": (
            "Projet de fin d'année : développement d'un moteur de jeu en C (SDL2) intégrant un agent entraîné "
            "par policy gradient (algorithme REINFORCE). Implémentation from scratch du pipeline d'entraînement : "
            "extraction de features d'état, politique softmax paramétrée et mise à jour des poids par descente "
            "de gradient, avec gestion bas-niveau de la mémoire."
        ),
    }
]

LANGUES = ["Français : langue maternelle", "Anglais : niveau B2 (professionnel)"]
CENTRES_INTERET = [
    "Cyclisme et triathlon (compétition)",
    "Sports automobiles",
    "Boxe et musculation",
    "Basketball",
    "Finance de marché",
]

# ---------------------------------------------------------------------------
# Variante 1 : DATA ANALYST
# ---------------------------------------------------------------------------
DATA_ANALYST = {
    "titre_fichier": "Data_Analyst",
    "profil": (
        "Étudiant ingénieur en informatique à l'ISIMA (Clermont-Ferrand), à la recherche d'un stage de 6 mois "
        "en <b>Data Analyse / Études statistiques à partir de janvier 2027</b>. Solide formation mathématique "
        "(classes préparatoires, olympiades) appliquée à l'analyse de données : statistiques inférentielles, "
        "analyse multivariée (ACP), modélisation prédictive et restitution via tableaux de bord. Maîtrise de "
        "Python, SQL et des outils de dataviz, avec une forte appétence pour les enjeux business et financiers."
    ),
    "competences": [
        ("Langages & requêtage", "Python, SQL (PostgreSQL), C, C++"),
        ("Statistiques", "statistiques inférentielles, tests d'hypothèses, ACP, clustering (k-means, CAH), régression"),
        ("Machine Learning", "Scikit-Learn, modélisation prédictive, séries temporelles, validation croisée"),
        ("Analyse de données", "Pandas, NumPy, nettoyage et structuration, ETL, données hétérogènes"),
        ("Dataviz & Reporting", "Streamlit, Matplotlib, tableaux de bord, suivi de KPI, Excel"),
        ("Cloud & Déploiement", "Google Cloud Platform (APIs Gemini, Sheets, Gmail), Docker, déploiement self-hosted, gestion d'authentification et de quotas API"),
        ("Outils", "Git, Linux, n8n, Jupyter, Excel"),
    ],
    "projets_personnels": [
        {
            "titre": "Automatisation de Pipeline de Données & Reporting (n8n)",
            "dates": "Juillet 2026",
            "texte": (
                "Pipeline ETL end-to-end sous n8n (self-hosted) : ingestion via API, normalisation, "
                "déduplication et persistance structurée (Google Sheets API), puis scoring automatisé de "
                "pertinence. Enrichissement sémantique via LLM (Gemini), logs d'audit et reporting "
                "automatisé des indicateurs de suivi."
            ),
        },
        {
            "titre": "Segmentation par ACP & Prévision de Distribution",
            "dates": "Février 2026 - Avril 2026",
            "texte": (
                "Pipeline Python/SQL d'analyse d'assortiment produit : nettoyage et agrégation des ventes, "
                "réduction dimensionnelle par ACP et classification ascendante hiérarchique pour "
                "identifier les typologies de points de vente. Modèle de forecasting à 3 mois et tableau "
                "de bord Streamlit mesurant l'écart entre assortiment théorique et distribution effective."
            ),
        },
        {
            "titre": "Backtesting Quantitatif – Validation Statistique de Stratégies",
            "dates": "Août 2025 - Décembre 2025",
            "texte": (
                "Framework d'analyse de séries temporelles financières (Pandas, NumPy, Backtrader) : "
                "ingestion de données de marché, stratégies momentum et mean-reversion, optimisation des "
                "hyperparamètres et validation out-of-sample par walk-forward. Évaluation de la robustesse "
                "via métriques de risque (Sharpe, drawdown) et tests de significativité."
            ),
        },
        {
            "titre": "Pipeline RAG – Contrôle de Conformité Documentaire",
            "dates": "Mai 2025 - Juillet 2025",
            "texte": (
                "Pipeline RAG en Python pour le contrôle automatisé de documents réglementaires : "
                "structuration de corpus hétérogènes, indexation vectorielle (PostgreSQL/pgvector) et "
                "inférence LLM. Détection d'anomalies avec justification par extraits sourcés pour "
                "garantir la traçabilité, résultats exposés via API REST (FastAPI)."
            ),
        },
    ],
}

# ---------------------------------------------------------------------------
# Variante 2 : DATA SCIENCE / IA
# ---------------------------------------------------------------------------
DATA_SCIENCE_IA = {
    "titre_fichier": "Data_Science_IA",
    "profil": (
        "Étudiant ingénieur en informatique à l'ISIMA (Clermont-Ferrand), à la recherche d'un stage de 6 mois "
        "en <b>Data Science / Intelligence Artificielle à partir de janvier 2027</b>. Expérience concrète et "
        "autonome en conception de solutions IA end-to-end : pipelines de données, machine learning, LLM et RAG, "
        "computer vision et automatisation de workflows. Maîtrise de Python et SQL, à l'aise en environnement "
        "collaboratif (Git), avec une forte appétence pour la finance quantitative."
    ),
    "competences": [
        ("Langages", "Python, SQL, C, C++"),
        ("Machine Learning", "Scikit-Learn, apprentissage supervisé, Reinforcement Learning, évaluation de modèles"),
        ("LLM & NLP", "RAG, LangChain, embeddings, bases vectorielles (pgvector, ChromaDB), prompt engineering"),
        ("Computer Vision", "OpenCV, MediaPipe, détection et estimation de pose"),
        ("Data Engineering", "Pandas, NumPy, ETL, API REST (FastAPI), PostgreSQL, Google Sheets API"),
        ("Cloud & Déploiement", "Google Cloud Platform (APIs Gemini, Sheets, Gmail), Docker, conteneurisation et déploiement self-hosted, gestion d'authentification et de quotas API"),
        ("Outils", "Git, Linux, n8n, Jupyter"),
    ],
    "projets_personnels": [
        {
            "titre": "Agent IA Connecté – Protocole MCP (Model Context Protocol)",
            "dates": "Août 2026 - En cours",
            "texte": (
                "Agent conversationnel Python (LangChain) connecté via le protocole MCP à des sources "
                "hétérogènes (SQL, SaaS CRM/support). Traduction du langage naturel en appels d'outils "
                "structurés et génération automatisée de rapports d'insights. Développement d'un serveur "
                "MCP exposant schémas de données et permissions d'accès."
            ),
        },
        {
            "titre": "Automatisation Intelligente de Candidatures (n8n)",
            "dates": "Juillet 2026",
            "texte": (
                "Pipeline d'automatisation end-to-end sous n8n (self-hosted, Docker) : ingestion d'offres "
                "(API Apify), normalisation et persistance (Google Sheets API), scoring de pertinence puis "
                "génération de contenus personnalisés via LLM (Gemini Flash-Lite, prompt engineering). "
                "Intégration Gmail API, logs d'audit et gestion d'erreurs."
            ),
        },
        {
            "titre": "Bike Fit – Solution IA d'Analyse Posturale par Computer Vision",
            "dates": "Juin 2026 - En cours",
            "texte": (
                "Logiciel Python modulaire : pipeline de traitement d'image et d'inférence de pose "
                "(MediaPipe, OpenCV), extraction de landmarks et calcul d'angles articulaires, génération "
                "de recommandations via API LLM (Gemini) et rapports PDF. Interface desktop CustomTkinter. "
                "En test auprès de vélocistes professionnels, cas d'usage B2B identifié."
            ),
        },
        {
            "titre": "Pipeline RAG – Contrôle de Conformité Réglementaire",
            "dates": "Mai 2025 - Juillet 2025",
            "texte": (
                "Pipeline RAG en Python pour l'analyse automatisée de documents réglementaires : chunking "
                "sémantique, indexation vectorielle (PostgreSQL/pgvector) et inférence LLM. Détection "
                "d'anomalies avec justification par extraits sourcés pour garantir la traçabilité. "
                "Résultats exposés via API REST (FastAPI), évaluation de la pertinence du retrieval."
            ),
        },
    ],
}

PROFILES = {
    "Data_Analyst": DATA_ANALYST,
    "Data_Science_IA": DATA_SCIENCE_IA,
}

# ---------------------------------------------------------------------------
# Contenu spécifique à la version ATS (1 colonne) :
# - pas de PROFIL (remplacé par une accroche dans l'en-tête)
# - compétences avec Java ajouté et PowerBI à la place de Streamlit
# - "projets majeurs" décrits par tirets (comme les expériences), sans le RAG
# ---------------------------------------------------------------------------
GITHUB_URL = "https://github.com/marcelyeo0"
ADRESSE_ATS = "Clermont-Ferrand 63"

ATS_DATA = {
    "Data_Analyst": {
        "tagline": "Recherche d'un stage de 4-6 mois en Data Analyst à partir de mars 2027",
        "competences": [
            ("Langages & requêtage", "Python, SQL (PostgreSQL), Java, C, C++"),
            ("Statistiques", "statistiques inférentielles, tests d'hypothèses, ACP, clustering (k-means, CAH), régression"),
            ("Machine Learning", "Scikit-Learn, modélisation prédictive, séries temporelles, validation croisée"),
            ("Analyse de données", "Pandas, NumPy, nettoyage et structuration, ETL, données hétérogènes"),
            ("Dataviz & Reporting", "Power BI, Matplotlib, tableaux de bord, suivi de KPI, Excel"),
            ("Cloud & Déploiement", "Google Cloud Platform (APIs Gemini, Sheets, Gmail), Docker, déploiement self-hosted, gestion d'authentification et de quotas API"),
            ("Outils", "Git, Linux, n8n, Jupyter, Excel"),
        ],
        "projets_majeurs": [
            {
                "titre": "Bike Fit – Analyse Posturale par Computer Vision (Freelance)",
                "dates": "Juin 2026 - En cours",
                "bullets": [
                    "Logiciel Python modulaire : pipeline de pose (MediaPipe, OpenCV), extraction de landmarks et calcul d'angles articulaires, recommandations via LLM (Gemini) et rapports PDF.",
                    "En test auprès de vélocistes professionnels.",
                ],     
                # "titre": "Automatisation de Pipeline de Données & Reporting (n8n)",
                # "dates": "Juillet 2026",
                # "bullets": [
                #     "Conception d'un pipeline ETL end-to-end orchestré sous n8n (self-hosted) : ingestion de données via API, normalisation, déduplication et persistance structurée (Google Sheets API), puis scoring automatisé de pertinence.",
                #     "Intégration d'une API LLM (Gemini) pour l'enrichissement sémantique des données, avec logs d'audit, gestion d'erreurs et reporting automatisé des indicateurs de suivi.",
                # ],
            },
            {
                "titre": "Segmentation par ACP & Prévision de Distribution",
                "dates": "Février 2026 - Avril 2026",
                "bullets": [
                    "Pipeline Python/SQL d'analyse d'assortiment produit : nettoyage et agrégation de données de ventes, réduction dimensionnelle par Analyse en Composantes Principales et classification ascendante hiérarchique pour identifier les typologies de points de vente.",
                    "Interprétation des axes factoriels, modèle de forecasting à 3 mois et tableau de bord Power BI mesurant l'écart entre assortiment théorique et distribution effective.",
                ],
            },
            {
                "titre": "Backtesting Quantitatif – Validation Statistique de Stratégies",
                "dates": "Août 2025 - Décembre 2025",
                "bullets": [
                    "Conception d'un framework d'analyse de séries temporelles financières (Pandas, NumPy, Backtrader) : ingestion et nettoyage de données de marché, implémentation de stratégies momentum et mean-reversion, optimisation des hyperparamètres et validation out-of-sample par walk-forward.",
                    "Évaluation de la robustesse via métriques de risque (ratio de Sharpe, drawdown maximum) et tests de significativité des résultats.",
                ],
            },
        ],
    },
    "Data_Science_IA": {
        "tagline": "Recherche d'un stage de 4-6 mois en Data Science / AI Engineer à partir de mars 2027",
        "competences": [
            ("Langages", "Python, SQL, Java, C, C++"),
            ("Machine Learning", "Scikit-Learn, apprentissage supervisé, Reinforcement Learning, évaluation de modèles"),
            ("LLM & NLP", "RAG, LangChain, embeddings, bases vectorielles (pgvector, ChromaDB), prompt engineering"),
            ("Computer Vision", "OpenCV, MediaPipe, détection et estimation de pose"),
            ("Data Engineering", "Pandas, NumPy, ETL, API REST (FastAPI), PostgreSQL, Google Sheets API"),
            ("Cloud & Déploiement", "Google Cloud Platform (APIs Gemini, Sheets, Gmail), Docker, conteneurisation et déploiement self-hosted, gestion d'authentification et de quotas API"),
            ("Outils", "Git, Linux, n8n, Jupyter"),
        ],
        "projets_majeurs": [
            {
                "titre": "Agent IA Connecté – Protocole MCP ",
                "dates": "Août 2026 - En cours",
                "bullets": [
                    "Agent conversationnel Python connecté via le protocole MCP à des sources hétérogènes (SaaS).",
                    "Traduction du langage naturel en appels d'outils structurés et génération automatisée de rapports d'insights.",
                    "Développement d'un serveur MCP exposant schémas de données et permissions d'accès.",
                ],
            },
            {
                "titre": "Automatisation Intelligente de Candidatures (n8n)",
                "dates": "Juillet 2026",
                "bullets": [
                    "Pipeline d'automatisation sous n8n (self-hosted) : ingestion d'offres (via API), normalisation, stockage et scoring de pertinence.",
                    "Génération de contenus personnalisés via LLM ; intégration Gmail API, logs d'audit et gestion d'erreurs.",
                ],
            },
            {
                "titre": "Bike Fit – Analyse Posturale par Computer Vision (Freelance)",
                "dates": "Juin 2026 - En cours",
                "bullets": [
                    "Logiciel Python modulaire : pipeline de pose (MediaPipe, OpenCV), extraction de landmarks et calcul d'angles articulaires, recommandations via LLM (Gemini) et rapports PDF.",
                    "En test auprès de vélocistes professionnels.",
                ],

            },
        ],
    },
}