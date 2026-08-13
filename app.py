# streamlit run .ipynb_checkpoints/app.py
import streamlit as st
import requests

# =============================
# CONFIG
# =============================
API_BASE = "https://movie-rec-466x.onrender.com"
TMDB_IMG = "https://image.tmdb.org/t/p/w342"  # faster images
OMDB_API_KEY = "http://www.omdbapi.com/?i=tt3896198&apikey=696dada7"  # put your OMDb key
YOUTUBE = "https://www.youtube.com/embed/"

st.set_page_config(page_title="Movie Recommender", layout="wide")

# =============================
# STATE
# =============================
if "view" not in st.session_state:
    st.session_state.view = "home"
if "movie" not in st.session_state:
    st.session_state.movie = None
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

# =============================
# STYLES (subtle premium)
# =============================
st.markdown("""
<style>
.card {
    border: 1px solid rgba(0,0,0,0.08);
    border-radius: 14px;
    padding: 10px;
    transition: transform .18s ease, box-shadow .18s ease;
    background: rgba(255,255,255,0.7);
}
.card:hover {
    transform: translateY(-3px) scale(1.02);
    box-shadow: 0 8px 20px rgba(0,0,0,0.08);
}
.title {
    font-size: 0.9rem;
    line-height: 1.1rem;
    height: 2.2rem;
    overflow: hidden;
}
.badge {
    font-size: 0.75rem;
    background: #111827;
    color: white;
    padding: 2px 6px;
    border-radius: 6px;
    display: inline-block;
    margin-bottom: 4px;
}
.small-muted {
    color:#6b7280;
    font-size:0.85rem;
}
</style>
""", unsafe_allow_html=True)

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.markdown("## 🎬 Menu")

    if st.button("🏠 Home", use_container_width=True):
        st.session_state.view = "home"
        st.rerun()

    if st.button("❤️ Watchlist", use_container_width=True):
        st.session_state.view = "watchlist"
        st.rerun()

    st.markdown("---")

    st.markdown("### 🎬 Home Feed")
    home_category = st.selectbox(
        "Category",
        ["trending", "popular", "top_rated", "now_playing", "upcoming"],
        index=0,
    )

    grid_cols = st.slider("Grid", 4, 8, 6)

# =============================
# API (cached)
# =============================
@st.cache_data(ttl=60)
def api(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=15)
        if r.status_code >= 400:
            return {}
        return r.json()
    except:
        return {}

@st.cache_data(ttl=300)
def get_imdb(title):
    try:
        r = requests.get(f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}", timeout=10)
        return r.json().get("imdbRating", "N/A")
    except:
        return "N/A"

# =============================
# GRID
# =============================
def poster_grid(cards, cols=6, prefix="grid"):
    if not cards:
        st.info("😕 No movies found. Try another keyword.")
        return

    rows = (len(cards) + cols - 1) // cols
    i = 0

    for r in range(rows):
        cols_ui = st.columns(cols)
        for c_idx, col in enumerate(cols_ui):
            if i >= len(cards):
                break

            m = cards[i]
            unique_id = f"{prefix}_{r}_{c_idx}_{m.get('tmdb_id')}_{i}"
            i += 1

            with col:
                st.markdown("<div class='card'>", unsafe_allow_html=True)

                # ⭐ rating badge
                imdb = get_imdb(m.get("title"))
                st.markdown(f"<div class='badge'>⭐ {imdb}</div>", unsafe_allow_html=True)

                if m.get("poster_url"):
                    st.image(m.get("poster_url"), width="stretch")

                st.markdown(
                    f"<div class='title'>{m.get('title')}</div>",
                    unsafe_allow_html=True
                )

                a, b = st.columns(2)

                with a:
                    if st.button("Open", key=f"open_{unique_id}", use_container_width=True):
                        st.session_state.view = "details"
                        st.session_state.movie = m["tmdb_id"]
                        st.rerun()

                with b:
                    if st.button("❤️", key=f"fav_{unique_id}", use_container_width=True):
                        if m not in st.session_state.watchlist:
                            st.session_state.watchlist.append(m)

                st.markdown("</div>", unsafe_allow_html=True)

# =============================
# HOME
# =============================
if st.session_state.view == "home":

    st.title("🎬 Movie Recommender")

    typed = st.text_input("🔍 Search movie", placeholder="Type at least 2 characters...")

    # 🔍 Debounced search
    if typed and len(typed) >= 2:
        with st.spinner("Searching..."):
            data = api("/tmdb/search", {"query": typed})

        cards = []
        suggestions = []

        for m in data.get("results", []):
            if not m.get("title"):
                continue

            suggestions.append(m["title"])
            cards.append({
                "tmdb_id": m["id"],
                "title": m["title"],
                "poster_url": TMDB_IMG + m["poster_path"] if m.get("poster_path") else None
            })

        selected = st.selectbox("Suggestions", ["-- Select movie --"] + suggestions)

        if selected != "-- Select movie --":
            for m in cards:
                if m["title"] == selected:
                    st.session_state.movie = m["tmdb_id"]
                    st.session_state.view = "details"
                    st.rerun()

        poster_grid(cards, cols=grid_cols, prefix="search")

    elif typed and len(typed) < 2:
        st.caption("Type at least 2 characters...")

    else:
        st.subheader(f"🎬 {home_category.title()} Movies")

        with st.spinner("Loading movies..."):
            data = api("/home", {"category": home_category, "limit": 24})

        poster_grid(data, cols=grid_cols, prefix="home")

# =============================
# DETAILS
# =============================
elif st.session_state.view == "details":

    if st.button("← Back"):
        st.session_state.view = "home"
        st.rerun()

    data = api(f"/movie/id/{st.session_state.movie}")

    col1, col2 = st.columns([1,2])

    with col1:
        st.image(data.get("poster_url"), width="stretch")

        if st.button("❤️ Add to Watchlist"):
            movie_obj = {
                "tmdb_id": st.session_state.movie,
                "title": data.get("title"),
                "poster_url": data.get("poster_url")
            }
            if movie_obj not in st.session_state.watchlist:
                st.session_state.watchlist.append(movie_obj)

    with col2:
        st.header(data.get("title"))

        st.write(f"⭐ IMDB: {get_imdb(data.get('title'))}")

        genres = ", ".join([g["name"] for g in data.get("genres", [])])
        st.markdown(f"<div class='small-muted'>🎭 {genres}</div>", unsafe_allow_html=True)

        st.write(data.get("overview"))

    # 🎬 Trailer
    for v in data.get("videos", []):
        if v.get("site") == "YouTube":
            st.subheader("▶ Trailer")
            st.components.v1.html(
                f"<iframe width='100%' height='400' src='{YOUTUBE}{v['key']}'></iframe>",
                height=400
            )
            break

    # 🎯 Recommendations
    st.subheader("🎯 Recommended")
    rec = api("/recommend/genre", {"tmdb_id": st.session_state.movie})
    poster_grid(rec, cols=grid_cols, prefix="rec")

# =============================
# WATCHLIST
# =============================
elif st.session_state.view == "watchlist":

    st.title("❤️ Watchlist")

    if not st.session_state.watchlist:
        st.info("No saved movies")
    else:
        poster_grid(st.session_state.watchlist, cols=grid_cols, prefix="watchlist")

        if st.button("🗑 Clear"):
            st.session_state.watchlist = []