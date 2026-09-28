<!--
Squelette de lettre de motivation.

Les blocs {{ ... }} sont remplis automatiquement. Les quatre paragraphes du corps sont
rédigés par le LLM :

  1. {{ pourquoi_entreprise }}     — l'entreprise et le poste, d'après l'offre
  2. {{ adequation_missions }}     — missions de l'offre face aux projets de selection.json
  3. {{ motivation_personnelle }}  — PROPOSITION à relire : le LLM ne connaît pas tes
                                     raisons réelles, il compose à partir du catalogue
  4. {{ apport_parcours }}         — PROPOSITION à relire : idem, à partir de ta formation
                                     et de tes expériences du catalogue

Les paragraphes 3 et 4 sont les seuls du pipeline qui ne se déduisent pas d'une donnée
vérifiable. Relis-les et réécris-les à ta main avant d'envoyer : c'est ce que tu devras
défendre en entretien.

L'adresse postale n'apparaît pas dans la lettre : nom, e-mail et téléphone suffisent.
-->
{{ contact_nom }}
{{ contact_email }} · {{ contact_tel }}

{{ entreprise }}
{{ lieu }}

{{ ville_expedition }}, le {{ date }}

**Objet : candidature — {{ poste }}**

Madame, Monsieur,

{{ pourquoi_entreprise }}

{{ adequation_missions }}

{{ motivation_personnelle }}

{{ apport_parcours }}

Je suis disponible pour un {{ disponibilite_duree }} {{ disponibilite_debut }}, et je reste à votre disposition pour en échanger.

Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations respectueuses.

{{ contact_nom }}
