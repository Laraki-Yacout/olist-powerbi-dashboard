#!/usr/bin/env python3
"""Prépare le modèle en étoile Olist pour Power BI.
Usage : python preparer_donnees.py <dossier_csv_bruts> <dossier_sortie>
Dépendance : pandas. Les CSV de sortie sont en UTF-8, séparateur virgule, décimale point."""
import sys
from pathlib import Path
import pandas as pd

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

ETATS = {"AC":"Acre","AL":"Alagoas","AM":"Amazonas","AP":"Amapá","BA":"Bahia","CE":"Ceará","DF":"Distrito Federal",
"ES":"Espírito Santo","GO":"Goiás","MA":"Maranhão","MG":"Minas Gerais","MS":"Mato Grosso do Sul","MT":"Mato Grosso",
"PA":"Pará","PB":"Paraíba","PE":"Pernambuco","PI":"Piauí","PR":"Paraná","RJ":"Rio de Janeiro","RN":"Rio Grande do Norte",
"RO":"Rondônia","RR":"Roraima","RS":"Rio Grande do Sul","SC":"Santa Catarina","SE":"Sergipe","SP":"São Paulo","TO":"Tocantins"}

CAT_FR = {"agro_industria_e_comercio":"Agro-industrie et commerce","alimentos":"Alimentation","alimentos_bebidas":"Alimentation et boissons",
"artes":"Art","artes_e_artesanato":"Art et artisanat","artigos_de_festas":"Articles de fête","artigos_de_natal":"Articles de Noël","audio":"Audio",
"automotivo":"Automobile","bebes":"Bébé","bebidas":"Boissons","beleza_saude":"Beauté et santé","brinquedos":"Jouets","cama_mesa_banho":"Linge de maison",
"casa_conforto":"Confort de la maison","casa_conforto_2":"Confort de la maison 2","casa_construcao":"Maison et construction","cds_dvds_musicais":"CD et DVD musicaux",
"cine_foto":"Cinéma et photo","climatizacao":"Climatisation","consoles_games":"Consoles et jeux vidéo","construcao_ferramentas_construcao":"Outils de construction",
"construcao_ferramentas_ferramentas":"Outillage","construcao_ferramentas_iluminacao":"Éclairage","construcao_ferramentas_jardim":"Outillage de jardin (construction)",
"construcao_ferramentas_seguranca":"Équipement de sécurité","cool_stuff":"Objets tendance","dvds_blu_ray":"DVD et Blu-ray","eletrodomesticos":"Électroménager",
"eletrodomesticos_2":"Électroménager 2","eletronicos":"Électronique","eletroportateis":"Petit électroménager","esporte_lazer":"Sport et loisirs",
"fashion_bolsas_e_acessorios":"Sacs et accessoires","fashion_calcados":"Chaussures","fashion_esporte":"Vêtements de sport","fashion_roupa_feminina":"Vêtements femme",
"fashion_roupa_infanto_juvenil":"Vêtements enfant","fashion_roupa_masculina":"Vêtements homme","fashion_underwear_e_moda_praia":"Sous-vêtements et plage",
"ferramentas_jardim":"Outils de jardin","flores":"Fleurs","fraldas_higiene":"Couches et hygiène","industria_comercio_e_negocios":"Industrie et commerce",
"informatica_acessorios":"Accessoires informatiques","instrumentos_musicais":"Instruments de musique","la_cuisine":"La Cuisine","livros_importados":"Livres importés",
"livros_interesse_geral":"Livres grand public","livros_tecnicos":"Livres techniques","malas_acessorios":"Bagagerie","market_place":"Marketplace",
"moveis_colchao_e_estofado":"Literie et rembourrage","moveis_cozinha_area_de_servico_jantar_e_jardim":"Meubles cuisine et jardin","moveis_decoracao":"Meubles et décoration",
"moveis_escritorio":"Mobilier de bureau","moveis_quarto":"Meubles de chambre","moveis_sala":"Meubles de salon","musica":"Musique","papelaria":"Papeterie",
"pcs":"Ordinateurs","perfumaria":"Parfumerie","pet_shop":"Animalerie","portateis_casa_forno_e_cafe":"Petits appareils four et café","relogios_presentes":"Montres et cadeaux",
"seguros_e_servicos":"Assurances et services","sinalizacao_e_seguranca":"Signalisation et sécurité","tablets_impressao_imagem":"Tablettes et impression",
"telefonia":"Téléphonie","telefonia_fixa":"Téléphonie fixe","utilidades_domesticas":"Articles ménagers",
# absentes du fichier de traduction
"pc_gamer":"PC gamer","portateis_cozinha_e_preparadores_de_alimentos":"Petits appareils de cuisine"}
CAT_EN_MANQUANT = {"pc_gamer":"pc_gamer","portateis_cozinha_e_preparadores_de_alimentos":"small_kitchen_appliances"}
NON_RENSEIGNEE = "Non renseignée"

VILLES_ACCENTS = {"Brasilia":"Brasília","Goiania":"Goiânia","Niteroi":"Niterói","Santo Andre":"Santo André",
                  "Belem":"Belém","Florianopolis":"Florianópolis","Vitoria":"Vitória","Maringa":"Maringá"}
MINUSCULES = {"de","do","da","dos","das","e"}

def ville_propre(v):
    mots = [m if m in MINUSCULES and n else m.capitalize() for n, m in enumerate(v.split())]
    r = " ".join(mots).replace("Sao ", "São ")
    return VILLES_ACCENTS.get(r, r)

orders = pd.read_csv(SRC/"olist_orders_dataset.csv", dtype=str)
items = pd.read_csv(SRC/"olist_order_items_dataset.csv", dtype={"order_id":str,"product_id":str,"seller_id":str})
customers = pd.read_csv(SRC/"olist_customers_dataset.csv", dtype=str)
products = pd.read_csv(SRC/"olist_products_dataset.csv", dtype=str)
trad = pd.read_csv(SRC/"product_category_name_translation.csv", encoding="utf-8-sig", dtype=str)

# --- Fait : une ligne par article d'une commande livrée
livrees = orders.loc[orders.order_status == "delivered", ["order_id","customer_id","order_purchase_timestamp"]]
fait = items.merge(livrees, on="order_id", how="inner", validate="m:1")\
            .merge(customers[["customer_id","customer_unique_id"]], on="customer_id", how="left", validate="m:1")
fait["date_achat"] = pd.to_datetime(fait.order_purchase_timestamp).dt.date
fait = fait[["order_id","order_item_id","customer_id","customer_unique_id","product_id","date_achat","price","freight_value"]]
fait = fait.sort_values(["date_achat","order_id","order_item_id"])

# --- Dimension produit (produits vendus uniquement)
p = products.loc[products.product_id.isin(fait.product_id), ["product_id","product_category_name"]].copy()
p = p.merge(trad, on="product_category_name", how="left", validate="m:1")
p["categorie_fr"] = p.product_category_name.map(CAT_FR).fillna(NON_RENSEIGNEE)
p["categorie_en"] = p.product_category_name_english.fillna(p.product_category_name.map(CAT_EN_MANQUANT)).fillna("not_informed")
assert not set(p.product_category_name.dropna()) - set(CAT_FR)
p["code_produit"] = p.product_id.str[:8]
assert p.code_produit.is_unique
p["produit_libelle"] = p.categorie_fr.replace({"Accessoires informatiques":"Access. informatiques"}) + " · " + p.code_produit
dim_p = p[["product_id","code_produit","produit_libelle","categorie_fr","categorie_en"]]

# --- Dimension client (grain customer_id = un identifiant par commande)
c = customers[customers.customer_id.isin(fait.customer_id)].copy()
c["ville"] = c.customer_city.map(ville_propre)
c["etat"] = c.customer_state.map(ETATS)
assert c.etat.notna().all()
c["ville_etat"] = c.ville + " (" + c.customer_state + ")"
c["etat_libelle"] = c.etat + " (" + c.customer_state + ")"
dim_c = c.rename(columns={"customer_state":"uf"})[["customer_id","customer_unique_id","ville","uf","etat","ville_etat","etat_libelle"]]

# --- Dimension date (années complètes, sans trou)
MOIS = ["janv.","févr.","mars","avr.","mai","juin","juil.","août","sept.","oct.","nov.","déc."]
d = pd.DataFrame({"ts": pd.date_range("2016-01-01","2018-12-31")})
dim_d = pd.DataFrame({"date": d.ts.dt.date, "annee": d.ts.dt.year, "mois_num": d.ts.dt.month,
    "mois_debut": d.ts.dt.to_period("M").dt.start_time.dt.date,
    "mois_libelle": d.ts.dt.month.map(lambda m: MOIS[m-1]) + " " + d.ts.dt.year.astype(str)})

assert fait.date_achat.isin(dim_d.date).all() and fait.product_id.isin(dim_p.product_id).all() and fait.customer_id.isin(dim_c.customer_id).all()
assert dim_p.product_id.is_unique and dim_c.customer_id.is_unique and dim_d.date.is_unique

fait.to_csv(OUT/"Fait_Ventes.csv", index=False, encoding="utf-8", float_format="%.2f", lineterminator="\n")
dim_p.to_csv(OUT/"Dim_Produit.csv", index=False, encoding="utf-8", lineterminator="\n")
dim_c.to_csv(OUT/"Dim_Client.csv", index=False, encoding="utf-8", lineterminator="\n")
dim_d.to_csv(OUT/"Dim_Date.csv", index=False, encoding="utf-8", lineterminator="\n")
for n, t in dict(Fait_Ventes=fait, Dim_Produit=dim_p, Dim_Client=dim_c, Dim_Date=dim_d).items():
    print(n, t.shape)
