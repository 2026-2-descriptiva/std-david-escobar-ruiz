"""Analisis bibliometrico de la literatura sobre PropTech (Scopus).

Lee data/scopus.csv.gz (resultado de la busqueda en data/search_string.txt)
y genera en submission/:

  Datos procesados
  - scopus.csv.gz: registros originales con las columnas derivadas
    `countries`, `authors_list` y `keywords` (listas separadas por "; ")

  Frecuencias (documentos y citas)
  - authors_frequency.csv, source_frequency.csv, country_frequency.csv,
    keywords_frequency.csv

  Co-ocurrencia y clusters
  - country_cooc_matrix.csv, keywords_cooc_matrix.csv: documentos en que
    aparecen juntos dos paises / dos palabras clave (la diagonal es la
    cantidad de documentos de cada uno)
  - country_clusters.txt, keywords_clusters.txt: comunidades de la red de
    co-ocurrencia (algoritmo de Louvain)

  Graficos interactivos (HTML, plotly)
  - documents_by_year.html, country_frequency_plot.html, world_map.html,
    country_cooc_heatmap.html, country_collab_network.html,
    keywords_cooc_network.html

Decisiones de limpieza:
  - Pais: ultimo elemento, separado por comas, de cada afiliacion; cada pais
    se cuenta una vez por documento. Se descartan los elementos que son
    organizaciones (contienen digitos, "University", "Ltd", ...) o siglas en
    mayusculas, y se unifican alias (USA, Viet Nam, Russian Federation).
  - Palabras clave: `Author Keywords` en minusculas, sin espacios repetidos;
    cada palabra se cuenta una vez por documento.
"""

import re
from itertools import combinations
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import plotly.graph_objects as go

FOLDER = Path(__file__).resolve().parents[1]
DATA_FILE = FOLDER / "data" / "scopus.csv.gz"
SUBMISSION_DIR = FOLDER / "submission"

TOP_COUNTRIES = 20
TOP_KEYWORDS = 40
SEED = 42

COUNTRY_ALIASES = {
    "USA": "United States",
    "UK": "United Kingdom",
    "UAE": "United Arab Emirates",
    "Viet Nam": "Vietnam",
    "Russian Federation": "Russia",
}
NOT_A_COUNTRY = re.compile(
    r"\d|universit|ltd|group|\binc\b|research|college|institut|washington|dubai",
    re.IGNORECASE,
)

# Paleta (ver skill dataviz): una sola serie en azul, rampa secuencial azul
# para magnitudes y orden categorico fijo para los clusters.
SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e4e3df"
SERIES_BLUE = "#2a78d6"
SEQUENTIAL_BLUES = [
    [0.0, "#cde2fb"],
    [0.25, "#86b6ef"],
    [0.5, "#2a78d6"],
    [0.75, "#184f95"],
    [1.0, "#0d366b"],
]
CATEGORICAL = [
    "#2a78d6",
    "#eb6834",
    "#1baf7a",
    "#eda100",
    "#e87ba4",
    "#008300",
    "#4a3aa7",
    "#e34948",
]
OTHER_GRAY = "#8c8b86"


# Preparacion de los datos
# -----------------------------------------------------------------------------


def split_list(text, sep=";"):
    if pd.isna(text):
        return []
    return [item.strip() for item in str(text).split(sep) if item.strip()]


def unique(items):
    return list(dict.fromkeys(items))


def extract_countries(affiliations):
    countries = []
    for affiliation in split_list(affiliations):
        token = affiliation.split(",")[-1].strip()
        token = COUNTRY_ALIASES.get(token, token)
        if not token or NOT_A_COUNTRY.search(token):
            continue
        if token.isupper():
            continue
        countries.append(token)
    return unique(countries)


def extract_keywords(keywords):
    return unique(
        re.sub(r"\s+", " ", keyword.lower()) for keyword in split_list(keywords)
    )


def load_data(data_file=DATA_FILE):
    df = pd.read_csv(data_file)
    df["Cited by"] = df["Cited by"].fillna(0).astype(int)
    df["countries"] = df["Affiliations"].map(extract_countries)
    df["authors_list"] = df["Authors"].map(lambda text: unique(split_list(text)))
    df["keywords"] = df["Author Keywords"].map(extract_keywords)
    return df


def save_processed(df):
    processed = df.copy()
    for column in ["countries", "authors_list", "keywords"]:
        processed[column] = processed[column].map("; ".join)
    processed.to_csv(SUBMISSION_DIR / "scopus.csv.gz", index=False, compression="gzip")


# Frecuencias
# -----------------------------------------------------------------------------


def frequency(df, column, name):
    exploded = df[[column, "Cited by"]].explode(column).dropna(subset=[column])
    table = (
        exploded.groupby(column)
        .agg(num_documents=("Cited by", "size"), global_citations=("Cited by", "sum"))
        .reset_index()
        .rename(columns={column: name})
    )
    return table.sort_values(
        ["num_documents", "global_citations", name],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def source_frequency(df):
    sources = df.assign(source=df["Source title"].map(lambda s: [s] if pd.notna(s) else []))
    return frequency(sources, "source", "source_title")


# Co-ocurrencia y clusters
# -----------------------------------------------------------------------------


def cooccurrence_matrix(lists, items):
    index = {item: i for i, item in enumerate(items)}
    matrix = np.zeros((len(items), len(items)), dtype=int)
    for document_items in lists:
        present = sorted({index[item] for item in document_items if item in index})
        for i in present:
            matrix[i, i] += 1
        for i, j in combinations(present, 2):
            matrix[i, j] += 1
            matrix[j, i] += 1
    return pd.DataFrame(matrix, index=items, columns=items)


def build_graph(matrix):
    graph = nx.Graph()
    for item in matrix.index:
        graph.add_node(item, documents=int(matrix.loc[item, item]))
    for a, b in combinations(matrix.index, 2):
        weight = int(matrix.loc[a, b])
        if weight > 0:
            graph.add_edge(a, b, weight=weight)
    return graph


def find_clusters(graph):
    """Comunidades de Louvain ordenadas por tamanio; los nodos aislados
    quedan cada uno en su propio cluster."""
    communities = nx.community.louvain_communities(graph, weight="weight", seed=SEED)
    communities = sorted(
        communities,
        key=lambda c: (-len(c), -sum(graph.nodes[n]["documents"] for n in c)),
    )
    return [
        sorted(c, key=lambda n: (-graph.nodes[n]["documents"], n)) for c in communities
    ]


def write_clusters(graph, clusters, output_file, label):
    lines = [f"Clusters de la red de co-ocurrencia de {label} (Louvain)", ""]
    for number, members in enumerate(clusters, start=1):
        lines.append(f"Cluster {number} (n = {len(members)}):")
        for member in members:
            lines.append(f"  - {member} ({graph.nodes[member]['documents']} documentos)")
        lines.append("")
    output_file.write_text("\n".join(lines), encoding="utf-8")


# Graficos
# -----------------------------------------------------------------------------


def base_layout(title, **kwargs):
    return dict(
        title=dict(text=title, x=0, xanchor="left", font=dict(color=TEXT_PRIMARY)),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(color=TEXT_SECONDARY),
        margin=dict(l=60, r=30, t=70, b=50),
        **kwargs,
    )


def save_figure(figure, name):
    figure.write_html(SUBMISSION_DIR / name, include_plotlyjs="cdn")


def plot_documents_by_year(df):
    by_year = df["Year"].value_counts().sort_index()
    figure = go.Figure(
        go.Bar(
            x=by_year.index,
            y=by_year.values,
            marker=dict(color=SERIES_BLUE, cornerradius=4),
            hovertemplate="%{x}: %{y} documentos<extra></extra>",
        )
    )
    figure.update_layout(
        **base_layout(
            "Documentos por año",
            xaxis=dict(title="Año"),
            yaxis=dict(title="Documentos", gridcolor=GRID),
            bargap=0.15,
        )
    )
    save_figure(figure, "documents_by_year.html")


def plot_country_frequency(countries, n=TOP_COUNTRIES):
    top = countries.head(n).iloc[::-1]
    figure = go.Figure(
        go.Bar(
            x=top["num_documents"],
            y=top["country"],
            orientation="h",
            marker=dict(color=SERIES_BLUE, cornerradius=4),
            text=top["num_documents"],
            textposition="outside",
            customdata=top["global_citations"],
            hovertemplate=(
                "%{y}: %{x} documentos, %{customdata} citas<extra></extra>"
            ),
        )
    )
    figure.update_layout(
        **base_layout(
            f"Documentos por país (top {n})",
            xaxis=dict(title="Documentos", gridcolor=GRID),
            height=650,
        )
    )
    save_figure(figure, "country_frequency_plot.html")


def plot_world_map(countries):
    figure = go.Figure(
        go.Choropleth(
            locations=countries["country"],
            locationmode="country names",
            z=countries["num_documents"],
            colorscale=SEQUENTIAL_BLUES,
            marker_line_color=SURFACE,
            marker_line_width=0.5,
            colorbar=dict(title="Documentos"),
            hovertemplate="%{location}: %{z} documentos<extra></extra>",
        )
    )
    figure.update_layout(
        **base_layout("Producción científica por país"),
        geo=dict(
            showframe=False,
            showcoastlines=False,
            projection_type="natural earth",
            bgcolor=SURFACE,
            landcolor="#f0efec",
            showland=True,
        ),
    )
    save_figure(figure, "world_map.html")


def plot_cooc_heatmap(matrix):
    values = matrix.to_numpy(dtype=float)
    np.fill_diagonal(values, np.nan)  # la diagonal no es co-ocurrencia
    figure = go.Figure(
        go.Heatmap(
            z=values,
            x=matrix.columns,
            y=matrix.index,
            colorscale=SEQUENTIAL_BLUES,
            xgap=2,
            ygap=2,
            colorbar=dict(title="Documentos"),
            hovertemplate="%{y} – %{x}: %{z} documentos<extra></extra>",
        )
    )
    figure.update_layout(
        **base_layout(
            "Co-ocurrencia de países (documentos en coautoría)",
            yaxis=dict(autorange="reversed"),
            height=750,
        )
    )
    save_figure(figure, "country_cooc_heatmap.html")


def plot_network(graph, clusters, title, name):
    pos = nx.spring_layout(graph, weight="weight", k=0.6, seed=SEED)
    cluster_of = {
        node: number for number, members in enumerate(clusters) for node in members
    }

    traces = []

    # Aristas agrupadas en tres grosores segun su peso
    weights = [data["weight"] for _, _, data in graph.edges(data=True)]
    if weights:
        cuts = np.quantile(weights, [1 / 3, 2 / 3])
        for width, low, high in [
            (0.6, -np.inf, cuts[0]),
            (1.4, cuts[0], cuts[1]),
            (2.4, cuts[1], np.inf),
        ]:
            xs, ys = [], []
            for a, b, data in graph.edges(data=True):
                if low < data["weight"] <= high:
                    xs += [pos[a][0], pos[b][0], None]
                    ys += [pos[a][1], pos[b][1], None]
            traces.append(
                go.Scatter(
                    x=xs,
                    y=ys,
                    mode="lines",
                    line=dict(width=width, color="#c3c2b7"),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

    # Nodos: un trace por cluster (max. 8 colores; el resto en "Otros")
    max_documents = max(graph.nodes[n]["documents"] for n in graph.nodes)
    other = len(CATEGORICAL)
    groups = {}
    for node in graph.nodes:
        groups.setdefault(min(cluster_of[node], other), []).append(node)

    for key, nodes in sorted(groups.items()):
        color = OTHER_GRAY if key == other else CATEGORICAL[key]
        label = "Otros clusters" if key == other else f"Cluster {key + 1}"
        documents = [graph.nodes[n]["documents"] for n in nodes]
        traces.append(
            go.Scatter(
                x=[pos[n][0] for n in nodes],
                y=[pos[n][1] for n in nodes],
                mode="markers+text",
                name=label,
                text=nodes,
                textposition="top center",
                textfont=dict(size=10, color=TEXT_PRIMARY),
                marker=dict(
                    size=[10 + 30 * np.sqrt(d / max_documents) for d in documents],
                    color=color,
                    line=dict(color=SURFACE, width=2),
                ),
                customdata=documents,
                hovertemplate="%{text}<br>%{customdata} documentos<extra>"
                + label
                + "</extra>",
            )
        )

    figure = go.Figure(traces)
    figure.update_layout(
        **base_layout(
            title,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=750,
            legend=dict(orientation="h", y=-0.05),
        )
    )
    save_figure(figure, name)


# Proceso principal
# -----------------------------------------------------------------------------


def main():
    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data()
    save_processed(df)

    countries = frequency(df, "countries", "country")
    keywords = frequency(df, "keywords", "keyword")
    frequency(df, "authors_list", "author").to_csv(
        SUBMISSION_DIR / "authors_frequency.csv", index=False
    )
    source_frequency(df).to_csv(SUBMISSION_DIR / "source_frequency.csv", index=False)
    countries.to_csv(SUBMISSION_DIR / "country_frequency.csv", index=False)
    keywords.to_csv(SUBMISSION_DIR / "keywords_frequency.csv", index=False)

    plot_documents_by_year(df)
    plot_country_frequency(countries)
    plot_world_map(countries)

    # Paises
    top_countries = countries["country"].head(TOP_COUNTRIES).tolist()
    country_matrix = cooccurrence_matrix(df["countries"], top_countries)
    country_matrix.to_csv(SUBMISSION_DIR / "country_cooc_matrix.csv")
    country_graph = build_graph(country_matrix)
    country_clusters = find_clusters(country_graph)
    write_clusters(
        country_graph,
        country_clusters,
        SUBMISSION_DIR / "country_clusters.txt",
        "paises",
    )
    plot_cooc_heatmap(country_matrix)
    plot_network(
        country_graph,
        country_clusters,
        f"Red de colaboración entre países (top {TOP_COUNTRIES})",
        "country_collab_network.html",
    )

    # Palabras clave
    top_keywords = keywords["keyword"].head(TOP_KEYWORDS).tolist()
    keyword_matrix = cooccurrence_matrix(df["keywords"], top_keywords)
    keyword_matrix.to_csv(SUBMISSION_DIR / "keywords_cooc_matrix.csv")
    keyword_graph = build_graph(keyword_matrix)
    keyword_clusters = find_clusters(keyword_graph)
    write_clusters(
        keyword_graph,
        keyword_clusters,
        SUBMISSION_DIR / "keywords_clusters.txt",
        "palabras clave",
    )
    plot_network(
        keyword_graph,
        keyword_clusters,
        f"Red de co-ocurrencia de palabras clave (top {TOP_KEYWORDS})",
        "keywords_cooc_network.html",
    )


if __name__ == "__main__":
    main()
