"""MovieLens ratings dashboard (Week 4)."""

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).parent / "data" / "movie_ratings.csv"


@st.cache_data
def load_ratings() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    df["genres"] = df["genres"].fillna("unknown").astype(str)
    return df


@st.cache_data
def unique_movies(ratings: pd.DataFrame) -> pd.DataFrame:
    return (
        ratings.sort_values("movie_id")
        .drop_duplicates(subset=["movie_id"])
        [["movie_id", "title", "year", "genres"]]
        .reset_index(drop=True)
    )


def explode_genres(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["genre"] = out["genres"].str.split("|")
    out = out.explode("genre")
    out["genre"] = out["genre"].str.strip()
    return out[out["genre"].ne("")]


def bar_h(data: pd.DataFrame, x: str, y: str, x_title: str, tooltip: list[str]) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(x, title=x_title),
            y=alt.Y(y, sort="-x", title=None),
            tooltip=tooltip,
        )
        .properties(height=alt.Step(28))
    )


st.set_page_config(page_title="MovieLens Dashboard", layout="wide")
st.title("MovieLens Ratings Dashboard")
st.caption(
    "MovieLens 100K-style ratings. Multi-genre movies are split on `|` and counted "
    "once per tag (explode). Q1 uses unique rated movies; Q2–Q3 use ratings."
)

ratings = load_ratings()
movies = unique_movies(ratings)

year_min = int(ratings["year"].min())
year_max = int(ratings["year"].max())

st.sidebar.header("Filters")
year_lo, year_hi = st.sidebar.slider(
    "Release year range",
    min_value=year_min,
    max_value=year_max,
    value=(year_min, year_max),
)
floor = st.sidebar.slider(
    "Minimum ratings (Q4 floor)",
    min_value=50,
    max_value=250,
    value=50,
    step=10,
)

ratings_f = ratings[(ratings["year"] >= year_lo) & (ratings["year"] <= year_hi)]
movies_f = movies[(movies["year"] >= year_lo) & (movies["year"] <= year_hi)]

all_genres = sorted(explode_genres(movies)["genre"].unique())
selected_genres = st.sidebar.multiselect(
    "Genres (Q1–Q2 highlight; empty = all)",
    options=all_genres,
    default=[],
)

c1, c2, c3 = st.columns(3)
c1.metric("Ratings in range", f"{len(ratings_f):,}")
c2.metric("Movies in range", f"{movies_f['movie_id'].nunique():,}")
c3.metric("Mean rating", f"{ratings_f['rating'].mean():.2f}" if len(ratings_f) else "—")

# --- Q1 ---
st.header("Q1. Genre breakdown")
st.markdown(
    "Among **movies that were rated**, how are genres distributed? "
    "A film tagged `Action|Comedy` counts once for Action and once for Comedy. "
    "Each movie counts once regardless of how many ratings it has."
)

genre_movies = explode_genres(movies_f)
q1 = (
    genre_movies.groupby("genre", as_index=False)["movie_id"]
    .nunique()
    .rename(columns={"movie_id": "n_movies"})
    .sort_values("n_movies", ascending=False)
)
q1["share_pct"] = 100 * q1["n_movies"] / movies_f["movie_id"].nunique()
if selected_genres:
    q1_chart = q1[q1["genre"].isin(selected_genres)]
else:
    q1_chart = q1

st.altair_chart(
    bar_h(
        q1_chart,
        x="n_movies:Q",
        y="genre:N",
        x_title="Rated movies",
        tooltip=["genre", "n_movies", alt.Tooltip("share_pct:Q", format=".1f", title="% of movies")],
    ),
    use_container_width=True,
)

# --- Q2 ---
st.header("Q2. Genre satisfaction")
st.markdown(
    "Mean of **individual ratings** for movies tagged with each genre "
    "(the same explode rule). Highest and lowest genres are called out below."
)

genre_ratings = explode_genres(ratings_f)
q2 = (
    genre_ratings.groupby("genre", as_index=False)
    .agg(mean_rating=("rating", "mean"), n_ratings=("rating", "size"))
    .sort_values("mean_rating", ascending=False)
)
if selected_genres:
    q2_chart = q2[q2["genre"].isin(selected_genres)]
else:
    q2_chart = q2

usable = q2[q2["genre"] != "unknown"]
if len(usable):
    hi = usable.iloc[0]
    lo = usable.iloc[-1]
    hicol, locol = st.columns(2)
    hicol.success(f"Highest: **{hi['genre']}** ({hi['mean_rating']:.3f}, n={int(hi['n_ratings']):,})")
    locol.warning(f"Lowest: **{lo['genre']}** ({lo['mean_rating']:.3f}, n={int(lo['n_ratings']):,})")

st.altair_chart(
    bar_h(
        q2_chart,
        x="mean_rating:Q",
        y="genre:N",
        x_title="Mean rating",
        tooltip=["genre", alt.Tooltip("mean_rating:Q", format=".3f"), "n_ratings"],
    ),
    use_container_width=True,
)

# --- Q3 ---
st.header("Q3. Mean rating by release year")
st.markdown(
    "Trend uses **movie release year**, not the year the rating was submitted. "
    "Sparse early years make the line jumpy; 1990s titles dominate this dataset."
)

q3 = (
    ratings_f.groupby("year", as_index=False)
    .agg(mean_rating=("rating", "mean"), n_ratings=("rating", "size"))
    .sort_values("year")
)
line = (
    alt.Chart(q3)
    .mark_line(point=True)
    .encode(
        x=alt.X("year:Q", title="Release year"),
        y=alt.Y("mean_rating:Q", title="Mean rating", scale=alt.Scale(zero=False)),
        tooltip=["year", alt.Tooltip("mean_rating:Q", format=".3f"), "n_ratings"],
    )
    .properties(height=360)
)
st.altair_chart(line, use_container_width=True)

# --- Q4 ---
st.header("Q4. Best-rated movies with a count floor")
st.markdown(
    f"Only movies with **at least {floor} ratings** in the selected year range. "
    "Ranked by mean rating; ties broken by more ratings. Raise the floor to 150 to "
    "see Wallace & Gromit-style shorts drop out."
)

movie_stats = (
    ratings_f.groupby(["movie_id", "title", "year"], as_index=False)
    .agg(mean_rating=("rating", "mean"), n_ratings=("rating", "size"))
)
eligible = movie_stats[movie_stats["n_ratings"] >= floor].sort_values(
    ["mean_rating", "n_ratings"],
    ascending=[False, False],
)
top5 = eligible.head(5).copy()
top5["label"] = top5.apply(
    lambda r: f"{r['title']} ({int(r['year'])}, n={int(r['n_ratings'])})",
    axis=1,
)

st.caption(f"{len(eligible):,} movies meet the floor of {floor} in this year range.")
if len(top5) == 0:
    st.info("No movies meet this floor in the current year range. Widen years or lower the floor.")
else:
    st.altair_chart(
        bar_h(
            top5,
            x="mean_rating:Q",
            y="label:N",
            x_title="Mean rating",
            tooltip=["title", "year", alt.Tooltip("mean_rating:Q", format=".3f"), "n_ratings"],
        ),
        use_container_width=True,
    )
    table = top5[["title", "year", "mean_rating", "n_ratings"]].reset_index(drop=True)
    table["mean_rating"] = table["mean_rating"].round(3)
    st.dataframe(table, use_container_width=True, hide_index=True)
