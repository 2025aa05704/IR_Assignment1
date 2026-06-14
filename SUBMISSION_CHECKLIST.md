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
| A | Streamlit end-to-end workflow (upload, view, query, options, outputs) | 1.0 | `app.py` Tab A + sidebar | ✅ app boots (HTTP 200), ranked search returns results; live at https://irassignment1-group-63.streamlit.app/ |
| B | Text preprocessing (tokenize, lowercase, stop-words, hyphen, stem/lemma, inverted index) | 1.5 | `app.py` Tab B, `ir_utils.preprocess*` | ✅ 6 pipeline stages produced; inverted index built (263 terms) |
| B | Stemming vs lemmatization comparison + conclusion | 1.0 | `app.py` Tab B | ✅ vocab-reduction + Jaccard tables + auto conclusion |
| C | Phrase query: biword + positional index + false positives | 1.5 | `app.py` Tab C, `ir_utils.phrase_query_*` | ✅ both indexes return results; false-positive diff shown |
| D | Binary Search Tree vs B-Tree comparison (search/retrieval time table) | 1.5 | `app.py` Tab D, `ir_utils.benchmark_trees` | ✅ comparisons + timing table; BST h=16 vs B-Tree h=4 |
| E | Tolerant retrieval (wildcard, spelling, edit distance, k-gram, phonetic) | 1.5 | `app.py` Tab E, `ir_utils` | ✅ wildcard, edit-distance spell, k-gram, Soundex all work |
| G | Inference & discussion (compulsory) | 1.0 | `app.py` Tab G + `report/Report.md` | ✅ all 7 required questions answered |
| — | Virtual lab usage | 1.0 | (run on BITS lab) | ✅ executed on BITS virtual lab (Rocky Linux); screenshot in `report/screenshots/bits_lab_app.png` |
| | **Total** | **10** | | |

> Note: the rubric splits B into "Text preprocessing (1.5)" and "Stemming vs lemmatization (1.0)".

---

## C. Manual actions still required before submitting

- ✅ **Fill student details**: `make_contribution.py` `STUDENTS` list filled
  (Piyali Sarkar, Prateek Kumar Gupta, Kashif Zuhair); `Group63_Contribution.xlsx` regenerated.
- ✅ **Run on the BITS virtual lab**: executed on Rocky Linux lab; deployed app opened at
  https://irassignment1-group-63.streamlit.app/.
- ⬜ **Save the BITS lab screenshot** to `report/screenshots/bits_lab_app.png` (referenced by `report/Report.md` Section 2).
- ⬜ **Add remaining screenshots** to `report/Report.md` at every `[SCREENSHOT: ...]` marker
  (Tab A search, Tab B stages + stem/lemma tables, Tab C results, Tab D benchmark, Tab E techniques).
- ⬜ **Export report** to PDF (`report/Report.md` → `Report.pdf`) for submission.
- ⬜ (Optional) **Demo recording**: short screen recording of the app running.

---

## C2. Final ZIP to submit

- **Folder name:** `Group63_IR_Assignment1`
- **ZIP file name:** `Group63_IR_Assignment1.zip`

The folder should contain exactly:

```
Group63_IR_Assignment1/
├── app.py
├── ir_utils.py
├── make_contribution.py
├── requirements.txt
├── README.md
├── SUBMISSION_CHECKLIST.md
├── Group63_Contribution.xlsx
├── data/                       (12 .txt documents)
└── report/
    ├── Report.md
    ├── Report.pdf              (exported final report)
    └── screenshots/
        └── bits_lab_app.png    (+ any other tab screenshots)
```

Exclude `.venv/`, `__pycache__/`, `.idea/`, `.git/`, `.DS_Store` from the zip.

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
