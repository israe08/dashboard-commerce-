from dash import Dash, dcc, html, Input, Output, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from donnees import df, filtrer, calculer_kpis, mad
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "Atlas Commerce | Dashboard decisionnel"
DATE_MIN = df["Date"].min().date().isoformat()
DATE_MAX = df["Date"].max().date().isoformat()
# ZONE_FONCTIONS
def carte_kpi(titre, identifiant):
    """Construit une carte KPI reutilisable."""
    return dbc.Card(dbc.CardBody([
        html.Div(titre, className="kpi-label"),
        html.Div("--", id=identifiant, className="kpi-valeur")
    ]), className="kpi-card")
def carte_graphique(identifiant):
    """Construit une carte contenant un graphique Dash."""
    return dbc.Card(dbc.CardBody(
        dcc.Loading(dcc.Graph(id=identifiant))
    ), className="graph-card")
def figure_vide(titre):
    """Affiche un message pour les filtres sans ventes."""
    fig = go.Figure()
    fig.add_annotation(
        text="Aucune vente pour ces filtres",
        x=0.5, y=0.5, xref="paper", yref="paper",
        showarrow=False
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(title=titre, template="plotly_white", height=350)
    return fig
def harmoniser(fig):
        """Applique une hauteur et un fond communs aux figures."""
        fig.update_layout(
            template="plotly_white", height=360,
            margin=dict(l=25, r=20, t=60, b=35)
        )
        return fig
app.layout = dbc.Container([
    # ZONE_ENTETE
    html.Div([
        html.H1("ATLAS COMMERCE"),
        html.P("Pilotage des ventes | jeu de donnees fictif")
], className="bandeau"),
    # ZONE_FILTRES
        dbc.Card(
        dbc.CardBody(
            dbc.Row([
                dbc.Col([
                    html.Label("Periode", className="etiquette"),
                    dcc.DatePickerRange(
                        id="dates", start_date=DATE_MIN,
                        end_date=DATE_MAX,
                        min_date_allowed=DATE_MIN,
                        max_date_allowed=DATE_MAX,
                        display_format="DD/MM/YYYY"
                    )
                ], xs=12, lg=5),
                dbc.Col([
                    html.Label("Categorie", className="etiquette"),
                    dcc.Dropdown(
                        id="categorie", value="Toutes",
                        options=["Toutes"] + sorted(df["Categorie"].unique()),
                        clearable=False
                    )
                ], xs=12, lg=4),
                dbc.Col([
                    html.Label("Regroupement temporel", className="etiquette"),
                    dcc.RadioItems(
                        id="freq", value="M", inline=True,
                        options=[
                            {"label": "Jour", "value": "J"},
                            {"label": "Mois", "value": "M"}
                        ]
                    )], xs=12, lg=3),
            ], className="g-3")
        ), className="filter-card mb-3"
    ),
    # ZONE_KPIS
    dbc.Row([
    dbc.Col(carte_kpi("Chiffre d'affaires", "ca"), xs=12, sm=6, lg=3),
    dbc.Col(carte_kpi("Commandes distinctes", "commandes"), xs=12, sm=6, lg=3),
    dbc.Col(carte_kpi("Panier moyen", "panier"), xs=12, sm=6, lg=3),
    dbc.Col(carte_kpi("Marge commerciale", "marge"), xs=12, sm=6, lg=3),
    ], className="g-3 mb-4"),
    html.P(id="etat", className="text-muted"),
    # ZONE_EVOLUTION_UI
       dbc.Row([
        dbc.Col(carte_graphique("evolution"), xs=12)
    ], className="g-3 mb-4"),
    # ZONE_CATEGORIES_UI
        dbc.Row([
        dbc.Col(carte_graphique("categories"), xs=12)
    ], className="g-3 mb-4"),
    # ZONE_REGIONS_UI
        dbc.Row([
        dbc.Col(carte_graphique("regions"), xs=12)
    ], className="g-3 mb-4"),
    # ZONE_MARGES_UI
        dbc.Row([
        dbc.Col(carte_graphique("marges"), xs=12)
    ], className="g-3 mb-4"),
    # ZONE_TOP_UI
        dbc.Row([
        dbc.Col([
            html.H5(id="titre-top"),
            carte_graphique("top-produits")
        ], xs=12)
    ], className="g-3 mb-4"),
    dcc.Store(id="region-active", data=None),
    # ZONE_RESET_UI
        dbc.Row([
        dbc.Col(dbc.Button(
            "Effacer le filtre region", id="reset-region",
            color="outline-secondary", className="mb-3"
        ), xs=12)
    ]),
    # ZONE_MESSAGE_UI
    dbc.Alert(id="lecture-metier", color="info"),
], fluid=True, className="px-3 px-xl-5 py-4")
# ZONE_KPI_CALLBACK
@app.callback(
    Output("ca", "children"),
    Output("commandes", "children"),
    Output("panier", "children"),
    Output("marge", "children"),
    Output("etat", "children"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
    Input("categorie", "value")
)
def actualiser_kpis(debut, fin, categorie):
    ventes = filtrer(debut, fin, categorie)
    k = calculer_kpis(ventes)
    message = f"{len(ventes)} lignes | {k['commandes']} commandes"
    return (
        mad(k["ca"]), str(k["commandes"]),
        mad(k["panier"]), mad(k["marge"]), message
    )
# ZONE_EVOLUTION_CB
@app.callback(
    Output("evolution", "figure"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
    Input("categorie", "value"),
    Input("freq", "value")
)
def tracer_evolution(debut, fin, categorie, freq):
    ventes = filtrer(debut, fin, categorie)
    if ventes.empty:
        return figure_vide("Evolution du chiffre d'affaires")
    ventes["Periode"] = (
        ventes["Date"].dt.to_period("M").dt.to_timestamp()
        if freq == "M" else ventes["Date"]
    )
    evolution = (ventes.groupby("Periode", as_index=False)
                 ["Chiffre_Affaires"].sum().sort_values("Periode"))
    fig = px.line(
        evolution, x="Periode", y="Chiffre_Affaires",
        markers=True, title="Evolution du chiffre d'affaires",
        labels={"Chiffre_Affaires": "CA (MAD)"}
    )
    fig.update_traces(line_color="#682c55")
    return harmoniser(fig)
# ZONE_CATEGORIES_CB
@app.callback(
    Output("categories", "figure"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
    Input("categorie", "value")
)
def tracer_categories(debut, fin, categorie):
    ventes = filtrer(debut, fin, categorie)
    if ventes.empty:
        return figure_vide("CA par categorie")
    resume = (ventes.groupby("Categorie", as_index=False)
              ["Chiffre_Affaires"].sum()
              .sort_values("Chiffre_Affaires", ascending=False))
    fig = px.bar(
        resume, x="Categorie", y="Chiffre_Affaires",
        color="Categorie", title="CA par categorie"
    )
    fig.update_layout(showlegend=False)
    return harmoniser(fig)
# ZONE_REGIONS_CB
@app.callback(
    Output("regions", "figure"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
    Input("categorie", "value")
)
def tracer_regions(debut, fin, categorie):
    ventes = filtrer(debut, fin, categorie)
    if ventes.empty:
        return figure_vide("Part de chaque region")
    resume = (ventes.groupby("Region", as_index=False)
              ["Chiffre_Affaires"].sum())
    fig = px.pie(
        resume, names="Region", values="Chiffre_Affaires",
        title="Part de chaque region dans le CA", hole=0.40
    )
    fig.update_traces(textinfo="percent")
    return harmoniser(fig)
# ZONE_MARGES_CB
@app.callback(
    Output("marges", "figure"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
    Input("categorie", "value")
)
def tracer_marges(debut, fin, categorie):
    ventes = filtrer(debut, fin, categorie)
    if ventes.empty:
        return figure_vide("Marge par categorie")
    resume = (ventes.groupby("Categorie", as_index=False)
              ["Marge"].sum().sort_values("Marge", ascending=False))
    fig = px.bar(
        resume, x="Categorie", y="Marge", color="Categorie",
        title="Marge commerciale par categorie"
    )
    fig.update_layout(showlegend=False)
    return harmoniser(fig)
# ZONE_TOP_CB
@app.callback(
    Output("top-produits", "figure"),
    Output("titre-top", "children"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
    Input("categorie", "value"),
    Input("region-active", "data")
)
def tracer_top(debut, fin, categorie, region):
    ventes = filtrer(debut, fin, categorie)
    if region:
        ventes = ventes[ventes["Region"] == region].copy()
    titre = "Top produits" + (f" | {region}" if region else " | Toutes regions")
    if ventes.empty:
        return figure_vide(titre), titre
    resume = (ventes.groupby("Produit", as_index=False)
              ["Chiffre_Affaires"].sum()
              .nlargest(10, "Chiffre_Affaires")
              .sort_values("Chiffre_Affaires"))
    fig = px.bar(
        resume, x="Chiffre_Affaires", y="Produit",
        orientation="h", color="Chiffre_Affaires",
        color_continuous_scale="Blues"
    )
    fig.update_layout(coloraxis_showscale=False)
    return harmoniser(fig), titre
# ZONE_RESET_CB
@app.callback(
    Output("region-active", "data"),
    Input("regions", "clickData"),
    Input("reset-region", "n_clicks"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
    Input("categorie", "value"),
    prevent_initial_call=True
)
def selectionner_region(clic, _reset, _debut, _fin, _categorie):
    """Memorise le clic regional ; sinon efface le filtre local."""
    if ctx.triggered_id == "regions" and clic and clic.get("points"):
        return clic["points"][0].get("label")
    return None
# ZONE_MESSAGE_CB
@app.callback(
    Output("lecture-metier", "children"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
    Input("categorie", "value")
)
def recommandation_metier(debut, fin, categorie):
    ventes = filtrer(debut, fin, categorie)
    if ventes.empty:
        return "Aucune vente : elargissez la plage ou changez la categorie."
    par_region = ventes.groupby("Region")["Chiffre_Affaires"].sum()
    par_categorie = ventes.groupby("Categorie")["Marge"].sum()
    region = par_region.idxmax()
    cat = par_categorie.idxmax()
    return (f"Region au CA le plus eleve : {region}. "
            f"Categorie a la marge totale la plus forte : {cat}. "
            "Analyse sur les filtres courants, pas en temps reel.")
server = app.server

if __name__ == "__main__":
    app.run(debug=False)