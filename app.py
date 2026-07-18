import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Movies Dashboard", page_icon="🎬", layout="wide")

OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#D55E00",
             "#56B4E9", "#CC79A7", "#F0E442", "#000000"]
HIGHLIGHT = "#0072B2"
GREY = "#BDBDBD"
DATA_PATH = "dataset/imdb_movies.csv"
TIER_LABELS = ["<1M", "1–10M", "10–50M", "50–100M", "100–200M", ">200M"]


def style_fig(fig, title, subtitle=None, h=430):
    full = f"<b>{title}</b>"
    if subtitle:
        full += f"<br><span style='font-size:12px;color:#666'>{subtitle}</span>"
    fig.update_layout(
        title=dict(text=full, x=0.01, xanchor="left"),
        template="plotly_white",
        font=dict(family="Arial", size=13, color="#222"),
        margin=dict(t=80, r=20, b=50, l=70),
        height=h, plot_bgcolor="white",
    )
    fig.update_xaxes(showgrid=False, zeroline=False, showline=True, linecolor="#ccc")
    fig.update_yaxes(showgrid=True, gridcolor="#eee", zeroline=False)
    return fig


@st.cache_data
def load_and_clean(path):
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={"names": "title", "date_x": "release_date", "score": "rating",
                            "orig_lang": "language", "budget_x": "budget"})
    df["release_date"] = pd.to_datetime(df["release_date"], format="mixed", errors="coerce")
    df["year"] = df["release_date"].dt.year
    df["month"] = df["release_date"].dt.month
    for c in ["rating", "budget", "revenue"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df.loc[df["budget"] == 0, "budget"] = np.nan
    df.loc[df["revenue"] == 0, "revenue"] = np.nan
    df["profit"] = df["revenue"] - df["budget"]
    df["roi"] = df["revenue"] / df["budget"]
    for c in ["genre", "language", "country", "status"]:
        df[c] = df[c].astype("string").str.strip()
    df["budget_tier"] = pd.cut(df["budget"],
                               bins=[0, 1e6, 1e7, 5e7, 1e8, 2e8, np.inf],
                               labels=TIER_LABELS)
    df["lang_group"] = np.where(df["language"].str.lower() == "english",
                                "English", "Non-English")
    return df


@st.cache_data
def explode_genre(df):
    g = df.assign(genre=df["genre"].str.split(",")).explode("genre")
    g["genre"] = g["genre"].str.strip()
    return g[g["genre"].notna() & (g["genre"] != "")]


try:
    df = load_and_clean(DATA_PATH)
except FileNotFoundError:
    st.error(f"Could not find `{DATA_PATH}`. Make sure imdb_movies.csv is in the dataset/ folder.")
    st.stop()

genre_df = explode_genre(df)

st.sidebar.header("🔎 Filters")
yr_min, yr_max = int(df["year"].min()), int(df["year"].max())
yr_lo, yr_hi = st.sidebar.slider("Release year", yr_min, yr_max, (1990, yr_max))
lang_choice = st.sidebar.radio("Language", ["All", "English", "Non-English"])
all_genres = sorted(genre_df["genre"].dropna().unique().tolist())
default_genres = [g for g in ["Drama", "Action", "Comedy", "Animation", "Documentary"] if g in all_genres]
picked = st.sidebar.multiselect("Genres (for genre charts)", all_genres, default=default_genres)

mask = df["year"].between(yr_lo, yr_hi)
if lang_choice != "All":
    mask &= df["lang_group"].eq(lang_choice)
fdf = df[mask]

gmask = genre_df["year"].between(yr_lo, yr_hi)
if lang_choice != "All":
    gmask &= genre_df["lang_group"].eq(lang_choice)
if picked:
    gmask &= genre_df["genre"].isin(picked)
fgdf = genre_df[gmask]

st.title("🎬 Movies: Money, Ratings & Genres")
st.markdown("#### What actually drives a film's success — budget, genre, timing, or acclaim?")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Films in view", f"{len(fdf):,}")
c2.metric("Median rating", f"{fdf['rating'].median():.0f}")
med_roi = fdf["roi"].median()
c3.metric("Median ROI", f"{med_roi:.1f}×" if pd.notna(med_roi) else "—")
med_bud = fdf["budget"].median()
c4.metric("Median budget", f"${med_bud/1e6:.0f}M" if pd.notna(med_bud) else "—")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(
    ["💰 Budget & returns", "⭐ Ratings vs money", "🎭 Genres & time", "🧭 Explore"])

with tab1:
    left, right = st.columns(2)
    with left:
        t = (fdf.dropna(subset=["roi"])
                .groupby("budget_tier", observed=True)["roi"].median().reset_index())
        if len(t):
            peak = t["roi"].idxmax()
            colors = [HIGHLIGHT if i == peak else GREY for i in range(len(t))]
            fig = go.Figure(go.Bar(x=t["budget_tier"].astype(str), y=t["roi"],
                                   marker_color=colors, text=t["roi"].round(1),
                                   textposition="outside"))
            fig.update_xaxes(title="Budget tier (USD)")
            fig.update_yaxes(title="Median ROI (revenue ÷ budget)")
            st.plotly_chart(style_fig(fig, "Small-budget films return the most per dollar",
                                      "Median return within each budget tier"),
                            use_container_width=True)
    with right:
        q = fdf.dropna(subset=["budget", "revenue"])
        fig = px.scatter(q, x="budget", y="revenue", color="rating",
                         color_continuous_scale="Viridis", hover_name="title")
        fig.update_traces(marker=dict(size=6, opacity=0.5))
        fig.update_xaxes(title="Budget (USD)")
        fig.update_yaxes(title="Revenue (USD)")
        st.plotly_chart(style_fig(fig, "Bigger budgets tend to earn more — not guaranteed",
                                  "Each dot is a film · colour = rating"),
                        use_container_width=True)
    st.info("💡 Cheap films win on efficiency (highest return per dollar); "
            "blockbusters win on scale (biggest absolute revenue).")

with tab2:
    q = fdf.dropna(subset=["rating", "revenue", "budget_tier"])
    fig = px.scatter(q, x="rating", y="revenue", color="budget_tier",
                     hover_name="title", color_discrete_sequence=OKABE_ITO,
                     category_orders={"budget_tier": TIER_LABELS})
    fig.update_traces(marker=dict(size=6, opacity=0.5))
    fig.update_xaxes(title="Rating")
    fig.update_yaxes(title="Revenue (USD)")
    st.plotly_chart(style_fig(fig, "Good reviews convert to money mainly for big-budget films",
                              "Rating vs revenue · colour = budget tier", h=520),
                    use_container_width=True)
    st.info("💡 Rating and revenue are nearly unrelated for cheap films, "
            "but the link grows strong for the biggest-budget movies.")

with tab3:
    left, right = st.columns(2)
    with left:
        r = (fgdf.dropna(subset=["roi"])
                 .groupby("genre")["roi"].median().sort_values(ascending=False).reset_index())
        if len(r):
            colors = [HIGHLIGHT if i == 0 else GREY for i in range(len(r))]
            fig = go.Figure(go.Bar(x=r["roi"], y=r["genre"], orientation="h",
                                   marker_color=colors, text=r["roi"].round(1),
                                   textposition="outside"))
            fig.update_yaxes(autorange="reversed", title="")
            fig.update_xaxes(title="Median ROI")
            st.plotly_chart(style_fig(fig, "Which selected genres return the most",
                                      "Median revenue ÷ budget, by genre"),
                            use_container_width=True)
        else:
            st.warning("Pick at least one genre in the sidebar.")
    with right:
        s = fgdf.dropna(subset=["year"]).copy()
        if len(s):
            s["decade"] = (s["year"] // 10) * 10
            counts = s.groupby(["decade", "genre"], observed=True).size().reset_index(name="n")
            counts["share"] = counts["n"] / counts.groupby("decade")["n"].transform("sum")
            fig = px.area(counts, x="decade", y="share", color="genre",
                          color_discrete_sequence=OKABE_ITO)
            fig.update_yaxes(title="Share of releases", tickformat=".0%")
            fig.update_xaxes(title="Decade")
            st.plotly_chart(style_fig(fig, "How the selected genres' share has shifted",
                                      "Within each decade"),
                            use_container_width=True)

with tab4:
    st.markdown("Build your own view — pick any two numeric measures.")
    num_cols = {"Rating": "rating", "Budget": "budget", "Revenue": "revenue",
                "ROI": "roi", "Profit": "profit", "Year": "year"}
    a, b, cc = st.columns(3)
    x_lab = a.selectbox("X axis", list(num_cols), index=1)
    y_lab = b.selectbox("Y axis", list(num_cols), index=2)
    color_by = cc.selectbox("Colour by", ["budget_tier", "lang_group", "none"], index=0)
    x, y = num_cols[x_lab], num_cols[y_lab]
    q = fdf.dropna(subset=[x, y])
    kwargs = dict(hover_name="title")
    if color_by != "none":
        kwargs["color"] = color_by
        kwargs["color_discrete_sequence"] = OKABE_ITO
    fig = px.scatter(q, x=x, y=y, **kwargs)
    fig.update_traces(marker=dict(size=6, opacity=0.5))
    fig.update_xaxes(title=x_lab)
    fig.update_yaxes(title=y_lab)
    st.plotly_chart(style_fig(fig, f"{y_lab} vs {x_lab}", h=520), use_container_width=True)

st.caption("Data: IMDB Movies (Kaggle) · Built with Streamlit + Plotly · CVD-safe Okabe–Ito palette")