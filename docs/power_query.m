// DossierDonnees : Accueil > Gérer les paramètres > Nouveau paramètre, type Texte, valeur C:\PBI_Olist\donnees\
// Puis une requête vide par bloc, avec le nom indiqué.

// ===== Fait_Ventes =====
let
    Source = Csv.Document(File.Contents(DossierDonnees & "Fait_Ventes.csv"), [Delimiter=",", Columns=8, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Entetes = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Types = Table.TransformColumnTypes(Entetes, {{"order_id", type text}, {"order_item_id", Int64.Type}, {"customer_id", type text}, {"customer_unique_id", type text}, {"product_id", type text}, {"date_achat", type date}, {"price", Currency.Type}, {"freight_value", Currency.Type}}, "en-US")
in
    Types

// ===== Dim_Produit =====
let
    Source = Csv.Document(File.Contents(DossierDonnees & "Dim_Produit.csv"), [Delimiter=",", Columns=5, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Entetes = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Types = Table.TransformColumnTypes(Entetes, {{"product_id", type text}, {"code_produit", type text}, {"produit_libelle", type text}, {"categorie_fr", type text}, {"categorie_en", type text}}, "en-US")
in
    Types

// ===== Dim_Client =====
let
    Source = Csv.Document(File.Contents(DossierDonnees & "Dim_Client.csv"), [Delimiter=",", Columns=7, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Entetes = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Types = Table.TransformColumnTypes(Entetes, {{"customer_id", type text}, {"customer_unique_id", type text}, {"ville", type text}, {"uf", type text}, {"etat", type text}, {"ville_etat", type text}, {"etat_libelle", type text}}, "en-US")
in
    Types

// ===== Dim_Date =====
let
    Source = Csv.Document(File.Contents(DossierDonnees & "Dim_Date.csv"), [Delimiter=",", Columns=5, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Entetes = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Types = Table.TransformColumnTypes(Entetes, {{"date", type date}, {"annee", Int64.Type}, {"mois_num", Int64.Type}, {"mois_debut", type date}, {"mois_libelle", type text}}, "en-US")
in
    Types
