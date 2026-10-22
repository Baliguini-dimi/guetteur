# Charte graphique et éditoriale

Projet : Guetteur, outil de surveillance de sécurité pour sites web.
Auteur : Dimitri Nelson Baliguini Demba. Version 1.0, à valider. Fichier prévu pour `docs/charte.md`.

## 1. Principe directeur

L'interface doit se lire comme un rapport d'audit bien composé. Le public principal est composé de banques et d'institutions : elles jugent le sérieux d'un outil à sa précision, à sa sobriété et à ce qu'il refuse de promettre. Chaque choix visuel doit servir la lecture de données ou la confiance. Ce qui ne sert ni l'un ni l'autre est retiré.

Trois règles dominent toutes les autres :
1. Le contenu réel (données, tableaux, rapports) fait l'essentiel du visuel.
2. Une seule couleur d'accent, des couleurs de gravité réservées aux gravités.
3. Aucun élément qui ressemble à un modèle générique ou à un rendu automatique.

## 2. Couleurs

**Thème clair (par défaut)**

| Rôle | Valeur | Usage |
|---|---|---|
| Fond de page | `#F7F6F3` | Arrière-plan général |
| Surface | `#FFFFFF` | Tableaux, blocs, formulaires |
| Bordure | `#D9D6CE` | Contours des blocs |
| Bordure légère | `#E6E3DC` | Séparateurs de lignes |
| Texte | `#1B1F23` | Texte principal |
| Texte secondaire | `#5B6470` | Légendes, en-têtes de colonnes |
| Accent | `#1F3A5F` | Liens, boutons principaux, navigation active |
| Accent au survol | `#162B48` | États de survol et d'appui |

**Gravités**

| Gravité | Valeur | Rendu |
|---|---|---|
| Critique | `#B42318` | Pastille pleine, texte blanc, en gras |
| Élevée | `#B54708` | Contour et texte, en gras |
| Moyenne | `#946A00` | Contour et texte, graisse normale |
| Faible | `#475467` | Contour gris, texte gris |

Une gravité ne se reconnaît jamais à la couleur seule. Elle porte toujours son libellé, et le rendu (pleine, contour gras, contour fin, grise) la distingue aussi pour les personnes qui perçoivent mal les couleurs.

**Règles**
- Les couleurs de gravité servent uniquement aux gravités. Aucun autre élément ne les utilise.
- Les quantités et les tendances d'un graphique utilisent l'accent, dans une seule teinte.
- Aucun dégradé, aucune transparence décorative, aucun effet de verre dépoli.
- Contraste minimal de 4,5 pour 1 pour le texte courant, 3 pour 1 à partir de 24 px. Les valeurs ci-dessus sont à recontrôler avec un outil avant la mise en production.

**Thème sombre (option, à valider avant développement)**

| Rôle | Valeur proposée |
|---|---|
| Fond | `#11161C` |
| Surface | `#171E26` |
| Bordure | `#2A3441` |
| Texte | `#E6E8EB` |
| Texte secondaire | `#9AA4B1` |
| Accent | `#8FB0DB` |

Les gravités sont éclaircies pour garder le contraste. Elles sont définies et testées au moment de l'implémentation du thème, pas avant.

## 3. Typographie

Deux familles chargées, rien d'autre.

- **Source Serif 4, graisse 600** : titres de niveau 1 à 3 et grands chiffres des indicateurs. Elle donne de l'autorité et distingue l'outil des interfaces habituelles.
- **IBM Plex Sans, graisses 400, 500, 600** : tout le reste de l'interface.
- **Police à chasse fixe du système** (`ui-monospace, Menlo, Consolas`) : adresses IP, chemins d'URL, identifiants techniques. Elle n'est pas téléchargée.
- Chiffres de largeur fixe (`font-variant-numeric: tabular-nums`) dans tous les tableaux et indicateurs, pour aligner les colonnes.
- Polices servies avec `font-display: swap` et limitées aux caractères latins nécessaires.

**Échelle**

| Usage | Taille | Interligne |
|---|---|---|
| Légende, en-tête de colonne | 12 px | 1,4 |
| Donnée technique (chasse fixe) | 13 px | 1,4 |
| Texte d'interface | 14 px | 1,45 |
| Texte de lecture (pages légales, rapports) | 16 px | 1,6 |
| Titre de niveau 3 | 19 px | 1,3 |
| Titre de niveau 2 | 24 px | 1,25 |
| Titre de niveau 1 | 30 px | 1,2 |
| Titre de page publique | 40 px | 1,15 |

Le serif n'est jamais utilisé dans les tableaux, les boutons ni les champs de formulaire.

## 4. Mise en page

- **Unité de base** : 4 px. Échelle d'espacement : 4, 8, 12, 16, 24, 32, 48.
- **Conteneur** : largeur maximale de 1200 px, marges latérales de 32 px (16 px sous 640 px).
- **Points de rupture** : 640, 960 et 1280 px. La mise en page est pensée d'abord pour le téléphone, puis élargie.
- **Coins** : 2 px pour les contrôles et les étiquettes, 0 pour les tableaux et les blocs.
- **Bordures** de 1 px à la place des ombres. Une ombre légère (`0 8px 24px rgba(27,31,35,.12)`) est réservée aux fenêtres superposées.
- **Hauteur des lignes de tableau** : 36 px en affichage compact, 44 px sur écran tactile.
- **Zones tactiles** : 44 px minimum de haut et de large.

## 5. Composants

**Bande de démonstration** : fond accent, texte blanc 13 px, texte « Démonstration : toutes les données sont fictives. » et bouton « Créer un compte ». Elle reste visible sur toutes les pages de la démo.

**Navigation** : fond blanc, bordure basse. Lien actif en accent, graisse 600, soulignement de 2 px. Pas d'icônes dans la navigation principale.

**Indicateurs (KPI)** : cellules accolées dans un bloc bordé. Libellé en 12 px gris, valeur en serif 28 px. Pas de flèches de tendance décoratives : une variation s'écrit en toutes lettres (« +12 par rapport à la semaine précédente »).

**Tableaux** : en-tête gris 12 px, lignes séparées par un filet léger, pas de lignes alternées en couleur, défilement horizontal dans le bloc sur petit écran. Colonnes numériques alignées à droite.

**Boutons**
- Principal : fond accent, texte blanc. Un seul par écran.
- Secondaire : fond blanc, bordure accent, texte accent.
- Destructif : fond critique, réservé aux suppressions définitives, avec confirmation.
- États : survol, focus visible (contour de 2 px en accent avec 2 px d'écart), désactivé, chargement (libellé conservé, bouton verrouillé).

**Formulaires** : libellé toujours visible au-dessus du champ, jamais seulement en texte indicatif. Aide sous le champ, erreur sous le champ en texte critique avec une phrase qui dit quoi corriger. Un champ de mot de passe permet d'afficher la saisie et le collage.

**Étiquettes de gravité et de statut** : 12 px, coins de 2 px, selon le tableau de la section 2. Les statuts sont : Nouveau, Vu, Traité, Faux positif.

**Rapport d'incident** : page de type document, titre en serif, tableau de synthèse en tête, puis Résumé, Chronologie, Recommandation. Numéro de référence en haut à droite. Exportable en PDF. Les adresses IP y sont partiellement masquées.

## 6. États obligatoires de chaque écran

- **Chargement** : squelette qui reprend la forme du contenu, en blocs `#E6E3DC`. Pas de roue plein écran. Animation limitée à un léger changement d'opacité, désactivée si l'utilisateur demande moins d'animations.
- **Vide** : une phrase qui explique pourquoi c'est vide et une action claire. Exemple : « Aucune alerte sur cette période. Les événements apparaîtront ici dès qu'une règle se déclenche. »
- **Erreur** : ce qui s'est passé, ce que la personne peut faire, un code de référence, un bouton « Réessayer ».
- **Session expirée** : invitation à se reconnecter, avec conservation de ce qui était saisi.
- **Page 404** : « Page introuvable », une phrase d'explication, lien vers le tableau de bord, code 404 affiché discrètement.
- **Page 500 et maintenance** : même composition que la 404, avec heure de reprise prévue si elle est connue.
- **Aucun écran blanc** : une barrière d'erreur globale affiche toujours un message sobre avec un code de référence.

## 7. Graphiques et cartes

- Barres et lignes plutôt que secteurs. Pas de diagramme en secteurs au-delà de trois parts. Jamais de 3D.
- Barres avec une base à zéro. Valeurs écrites directement sur ou à côté des éléments, légende réduite au minimum.
- Une seule teinte (accent) pour les quantités. Les couleurs de gravité servent uniquement à représenter des gravités.
- Quadrillage très léger, chiffres en largeur fixe.
- Origine géographique : tableau et barres par pays et par ville. Si une carte est ajoutée plus tard, elle est plate, en une seule teinte, sans décor. La mention « Localisation estimée à partir de l'adresse IP, donc approximative » accompagne toujours ces données.

## 8. Icônes et images

- Icônes rares, en trait de 1,5 px, tailles de 16 et 20 px (jeu Lucide). Le libellé texte passe avant l'icône. Une icône seule porte toujours un nom accessible.
- Aucun emoji dans l'interface, la documentation ou les emails.
- Pas de photos de banque d'images, pas d'illustrations décoratives, pas de logos de faux clients, pas de témoignages inventés.
- Les images de présentation sont des captures réelles de la démo.
- Logo : provisoire, le mot « Guetteur » en Source Serif 4 graisse 600 couleur accent. Favicon : monogramme simple de la lettre G.

## 9. Animation

- 120 à 160 ms, courbe `ease-out`, uniquement pour le survol, le focus et l'ouverture d'un panneau.
- Aucune animation d'entrée, aucun effet de défilement, aucune animation décorative.
- Respect de la préférence système « réduire les animations ».

## 10. Ton et rédaction

- Interface en français, **vouvoiement** (à valider). Phrases courtes, verbes d'action sur les boutons : « Créer un compte », « Exporter le rapport », « Marquer comme traité ».
- Dates en toutes lettres : « 16 octobre 2026 ». Heures sur 24 heures : « 14:32 ». Milliers séparés par une espace insécable : « 48 213 ». Virgule pour les décimales.
- Pas de point d'exclamation, pas d'emojis, pas de tirets cadratins, pas d'énumérations de trois adjectifs, pas de formules creuses (« puissant », « révolutionnaire », « boostez »).
- Les chiffres valent mieux que les adjectifs : « 126 tentatives en 9 minutes » plutôt que « une attaque massive ».
- Une erreur dit ce qui s'est passé et ce qu'on peut faire, sans reproche ni excès d'excuses.
- Libellés de gravité : Critique, Élevée, Moyenne, Faible. Libellés de statut : Nouveau, Vu, Traité, Faux positif.

| À éviter | À écrire |
|---|---|
| Oups, quelque chose s'est mal passé ! | La requête n'a pas abouti. Réessayez, ou contactez-nous avec le code ERR-4821. |
| Boostez votre sécurité dès aujourd'hui | Détectez les attaques courantes sur votre site et recevez une alerte par email. |
| Une menace critique vous guette | 2 alertes critiques à traiter. |

## 11. Démonstration et pages publiques

- La démo s'ouvre directement sur le tableau de bord d'une organisation fictive, sans inscription. Données synthétiques, adresses IP masquées, aucun vrai nom.
- La page d'accueil suit cet ordre : titre et sous-titre factuels avec une capture réelle ; boutons « Voir la démonstration » (principal) et « Créer un compte » (secondaire) ; tableau des attaques détectées avec leur gravité ; exemple de rapport d'incident ; page sécurité et données ; tarifs en tableau ; pied de page avec les pages légales.
- La page « Sécurité » n'affirme que ce qui est vrai à la date de publication : isolation des données, chiffrement, sauvegardes, politique de divulgation, date du dernier test d'intrusion quand il existe. Aucun logo de certification tant qu'elle n'est pas obtenue.
- Pages légales (confidentialité, conditions d'utilisation, mentions légales) en texte de lecture 16 px, largeur de ligne de 70 caractères maximum.

## 12. Accessibilité

- Contraste conforme WCAG AA, navigation complète au clavier, ordre de tabulation logique, focus toujours visible.
- Éléments interactifs en vrais boutons, liens et champs avec libellés. Aucune information portée par la couleur seule.
- Texte redimensionnable jusqu'à 200 % sans perte de contenu.
- Tableaux avec en-têtes de colonnes balisés.

## 13. Mise en œuvre

- Toutes les valeurs de ce document deviennent des variables CSS dans un fichier `tokens.css` (couleurs, tailles de texte, espacements, rayons). Aucune valeur de couleur ni de taille n'est écrite en dur dans les composants.
- Toute modification de la charte est notée dans `docs/decisions.md` avec sa raison.

## 14. Contrôle avant livraison d'un écran

1. Une seule couleur d'accent, aucune couleur de gravité hors gravités.
2. Aucun dégradé, aucune ombre décorative, aucun emoji.
3. Quatre états prévus : chargement, vide, erreur, session expirée.
4. Chiffres en largeur fixe dans les tableaux.
5. Contrastes vérifiés, focus visible, zones tactiles de 44 px.
6. Textes sans tirets cadratins, sans adjectifs creux, avec des chiffres précis.
7. Rien d'affiché au-delà de ce que le rôle de l'utilisateur permet de voir.
8. Aucune affirmation de sécurité que l'on ne peut pas prouver aujourd'hui.
