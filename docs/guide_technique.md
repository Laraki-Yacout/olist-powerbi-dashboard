# Guide technique · Tableau de bord des ventes Olist

Le projet `Olist_Ventes.pbip` contient déjà tout ce qui suit. Ce guide sert de référence, et de plan B si le projet ne s'ouvre pas.

## 1. Problèmes détectés et traitement

| Constat | Impact | Traitement |
|---|---|---|
| 99 441 commandes, dont 96 478 livrées (97,0 %) | Les autres statuts ne sont pas des ventes abouties | Conservées : `delivered` uniquement |
| 2016 quasi vide : 267 commandes, aucun achat livré en novembre | La courbe suggérerait un faux départ à zéro | Courbe limitée à janv. 2017 – août 2018 ; 2016 reste dans les totaux |
| Fin de période : aucun achat livré après le 29/08/2018 | Août 2018 est légèrement incomplet | Conservé et signalé |
| Pas de nom de produit, seulement des identifiants | Top produits illisible | Libellé `catégorie · 8 premiers caractères de l'identifiant` |
| 610 produits sans catégorie, dont 584 vendus (R$ 170 726,63, soit 1,3 % du CA) | Catégorie vide | Valeur « Non renseignée » |
| 2 catégories sans traduction (13 produits) | Libellés manquants | Traduction ajoutée |
| 163 noms de ville présents dans plusieurs États | Villes homonymes fusionnées à tort | Libellé `Ville (UF)` |
| Un `customer_id` par commande | Compter ce champ surestime les clients | `customer_unique_id` : 93 358 clients uniques |
| 8 livraisons sans date, 61 livraisons datées avant l'approbation | Aucun, car la date de référence est l'achat | Conservées |
| Décimale avec un point dans les CSV | Erreurs possibles sur un Windows en français | Conversion forcée en `en-US` dans Power Query |
| Prix maximum R$ 6 735 | Valeur haute mais plausible | Conservée |

Aucun doublon de ligne ni aucune référence orpheline dans les jointures utilisées.

## 2. Données prêtes à importer

Les CSV propres sont dans `donnees/`. `scripts/preparer_donnees.py` les reproduit à partir des fichiers d'origine.

| Table | Lignes | Grain |
|---|---:|---|
| `Fait_Ventes` | 110 197 | Un article d'une commande livrée |
| `Dim_Produit` | 32 216 | Un produit vendu |
| `Dim_Client` | 96 478 | Un `customer_id` |
| `Dim_Date` | 1 096 | Un jour, de 2016 à 2018 |

## 3. Modèle en étoile

```
Dim_Date    1 ──▶ * Fait_Ventes * ◀── 1 Dim_Produit
                         *
                         ▲
                         1
                     Dim_Client
```

| De (plusieurs) | Vers (un) | Cardinalité | Filtrage |
|---|---|---|---|
| `Fait_Ventes[date_achat]` | `Dim_Date[date]` | *:1 | Unique, de la dimension vers le fait |
| `Fait_Ventes[product_id]` | `Dim_Produit[product_id]` | *:1 | Unique |
| `Fait_Ventes[customer_id]` | `Dim_Client[customer_id]` | *:1 | Unique |

Réglages : marquer `Dim_Date` comme table de dates sur `date`, trier `mois_libelle` par `mois_debut`, et désactiver « Date/heure automatique ». `customer_unique_id` est aussi dans le fait pour que le compte de clients réagisse aux filtres produit.

## 4. Mesures DAX

```dax
// Crée ces mesures dans la table Fait_Ventes.

// Format : "R$" #,0
Chiffre d'affaires =
SUM(Fait_Ventes[price])

// Format : #,0
Commandes =
DISTINCTCOUNT(Fait_Ventes[order_id])

// Format : "R$" #,0.00
Panier moyen =
DIVIDE([Chiffre d'affaires], [Commandes])

// Format : #,0
Clients uniques =
DISTINCTCOUNT(Fait_Ventes[customer_unique_id])

// Format : "R$" #,0
CA mensuel =
CALCULATE([Chiffre d'affaires], KEEPFILTERS(Dim_Date[annee] >= 2017))

// Format : 0.0%
Part du CA =
DIVIDE([Chiffre d'affaires], CALCULATE([Chiffre d'affaires], ALLSELECTED()))

// Format : "R$" #,0
CA Top 10 catégories =
VAR Rang =
    RANKX(ALLSELECTED(Dim_Produit[categorie_fr]), [Chiffre d'affaires], , DESC, Skip)
RETURN
    IF(NOT ISBLANK([Chiffre d'affaires]) && Rang <= 10, [Chiffre d'affaires])

// Format : "R$" #,0
CA Top 10 produits =
VAR Rang =
    RANKX(ALLSELECTED(Dim_Produit[produit_libelle]), [Chiffre d'affaires], , DESC, Skip)
RETURN
    IF(NOT ISBLANK([Chiffre d'affaires]) && Rang <= 10, [Chiffre d'affaires])

// Format : "R$" #,0
CA Top 10 villes =
VAR Rang =
    RANKX(ALLSELECTED(Dim_Client[ville_etat]), [Chiffre d'affaires], , DESC, Skip)
RETURN
    IF(NOT ISBLANK([Chiffre d'affaires]) && Rang <= 10, [Chiffre d'affaires])

// Format : "R$" #,0
CA Top 10 États =
VAR Rang =
    RANKX(ALLSELECTED(Dim_Client[etat_libelle]), [Chiffre d'affaires], , DESC, Skip)
RETURN
    IF(NOT ISBLANK([Chiffre d'affaires]) && Rang <= 10, [Chiffre d'affaires])
```

## 5. Maquette (page 1280 × 720, fond `#F3F5F8`)

| Zone | Visuel | Champs | x, y, largeur, hauteur | Titre |
|---|---|---|---|---|
| En-tête | Zone de texte | | 16, 14, 960, 50 | Tableau de bord des ventes e-commerce · Brésil |
| En-tête | Segment liste déroulante | `Dim_Date[annee]` | 1064, 14, 200, 50 | Année |
| KPI | Carte | Chiffre d'affaires | 16, 72, 300, 88 | |
| KPI | Carte | Commandes | 332, 72, 300, 88 | |
| KPI | Carte | Panier moyen | 648, 72, 300, 88 | |
| KPI | Carte | Clients uniques | 964, 72, 300, 88 | |
| Centre | Courbes | `mois_libelle`, CA mensuel | 16, 172, 827, 252 | Évolution mensuelle du chiffre d'affaires (janv. 2017 – août 2018) |
| Centre | Barres groupées | `categorie_fr`, CA Top 10 catégories | 858, 172, 406, 252 | Top 10 catégories par CA |
| Bas | Barres groupées | `produit_libelle`, CA Top 10 produits | 16, 436, 406, 248 | Top 10 produits par CA (noms absents de la source) |
| Bas | Barres groupées | `etat_libelle`, CA Top 10 États | 437, 436, 406, 248 | Top 10 États par CA |
| Bas | Barres groupées | `ville_etat`, CA Top 10 villes | 858, 436, 406, 248 | Top 10 villes par CA |
| Pied | Zone de texte | | 16, 690, 1248, 24 | Source et définition du CA |

Couleurs : marques `#1F5F8B`, texte `#1B2733`, texte secondaire `#5B6776`, cartes `#FFFFFF`, bordures `#DDE3EA`, grille `#E8ECF1`. Barres triées par CA décroissant, étiquettes en milliers.

Pas de carte géographique : des barres se lisent plus vite, et ce choix évite de dépendre des réglages de cartes de Power BI.

## 6. Chiffres de contrôle (page sans filtre)

| Indicateur | Valeur attendue |
|---|---:|
| Chiffre d'affaires | R$ 13 221 498,11 |
| Commandes | 96 478 |
| Panier moyen | R$ 137,04 |
| Clients uniques | 93 358 |
| Lignes de `Fait_Ventes` | 110 197 |
| Somme de la courbe | R$ 13 181 027,13 (96 211 commandes) |
| Frais de port exclus | R$ 2 202 965,54 |

| Année | CA (R$) | Commandes | Panier moyen (R$) | Clients uniques |
|---|---:|---:|---:|---:|
| 2016 | 40 470,98 | 267 | 151,58 | 264 |
| 2017 | 5 962 902,01 | 43 428 | 137,31 | 42 136 |
| 2018 | 7 218 125,12 | 52 783 | 136,75 | 51 612 |

| Mois | CA (R$) | Commandes |
|---|---:|---:|
| 2017-01 | 111 798,36 | 750 |
| 2017-02 | 234 223,40 | 1 653 |
| 2017-03 | 359 198,85 | 2 546 |
| 2017-04 | 340 669,68 | 2 303 |
| 2017-05 | 489 338,25 | 3 546 |
| 2017-06 | 421 923,37 | 3 135 |
| 2017-07 | 481 604,52 | 3 872 |
| 2017-08 | 554 699,70 | 4 193 |
| 2017-09 | 607 399,67 | 4 150 |
| 2017-10 | 648 247,65 | 4 478 |
| 2017-11 | 987 765,37 | 7 289 |
| 2017-12 | 726 033,19 | 5 513 |
| 2018-01 | 924 645,00 | 7 069 |
| 2018-02 | 826 437,13 | 6 555 |
| 2018-03 | 953 356,25 | 7 003 |
| 2018-04 | 973 534,09 | 6 798 |
| 2018-05 | 977 544,69 | 6 749 |
| 2018-06 | 856 077,86 | 6 099 |
| 2018-07 | 867 953,46 | 6 159 |
| 2018-08 | 838 576,64 | 6 351 |

| Catégorie | CA (R$) | Commandes |
|---|---:|---:|
| Beauté et santé | 1 233 131,72 | 8 647 |
| Montres et cadeaux | 1 166 176,98 | 5 495 |
| Linge de maison | 1 023 434,76 | 9 272 |
| Sport et loisirs | 954 852,55 | 7 530 |
| Accessoires informatiques | 888 724,61 | 6 530 |
| Meubles et décoration | 711 927,69 | 6 307 |
| Articles ménagers | 615 628,69 | 5 743 |
| Objets tendance | 610 204,10 | 3 559 |
| Automobile | 578 966,65 | 3 810 |
| Jouets | 471 286,48 | 3 804 |

| Produit | CA (R$) | Commandes |
|---|---:|---:|
| Beauté et santé · bb50f2e2 | 63 560,00 | 186 |
| Beauté et santé · 6cdd5384 | 53 652,30 | 148 |
| Ordinateurs · d6160fb7 | 45 949,35 | 33 |
| Access. informatiques · d1c42706 | 45 620,56 | 313 |
| Linge de maison · 99a4788c | 42 049,66 | 456 |
| Access. informatiques · 3dd2a171 | 40 782,80 | 253 |
| Bébé · 25c38557 | 38 907,32 | 38 |
| Objets tendance · 5f504b3a | 37 733,90 | 63 |
| Montres et cadeaux · 53b36df6 | 37 454,63 | 304 |
| Meubles et décoration · aca2eb7d | 37 104,30 | 425 |

| État | CA (R$) | Commandes |
|---|---:|---:|
| São Paulo (SP) | 5 067 633,16 | 40 501 |
| Rio de Janeiro (RJ) | 1 759 651,13 | 12 350 |
| Minas Gerais (MG) | 1 552 481,83 | 11 354 |
| Rio Grande do Sul (RS) | 728 897,47 | 5 345 |
| Paraná (PR) | 666 063,51 | 4 923 |
| Santa Catarina (SC) | 507 012,13 | 3 546 |
| Bahia (BA) | 493 584,14 | 3 256 |
| Distrito Federal (DF) | 296 498,41 | 2 080 |
| Goiás (GO) | 282 836,70 | 1 957 |
| Espírito Santo (ES) | 268 643,45 | 1 995 |

| Ville | CA (R$) | Commandes |
|---|---:|---:|
| São Paulo (SP) | 1 859 556,83 | 15 045 |
| Rio de Janeiro (RJ) | 955 573,97 | 6 601 |
| Belo Horizonte (MG) | 346 039,04 | 2 697 |
| Brasília (DF) | 295 814,72 | 2 071 |
| Curitiba (PR) | 205 999,33 | 1 489 |
| Campinas (SP) | 184 657,87 | 1 406 |
| Porto Alegre (RS) | 182 319,55 | 1 342 |
| Salvador (BA) | 173 273,05 | 1 188 |
| Guarulhos (SP) | 139 008,19 | 1 144 |
| Niterói (RJ) | 115 890,26 | 825 |

Ces chiffres sont aussi dans `chiffres_controle.csv`. Les clients uniques par année ne s'additionnent pas : un même client peut acheter sur deux années.

## 7. Plan B : reconstruire à la main (environ 20 min)

1. Accueil > Transformer les données > Gérer les paramètres : créer `DossierDonnees`, type Texte, valeur `C:\PBI_Olist\donnees\`.
2. Créer une requête vide par table et coller chaque bloc de `power_query.m` dans l'Éditeur avancé. Fermer et appliquer.
3. Créer les 3 relations de la section 3 et appliquer les réglages.
4. Coller les mesures de `mesures.dax` dans `Fait_Ventes`.
5. Placer les visuels de la section 5, puis comparer avec la section 6.
