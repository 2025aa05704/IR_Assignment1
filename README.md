# Information Retrieval System — Assignment 1 (Group 63)

An end-to-end Information Retrieval (IR) system built entirely with **Streamlit**.
The whole workflow — uploading a document collection, viewing it, preprocessing,
indexing, querying, phrase search, dictionary search and tolerant retrieval — runs
from the front end.

Course: Information Retrieval (AIMLCZG537 / DSECLZG537), S2-25.

---

## Features (mapped to the assignment tasks)

| Task | Where in the app |
|------|------------------|
| **A. Streamlit end-to-end workflow** | Sidebar (upload / options) + `Tab A` (view docs, ranked search, inverted index) |
| **B. Text preprocessing** | `Tab B` — tokenization, lowercasing, hyphen handling, stop-word removal, stemming, lemmatization, inverted-index creation, and a **stemming vs lemmatization** comparison |
| **C. Phrase queries** | `Tab C` — biword vs positional index, with false-positive detection |
| **D. Dictionary search** | `Tab D` — Binary Search Tree vs B-Tree benchmark (comparisons + timing table) |
| **E. Tolerant retrieval** | `Tab E` — wildcard, spelling correction (edit distance), k-gram index, phonetic (Soundex) |
| **G. Inference & discussion** | `Tab G` (in app) and `report/Report.md` |

---

## Project structure

```
Assignment1/
├── app.py                     # Streamlit front end (all sections)
├── ir_utils.py                # Core IR algorithms (preprocessing, indexes, trees, tolerant retrieval)
├── make_contribution.py       # Regenerates Group63_Contribution.xlsx
├── requirements.txt
├── README.md
├── data/                      # Sample document collection (12 .txt files)
├── report/
│   └── Report.md              # Detailed report + inferences (add screenshots here)
└── Group63_Contribution.xlsx  # Contribution sheet
```

---

## 1. Install dependencies

```bash
# (recommended) create a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# install requirements
pip install -r requirements.txt
```

> `nltk` is **optional**. If it is installed the app uses the full Porter stemmer
> and WordNet lemmatizer; otherwise it automatically uses the built-in fallbacks,
> so the app always runs (including offline / in the BITS virtual lab).
> The sidebar shows which engine is active.

To enable the NLTK WordNet lemmatizer the first run will try to download the
`wordnet` corpus automatically. If the lab blocks downloads, the fallback is used.

## 2. Run the app

```bash
streamlit run app.py
```

Then open the URL shown in the terminal (default `http://localhost:8501`).

---

## How to use

1. **Dataset** — the bundled sample collection loads automatically. You can also
   upload your own `.txt`/`.csv` files in the sidebar and click *Load uploaded*.
2. **Preprocessing options** — toggle lowercasing, stop-word removal, hyphen mode
   and normalization (none / stem / lemma) in the sidebar. Every tab respects these.
3. Explore each tab (A–E) and read the inferences in **Tab G**.

---

## Regenerating the contribution sheet

```bash
python make_contribution.py
```

Edit the `STUDENTS` list inside `make_contribution.py` to enter each member's
**Registration Number** and **Name** (all set to 100% contribution).

---

## Notes for the report / demo

- Take screenshots of each tab running in the BITS virtual lab and add them to
  `report/Report.md` (placeholders are marked there).
- The experimental tables (stemming vs lemmatization, BST vs B-Tree) are produced
  live by the app — screenshot them for the "Experimental results" section.
