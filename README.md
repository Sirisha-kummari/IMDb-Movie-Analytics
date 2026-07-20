# 🎬 IMDb Movie Analytics

Final Individual Project — **Data Visualization · Summer 2026**

An analysis of ~10,000 films exploring what drives a movie's success — budget, genre, timing, or critical acclaim — with an interactive Streamlit dashboard.

## Key findings
- **Small budgets win on efficiency:** films under $1M return ~27× their budget, while $200M+ blockbusters barely break even.
- **Acclaim ≠ box office:** rating and revenue are nearly unrelated overall, but the link grows strong for big-budget films.
- **Genres have diversified** from an early Drama/Adventure core into a broad modern mix.

## Live dashboard
👉 https://imdb-movie-analytics-uqxfgls6f7fgcofjeczubu.streamlit.app/

## Project structure
├── app.py # Streamlit dashboard
├── requirements.txt # dependencies
└── dataset/
└── imdb_movies.csv # the data
## Run locally
​```
pip install -r requirements.txt
streamlit run app.py
​```

## Tools
Python · pandas · Plotly · Streamlit. Charts use a colour-vision-deficiency-safe (Okabe–Ito) palette.
