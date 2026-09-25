<!--
Squelette de lettre de motivation.

Les blocs {{ ... }} sont remplis automatiquement :
  - {{ pourquoi_entreprise }} et {{ adequation_missions }} sont rédigés par le LLM à
    partir de l'offre et de la sélection ; ils ne citent que des projets et des
    compétences présents dans selection.json.
  - les autres viennent du catalogue ou de l'analyse de l'offre.

Les blocs [À REMPLIR PAR MARCEL] ne sont JAMAIS écrits automatiquement. Le rendu PDF
échoue tant qu'ils sont là : c'est voulu, ta motivation ne s'invente pas.
-->
{{ contact_nom }}
{{ contact_adresse }}
{{ contact_email }} · {{ contact_tel }}

{{ entreprise }}
{{ lieu }}

{{ ville_expedition }}, le {{ date }}

**Objet : candidature — {{ poste }}**

Madame, Monsieur,

{{ pourquoi_entreprise }}

{{ adequation_missions }}

[À REMPLIR PAR MARCEL : pourquoi ce métier et ces missions t'intéressent
personnellement. 2 ou 3 phrases, écrites par toi. Pas de formule creuse : une raison
concrète que tu peux défendre en entretien.]

[À REMPLIR PAR MARCEL : ce que ton parcours t'a apporté et que tu veux mettre en avant
ici — prépa, olympiades de mathématiques, ISIMA, Côte d'Ivoire, associatif. 2 ou 3
phrases.]

Je suis disponible pour un {{ disponibilite_duree }} {{ disponibilite_debut }}, et je
reste à votre disposition pour en échanger.

Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations respectueuses.

{{ contact_nom }}
