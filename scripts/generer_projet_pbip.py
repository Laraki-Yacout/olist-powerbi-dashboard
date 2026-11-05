#!/usr/bin/env python3
"""Génère le projet Power BI (.pbip) : modèle en étoile, mesures DAX et page unique.
Usage : python generer_projet_pbip.py <dossier_sortie> <theme_CY24SU10.json>"""
import json, sys, uuid, shutil
from pathlib import Path
OUT, THEME = Path(sys.argv[1]), Path(sys.argv[2])
NAME = "Olist_Ventes"
DOSSIER = "C:\\PBI_Olist\\donnees\\"
C = dict(fond="#F3F5F8", carte="#FFFFFF", bord="#DDE3EA", marque="#1F5F8B", texte="#1B2733", gris="#5B6776", grille="#E8ECF1")
SCH = "https://developer.microsoft.com/json-schemas/fabric"

def w(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    txt = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, indent=2)
    path.write_text(txt.replace("\r\n", "\n"), encoding="utf-8", newline="\n")

# ---------- Modèle ----------
TABLES = {
 "Fait_Ventes": [("order_id","string"),("order_item_id","int64"),("customer_id","string"),("customer_unique_id","string"),
                 ("product_id","string"),("date_achat","dateTime"),("price","decimal"),("freight_value","decimal")],
 "Dim_Produit": [("product_id","string"),("code_produit","string"),("produit_libelle","string"),("categorie_fr","string"),("categorie_en","string")],
 "Dim_Client":  [("customer_id","string"),("customer_unique_id","string"),("ville","string"),("uf","string"),("etat","string"),("ville_etat","string"),("etat_libelle","string")],
 "Dim_Date":    [("date","dateTime"),("annee","int64"),("mois_num","int64"),("mois_debut","dateTime"),("mois_libelle","string")],
}
HIDDEN = {"Fait_Ventes":{"order_id","order_item_id","customer_id","customer_unique_id","product_id","date_achat"},
          "Dim_Produit":{"product_id"},"Dim_Client":{"customer_id","customer_unique_id"},"Dim_Date":{"mois_num","mois_debut"}}
MTYPE = {"string":"type text","int64":"Int64.Type","dateTime":"type date","decimal":"Currency.Type"}

def m_query(t):
    cols = TABLES[t]
    typed = ", ".join('{"%s", %s}' % (n, MTYPE[d]) for n, d in cols)
    return ["let",
      f'    Source = Csv.Document(File.Contents(DossierDonnees & "{t}.csv"), [Delimiter=",", Columns={len(cols)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
      '    Entetes = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
      f'    Types = Table.TransformColumnTypes(Entetes, {{{typed}}}, "en-US")',
      "in", "    Types"]

def R(*lines): return list(lines)
MESURES = [
 ("Chiffre d'affaires", R("SUM(Fait_Ventes[price])"), '"R$" #,0'),
 ("Commandes", R("DISTINCTCOUNT(Fait_Ventes[order_id])"), "#,0"),
 ("Panier moyen", R("DIVIDE([Chiffre d'affaires], [Commandes])"), '"R$" #,0.00'),
 ("Clients uniques", R("DISTINCTCOUNT(Fait_Ventes[customer_unique_id])"), "#,0"),
 ("CA mensuel", R("CALCULATE([Chiffre d'affaires], KEEPFILTERS(Dim_Date[annee] >= 2017))"), '"R$" #,0'),
 ("Part du CA", R("DIVIDE([Chiffre d'affaires], CALCULATE([Chiffre d'affaires], ALLSELECTED()))"), "0.0%"),
]
def top(n, col):
    return (n, R("VAR Rang =", f"    RANKX(ALLSELECTED({col}), [Chiffre d'affaires], , DESC, Skip)", "RETURN",
                 "    IF(NOT ISBLANK([Chiffre d'affaires]) && Rang <= 10, [Chiffre d'affaires])"), '"R$" #,0')
MESURES += [top("CA Top 10 catégories","Dim_Produit[categorie_fr]"), top("CA Top 10 produits","Dim_Produit[produit_libelle]"),
            top("CA Top 10 villes","Dim_Client[ville_etat]"), top("CA Top 10 États","Dim_Client[etat_libelle]")]

def column(t, n, d):
    c = {"name":n,"dataType":d,"sourceColumn":n,"summarizeBy":"none","annotations":[{"name":"SummarizationSetBy","value":"Automatic"}]}
    if d == "dateTime": c["formatString"] = "yyyy-mm-dd"
    if d == "decimal": c["formatString"] = '"R$" #,0.00'; c["summarizeBy"] = "sum"
    if n in HIDDEN.get(t, ()): c["isHidden"] = True
    if (t, n) == ("Dim_Date","date"): c["isKey"] = True
    if (t, n) == ("Dim_Date","mois_libelle"): c["sortByColumn"] = "mois_debut"
    return c

tables = []
for t, cols in TABLES.items():
    o = {"name":t,"columns":[column(t,n,d) for n,d in cols],
         "partitions":[{"name":t,"mode":"import","source":{"type":"m","expression":m_query(t)}}],
         "annotations":[{"name":"PBI_ResultType","value":"Table"}]}
    if t == "Dim_Date": o["dataCategory"] = "Time"
    if t == "Fait_Ventes":
        o["measures"] = [{"name":n,"expression":e if len(e)>1 else e[0],"formatString":f} for n,e,f in MESURES]
    tables.append(o)

RELS = [("product_id","Dim_Produit","product_id"),("customer_id","Dim_Client","customer_id"),("date_achat","Dim_Date","date")]
bim = {"compatibilityLevel":1567,"model":{"culture":"en-US","defaultPowerBIDataSourceVersion":"powerBI_V3","sourceQueryCulture":"en-US",
  "dataAccessOptions":{"legacyRedirects":True,"returnErrorValuesAsNull":True},
  "tables":tables,
  "relationships":[{"name":str(uuid.uuid5(uuid.NAMESPACE_URL,a+b)),"fromTable":"Fait_Ventes","fromColumn":a,"toTable":b,"toColumn":c} for a,b,c in RELS],
  "expressions":[{"name":"DossierDonnees","kind":"m",
     "expression":json.dumps(DOSSIER)+' meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]',
     "annotations":[{"name":"PBI_ResultType","value":"Text"}]}],
  "annotations":[{"name":"PBI_ProTooling","value":'["DevMode"]'},{"name":"__PBI_TimeIntelligenceEnabled","value":"0"},
     {"name":"PBI_QueryOrder","value":json.dumps(["DossierDonnees",*TABLES])}]}}

SM, RP = OUT/f"{NAME}.SemanticModel", OUT/f"{NAME}.Report"
for p in (SM, RP):
    if p.exists(): shutil.rmtree(p)
PLAT = SCH+"/gitIntegration/platformProperties/2.0.0/schema.json"
w(SM/"model.bim", bim)
w(SM/"definition.pbism", {"$schema":SCH+"/item/semanticModel/definitionProperties/1.0.0/schema.json","version":"4.0","settings":{}})
w(SM/".platform", {"$schema":PLAT,"metadata":{"type":"SemanticModel","displayName":NAME},"config":{"version":"2.0","logicalId":str(uuid.uuid5(uuid.NAMESPACE_URL,NAME+"sm"))}})
w(RP/".platform", {"$schema":PLAT,"metadata":{"type":"Report","displayName":NAME},"config":{"version":"2.0","logicalId":str(uuid.uuid5(uuid.NAMESPACE_URL,NAME+"rp"))}})
w(RP/"definition.pbir", {"$schema":SCH+"/item/report/definitionProperties/2.0.0/schema.json","version":"4.0","datasetReference":{"byPath":{"path":f"../{NAME}.SemanticModel"}}})
w(OUT/f"{NAME}.pbip", {"$schema":SCH+"/pbip/pbipProperties/1.0.0/schema.json","version":"1.0","artifacts":[{"report":{"path":f"{NAME}.Report"}}],"settings":{"enableAutoRecovery":True}})
w(OUT/".gitignore", "**/.pbi/localSettings.json\n**/.pbi/cache.abf\ndonnees/*.csv\n")
(RP/"StaticResources/SharedResources/BaseThemes").mkdir(parents=True)
shutil.copy(THEME, RP/"StaticResources/SharedResources/BaseThemes/CY24SU10.json")

# ---------- Rapport ----------
D = RP/"definition"
V = SCH+"/item/report/definition"
w(D/"version.json", {"$schema":V+"/versionMetadata/1.0.0/schema.json","version":"2.0.0"})
def lit(v): return {"expr":{"Literal":{"Value":v}}}
def s(v): return lit("'"+v.replace("'","''")+"'")
def col(c): return {"solid":{"color":s(c)}}
w(D/"report.json", {"$schema":V+"/report/1.2.0/schema.json",
 "themeCollection":{"baseTheme":{"name":"CY24SU10","reportVersionAtImport":"5.59","type":"SharedResources"}},
 "layoutOptimization":"None",
 "objects":{"section":[{"properties":{"verticalAlignment":s("Top")}}]},
 "resourcePackages":[{"name":"SharedResources","type":"SharedResources","items":[{"name":"CY24SU10","path":"BaseThemes/CY24SU10.json","type":"BaseTheme"}]}],
 "settings":{"useStylableVisualContainerHeader":True,"defaultDrillFilterOtherVisuals":True,"allowChangeFilterTypes":True,"useDefaultAggregateDisplayName":True}})
PAGE = "tableau_de_bord_ventes"
w(D/"pages/pages.json", {"$schema":V+"/pagesMetadata/1.0.0/schema.json","pageOrder":[PAGE],"activePageName":PAGE})
w(D/f"pages/{PAGE}/page.json", {"$schema":V+"/page/1.2.0/schema.json","name":PAGE,"displayName":"Tableau de bord des ventes","displayOption":"FitToPage","height":720,"width":1280,
 "objects":{"background":[{"properties":{"color":col(C["fond"]),"transparency":lit("0D")}}],"outspace":[{"properties":{"color":col(C["fond"]),"transparency":lit("0D")}}]}})

def m(n): return {"Measure":{"Expression":{"SourceRef":{"Entity":"Fait_Ventes"}},"Property":n}}
def cl(t,n): return {"Column":{"Expression":{"SourceRef":{"Entity":t}},"Property":n}}
def pm(n, **k): return {"field":m(n),"queryRef":f"Fait_Ventes.{n}","nativeQueryRef":n, **k}
def pc(t,n, **k): return {"field":cl(t,n),"queryRef":f"{t}.{n}","nativeQueryRef":n,"active":True, **k}
def conteneur(titre, alt):
    o = {"general":[{"properties":{"altText":s(alt)}}],
         "background":[{"properties":{"show":lit("true"),"color":col(C["carte"]),"transparency":lit("0D")}}],
         "border":[{"properties":{"show":lit("true"),"color":col(C["bord"]),"radius":lit("8D"),"width":lit("1D")}}],
         "visualHeader":[{"properties":{"show":lit("false")}}]}
    o["title"] = [{"properties":{"show":lit("true"),"text":s(titre),"fontSize":lit("12D"),"bold":lit("true"),"fontColor":col(C["texte"]),"alignment":s("left")}}] if titre else [{"properties":{"show":lit("false")}}]
    return o
n = [0]
def visual(nom, x,y,wd,h, v):
    n[0]+=1
    w(D/f"pages/{PAGE}/visuals/{nom}/visual.json", {"$schema":V+"/visualContainer/1.3.0/schema.json","name":nom,
       "position":{"x":x,"y":y,"z":n[0]*100,"width":wd,"height":h,"tabOrder":n[0]*100},"visual":v})
def texte(nom,x,y,wd,h,paras,alt):
    visual(nom,x,y,wd,h,{"visualType":"textbox","objects":{"general":[{"properties":{"paragraphs":paras}}]},
      "visualContainerObjects":{"general":[{"properties":{"altText":s(alt)}}],"background":[{"properties":{"show":lit("false")}}],
                                "visualHeader":[{"properties":{"show":lit("false")}}]},"drillFilterOtherVisuals":True})
def carte(nom,x,mes,decimales,alt):
    visual(nom,x,72,300,88,{"visualType":"card","query":{"queryState":{"Values":{"projections":[pm(mes)]}}},
      "objects":{"labels":[{"properties":{"color":col(C["texte"]),"fontSize":lit("26D"),"labelDisplayUnits":lit("1D"),"labelPrecision":lit(f"{decimales}L")}}],
                 "categoryLabels":[{"properties":{"show":lit("true"),"color":col(C["gris"]),"fontSize":lit("11D")}}]},
      "visualContainerObjects":conteneur(None,alt),"drillFilterOtherVisuals":True})
def barres(nom,x,y,wd,h,titre,t,cc,mes,alt):
    visual(nom,x,y,wd,h,{"visualType":"barChart","query":{"queryState":{"Category":{"projections":[pc(t,cc)]},"Y":{"projections":[pm(mes)]}},
        "sortDefinition":{"sort":[{"field":m(mes),"direction":"Descending"}],"isDefaultSort":True}},
      "objects":{"dataPoint":[{"properties":{"fill":col(C["marque"])}}],
        "categoryAxis":[{"properties":{"showAxisTitle":lit("false"),"fontSize":lit("9D"),"labelColor":col(C["texte"]),"maxMarginFactor":lit("55L")}}],
        "valueAxis":[{"properties":{"show":lit("false"),"showAxisTitle":lit("false"),"gridlineShow":lit("false")}}],
        "labels":[{"properties":{"show":lit("true"),"labelDisplayUnits":lit("1000D"),"labelPrecision":lit("0L"),"fontSize":lit("9D"),"color":col(C["gris"])}}]},
      "visualContainerObjects":conteneur(titre,alt),"drillFilterOtherVisuals":True})

texte("titre",16,14,960,50,[
  {"textRuns":[{"value":"Tableau de bord des ventes e-commerce · Brésil","textStyle":{"fontWeight":"bold","fontSize":"20pt","color":C["texte"]}}]},
  {"textRuns":[{"value":"Démonstration sur données publiques Olist · commandes livrées, sept. 2016 – août 2018","textStyle":{"fontSize":"10pt","color":C["gris"]}}]}],
  "Titre du tableau de bord")
visual("filtre_annee",1064,14,200,50,{"visualType":"slicer","query":{"queryState":{"Values":{"projections":[pc("Dim_Date","annee",displayName="Année")]}}},
  "objects":{"data":[{"properties":{"mode":s("Dropdown")}}],"header":[{"properties":{"show":lit("true"),"fontColor":col(C["gris"]),"textSize":lit("10D")}}]},
  "visualContainerObjects":{"general":[{"properties":{"altText":s("Filtre par année")}}],"background":[{"properties":{"show":lit("false")}}],"visualHeader":[{"properties":{"show":lit("false")}}]},"drillFilterOtherVisuals":True})
carte("kpi_ca",16,"Chiffre d'affaires",0,"Chiffre d'affaires total en réais, hors frais de port")
carte("kpi_commandes",332,"Commandes",0,"Nombre de commandes livrées")
carte("kpi_panier",648,"Panier moyen",2,"Panier moyen par commande en réais")
carte("kpi_clients",964,"Clients uniques",0,"Nombre de clients uniques")
visual("courbe_ca_mensuel",16,172,827,252,{"visualType":"lineChart","query":{"queryState":{"Category":{"projections":[pc("Dim_Date","mois_libelle")]},"Y":{"projections":[pm("CA mensuel")]}},
    "sortDefinition":{"sort":[{"field":cl("Dim_Date","mois_libelle"),"direction":"Ascending"}],"isDefaultSort":True}},
  "objects":{"dataPoint":[{"properties":{"fill":col(C["marque"])}}],
    "lineStyles":[{"properties":{"strokeWidth":lit("2D"),"showMarker":lit("true"),"markerSize":lit("4D")}}],
    "categoryAxis":[{"properties":{"showAxisTitle":lit("false"),"fontSize":lit("9D"),"labelColor":col(C["gris"])}}],
    "valueAxis":[{"properties":{"showAxisTitle":lit("false"),"fontSize":lit("9D"),"labelColor":col(C["gris"]),"labelDisplayUnits":lit("1000D"),"gridlineColor":col(C["grille"])}}]},
  "visualContainerObjects":conteneur("Évolution mensuelle du chiffre d'affaires (janv. 2017 – août 2018)","Courbe du chiffre d'affaires par mois"),"drillFilterOtherVisuals":True})
barres("top_categories",858,172,406,252,"Top 10 catégories par CA","Dim_Produit","categorie_fr","CA Top 10 catégories","Dix catégories au plus fort chiffre d'affaires")
barres("top_produits",16,436,406,248,"Top 10 produits par CA (noms absents de la source)","Dim_Produit","produit_libelle","CA Top 10 produits","Dix produits au plus fort chiffre d'affaires")
barres("top_etats",437,436,406,248,"Top 10 États par CA","Dim_Client","etat_libelle","CA Top 10 États","Dix États au plus fort chiffre d'affaires")
barres("top_villes",858,436,406,248,"Top 10 villes par CA","Dim_Client","ville_etat","CA Top 10 villes","Dix villes au plus fort chiffre d'affaires")
texte("note_source",16,690,1248,24,[{"textRuns":[{"value":"Source : Olist, github.com/olist/work-at-olist-data · CA = somme des prix en réais (R$), hors frais de port · Date d'achat · Projet de démonstration, sans lien avec Olist.","textStyle":{"fontSize":"9pt","color":C["gris"]}}]}],"Note de source et de définition")
print("ok")
