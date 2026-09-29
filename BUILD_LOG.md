# Week 4 build log (raw notes)

Not a polished writeup — just the process trail for next week's report.

---

## Moment 1 — Four questions before any app code

**Prompt:** Answer Q1–Q4 on `movie_ratings.csv` (multi-genre handling, genre means, mean by release year, top 5 with floors 50 and 150), then plan a live Streamlit URL.

**First output:** Parsed the 100k-row file with the stdlib (pandas wasn't installed yet). Q1 treated unique rated movies, exploded `|` genres. Q2 used rating-level means. Q3 used release `year`, not `rating_year`. Q4 ranked per-movie means with n≥50 then n≥150.

**What changed:** Kept those definitions in the dashboard so the charts match the answers, not a second ad-hoc method. Installed pandas later for the app.

---

## Moment 2 — Chart type for genre breakdown

**Prompt (from the assignment, via the plan):** Direct the assistant to answer each question with a chart; watch for a default pie on ~18 genres.

**First instinct the model almost took:** a pie/donut for "distribution of genres."

**What changed and why:** Used a **sorted horizontal bar** instead. 19 tags (including `unknown`) are unreadable as a pie, and exploded multi-label counts are not a partition of 100% anyway (tags sum to 2,893 vs 1,682 movies).

---

## Moment 3 — Widgets and the Q4 floor

**Prompt:** At least 1–2 interactive controls; Q4 must show what happens when the floor goes from 50 to 150.

**First sketch:** only a floor slider.

**What changed:** Added a **release-year range** (so Q3's year axis is filterable and Q1–Q2 can be sliced) plus an optional **genre multiselect**. Q4 ranking still uses mean rating, ties broken by more ratings. Raising the floor drops Wallace & Gromit shorts; Schindler's List and Casablanca stay.
