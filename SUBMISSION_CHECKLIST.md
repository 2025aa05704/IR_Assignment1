# Submission Checklist — Group 63 (IR Assignment 1)

Generated and auto-verified on 2026-05-31. Tick the manual items before zipping & submitting.

---

## A. Files included in this submission folder

| File / folder | Purpose | Status |
|---------------|---------|--------|
| `app.py` | Streamlit application (all sections A–E + G) | ✅ included, compiles |
| `ir_utils.py` | Core IR algorithms | ✅ included, compiles |
| `make_contribution.py` | Regenerates the contribution sheet | ✅ included, compiles |
| `requirements.txt` | Dependencies | ✅ included |
| `README.md` | Install steps + run command | ✅ included |
| `data/` (12 .txt docs) | Dataset / document collection | ✅ included (12 files) |
| `report/Report.md` | Report with inferences + screenshot slots | ✅ included |
| `Group63_Contribution.xlsx` | Contribution sheet (valid xlsx) | ✅ included, valid |
| `SUBMISSION_CHECKLIST.md` | This checklist | ✅ included |

---

## B. Assignment tasks — automated verification

| # | Task (rubric) | Marks | Implemented in | Verified |
|---|---------------|-------|----------------|----------|
| A | Streamlit end-to-end workflow (upload, view, query, options, outputs) | 1.0 | `app.py` Tab A + sidebar | ✅ app boots (HTTP 200), ranked search returns results |
| B | Text preprocessing (tokenize, lowercase, stop-words, hyphen, stem/lemma, inverted index) | 1.5 | `app.py` Tab B, `ir_utils.preprocess*` | ✅ 6 pipeline stages produced; inverted index built (263 terms) |
| B | Stemming vs lemmatization comparison + conclusion | 1.0 | `app.py` Tab B | ✅ vocab-reduction + Jaccard tables + auto conclusion |
| C | Phrase query: biword + positional index + false positives | 1.5 | `app.py` Tab C, `ir_utils.phrase_query_*` | ✅ both indexes return results; false-positive diff shown |
| D | Binary Search Tree vs B-Tree comparison (search/retrieval time table) | 1.5 | `app.py` Tab D, `ir_utils.benchmark_trees` | ✅ comparisons + timing table; BST h=16 vs B-Tree h=4 |
| E | Tolerant retrieval (wildcard, spelling, edit distance, k-gram, phonetic) | 1.5 | `app.py` Tab E, `ir_utils` | ✅ wildcard, edit-distance spell, k-gram, Soundex all work |
| G | Inference & discussion (compulsory) | 1.0 | `app.py` Tab G + `report/Report.md` | ✅ all 7 required questions answered |
| — | Virtual lab usage | 1.0 | (run on BITS lab) | ⬜ manual — see C below |
| | **Total** | **10** | | |

> Note: the rubric splits B into "Text preprocessing (1.5)" and "Stemming vs lemmatization (1.0)".

---

## C. Manual actions still required before submitting

- ⬜ **Fill student details**: open `make_contribution.py`, edit the `STUDENTS` list
  (each member's Registration Number + Name), then run `python make_contribution.py`
  to overwrite `Group63_Contribution.xlsx`. (Currently has placeholder rows at 100%.)
- ⬜ **Run on the BITS virtual lab** and confirm the app works there.
- ⬜ **Add screenshots** to `report/Report.md` at every `[SCREENSHOT: ...]` marker
  (home, Tab A search, Tab B stages + stem/lemma tables, Tab C results,
  Tab D benchmark, Tab E techniques, BITS lab terminal + browser).
- ⬜ (Optional) **Demo recording**: short screen recording of the app running.
- ⬜ (Optional) **Export report** to PDF/DOCX if the portal requires a document format.

---

## D. How to run (quick reference)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the URL shown in the terminal (default http://localhost:8501).

`nltk` is optional — the app uses built-in fallbacks if it is missing, so it runs
offline / in the virtual lab. The active engine is shown in the sidebar.

---

## E. Verification log (what was auto-tested)

```
all .py compile OK
A: docs=12  vocab=263  top=doc01_information_retrieval.txt  score=0.392
B: 6 preprocessing stages; stem('retrieving')=retriev, lemma=retrieving
C: biword=[0,1,3,5,9,10]  positional=[0,1,3,5,9,10]
D: terms=263  bst_height=16  btree_height=4
E: wildcard inform*=['inform']; spell 'retreival'->[('retrieval',2)]; soundex('retrievel')=R361
xlsx: valid (zip integrity OK)
Streamlit app: boots headless, HTTP 200
```
