"""
Information Retrieval System - Assignment 1 (Group 63)
======================================================
An end-to-end IR system built entirely with Streamlit. The complete workflow
-- upload, view, preprocess, index, query and tolerant retrieval -- runs from
this front end.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import ir_utils as ir

st.set_page_config(page_title="IR System - Group 63", page_icon="🔎", layout="wide")


# --------------------------------------------------------------------------- #
# Session-state helpers
# --------------------------------------------------------------------------- #
def _init_state() -> None:
    if "doc_names" not in st.session_state:
        names, contents = ir.load_default_docs()
        st.session_state.doc_names = names
        st.session_state.doc_texts = contents


_init_state()


def current_settings() -> dict:
    return {
        "lowercase": st.session_state.get("opt_lower", True),
        "remove_stopwords": st.session_state.get("opt_stop", True),
        "hyphen_mode": st.session_state.get("opt_hyphen", "split"),
        "normalization": st.session_state.get("opt_norm", "stem"),
    }


def build_index(normalization: str | None = None) -> ir.IRIndex:
    s = current_settings()
    if normalization is not None:
        s["normalization"] = normalization
    doc_tokens = [
        ir.preprocess(text, s["lowercase"], s["remove_stopwords"],
                      s["hyphen_mode"], s["normalization"])
        for text in st.session_state.doc_texts
    ]
    return ir.IRIndex(st.session_state.doc_names, doc_tokens)


def query_tokens(query: str, normalization: str | None = None) -> list[str]:
    s = current_settings()
    norm = normalization if normalization is not None else s["normalization"]
    return ir.preprocess(query, s["lowercase"], s["remove_stopwords"],
                         s["hyphen_mode"], norm)


# --------------------------------------------------------------------------- #
# Sidebar: dataset upload + preprocessing options (Section A controls)
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.title("🔎 IR System")
    st.caption("Group 63 - Assignment 1")

    st.header("1. Dataset")
    uploaded = st.file_uploader(
        "Upload documents (.txt / .csv)",
        type=["txt", "csv"],
        accept_multiple_files=True,
    )
    col_a, col_b = st.columns(2)
    if col_a.button("Load uploaded", use_container_width=True) and uploaded:
        names, texts = [], []
        for uf in uploaded:
            raw = uf.read().decode("utf-8", errors="ignore")
            if uf.name.lower().endswith(".csv"):
                # Treat every non-empty cell / row as a document line.
                import io
                df = pd.read_csv(io.StringIO(raw))
                text_col = df.select_dtypes(include="object")
                joined = text_col.astype(str).agg(" ".join, axis=1) if not text_col.empty else df.astype(str).agg(" ".join, axis=1)
                for i, line in enumerate(joined.tolist()):
                    names.append(f"{uf.name}#row{i+1}")
                    texts.append(line)
            else:
                names.append(uf.name)
                texts.append(raw)
        if names:
            st.session_state.doc_names = names
            st.session_state.doc_texts = texts
            st.success(f"Loaded {len(names)} documents.")

    if col_b.button("Reset to sample", use_container_width=True):
        names, contents = ir.load_default_docs()
        st.session_state.doc_names = names
        st.session_state.doc_texts = contents
        st.success("Sample dataset restored.")

    st.divider()
    st.header("2. Preprocessing options")
    st.checkbox("Lowercasing", value=True, key="opt_lower")
    st.checkbox("Stop-word removal", value=True, key="opt_stop")
    st.selectbox("Hyphen handling", ["split", "keep", "join"], index=0, key="opt_hyphen")
    st.selectbox("Normalization", ["none", "stem", "lemma"], index=1, key="opt_norm")

    st.divider()
    status = ir.nltk_status()
    st.caption(f"Stemmer: {status['stemmer']}")
    st.caption(f"Lemmatizer: {status['lemmatizer']}")


st.title("End-to-End Information Retrieval System")
st.write(
    f"**{len(st.session_state.doc_names)} documents** loaded. "
    "Use the tabs below to run every stage of the IR pipeline from this front end."
)

tabs = st.tabs([
    "A. Documents & Search",
    "B. Preprocessing",
    "C. Phrase Queries",
    "D. BST vs B-Tree",
    "E. Tolerant Retrieval",
    "G. Inferences",
])

# --------------------------------------------------------------------------- #
# TAB A: View documents + ranked retrieval
# --------------------------------------------------------------------------- #
with tabs[0]:
    st.header("A. View documents and run a search")

    with st.expander("View uploaded documents", expanded=False):
        for name, text in zip(st.session_state.doc_names, st.session_state.doc_texts):
            st.markdown(f"**{name}**")
            st.text(text.strip())
            st.divider()

    st.subheader("Ranked retrieval (tf-idf + cosine similarity)")
    q = st.text_input("Enter a search query", value="information retrieval system",
                      key="search_query")
    if st.button("Search", type="primary"):
        index = build_index()
        vectors, idf = ir.build_tfidf(index.doc_tokens)
        qtok = query_tokens(q)
        st.caption(f"Query tokens after preprocessing: `{qtok}`")
        ranking = ir.cosine_rank(qtok, vectors, idf)
        rows = []
        for d, score in ranking:
            if score <= 0:
                continue
            rows.append({
                "Rank": len(rows) + 1,
                "Document": index.doc_ids[d],
                "Cosine Score": round(score, 4),
                "Preview": st.session_state.doc_texts[d].strip().replace("\n", " ")[:90] + "…",
            })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.warning("No documents matched the query. Try tolerant retrieval (Tab E).")

    with st.expander("Show inverted index (postings lists)"):
        index = build_index()
        inv_rows = [
            {"Term": term, "Doc Frequency": len(index.postings(term)),
             "Postings (doc ids)": str(index.postings(term))}
            for term in index.vocabulary
        ]
        st.caption(f"Vocabulary size: {len(inv_rows)} terms")
        st.dataframe(pd.DataFrame(inv_rows), use_container_width=True, hide_index=True,
                     height=300)


# --------------------------------------------------------------------------- #
# TAB B: Preprocessing + stemming vs lemmatization comparison
# --------------------------------------------------------------------------- #
with tabs[1]:
    st.header("B. Text preprocessing")
    st.write("Each stage of the pipeline is shown below for a chosen document.")

    doc_idx = st.selectbox(
        "Choose a document to inspect",
        range(len(st.session_state.doc_names)),
        format_func=lambda i: st.session_state.doc_names[i],
    )
    hyphen_mode = st.session_state.get("opt_hyphen", "split")
    steps = ir.preprocess_steps(st.session_state.doc_texts[doc_idx], hyphen_mode)
    for stage, tokens in steps.items():
        st.markdown(f"**{stage}** — {len(tokens)} tokens")
        st.code(" ".join(tokens[:60]) + (" …" if len(tokens) > 60 else ""), language="text")

    st.divider()
    st.subheader("Inverted index creation")
    index = build_index()
    st.caption(f"Built from current settings: {current_settings()}")
    sample_terms = index.vocabulary[:15]
    st.table(pd.DataFrame(
        [{"Term": t, "Postings": str(index.postings(t))} for t in sample_terms]
    ))

    st.divider()
    st.subheader("Stemming vs Lemmatization comparison")
    st.write(
        "We compare the two normalizers on a **retrieval-quality** basis: vocabulary "
        "reduction (conflation power) and the overlap of retrieved documents for a set "
        "of test queries (Jaccard similarity of result sets vs. the raw, no-normalization baseline)."
    )

    test_queries = st.text_area(
        "Test queries (one per line)",
        value="retrieval systems\nindexing documents\nlearning models\nsearching queries",
    ).strip().splitlines()

    if st.button("Run comparison"):
        idx_none = build_index("none")
        idx_stem = build_index("stem")
        idx_lemma = build_index("lemma")

        vocab_rows = [{
            "Scheme": "No normalization", "Vocabulary size": len(idx_none.vocabulary),
            "Reduction vs raw": "0.0%",
        }, {
            "Scheme": "Stemming", "Vocabulary size": len(idx_stem.vocabulary),
            "Reduction vs raw": f"{100*(1-len(idx_stem.vocabulary)/max(1,len(idx_none.vocabulary))):.1f}%",
        }, {
            "Scheme": "Lemmatization", "Vocabulary size": len(idx_lemma.vocabulary),
            "Reduction vs raw": f"{100*(1-len(idx_lemma.vocabulary)/max(1,len(idx_none.vocabulary))):.1f}%",
        }]
        st.markdown("**Vocabulary reduction (conflation power)**")
        st.table(pd.DataFrame(vocab_rows))

        rows = []
        v_n, idf_n = ir.build_tfidf(idx_none.doc_tokens)
        v_s, idf_s = ir.build_tfidf(idx_stem.doc_tokens)
        v_l, idf_l = ir.build_tfidf(idx_lemma.doc_tokens)
        for raw_q in test_queries:
            if not raw_q.strip():
                continue
            res_n = {d for d, s in ir.cosine_rank(query_tokens(raw_q, "none"), v_n, idf_n) if s > 0}
            res_s = {d for d, s in ir.cosine_rank(query_tokens(raw_q, "stem"), v_s, idf_s) if s > 0}
            res_l = {d for d, s in ir.cosine_rank(query_tokens(raw_q, "lemma"), v_l, idf_l) if s > 0}
            rows.append({
                "Query": raw_q,
                "#docs (raw)": len(res_n),
                "#docs (stem)": len(res_s),
                "#docs (lemma)": len(res_l),
                "Jaccard stem-vs-raw": round(ir.jaccard(res_s, res_n), 3),
                "Jaccard lemma-vs-raw": round(ir.jaccard(res_l, res_n), 3),
            })
        comp_df = pd.DataFrame(rows)
        st.markdown("**Retrieval result overlap per query**")
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

        avg_stem = comp_df["#docs (stem)"].mean()
        avg_lemma = comp_df["#docs (lemma)"].mean()
        winner = "Stemming" if avg_stem >= avg_lemma else "Lemmatization"
        st.success(
            f"**Conclusion:** Stemming reduces the vocabulary more aggressively "
            f"(higher recall / conflation), while lemmatization keeps valid dictionary words "
            f"(higher precision). For this dataset, **{winner}** retrieves more documents on "
            f"average (stem avg={avg_stem:.2f}, lemma avg={avg_lemma:.2f}). "
            "Stemming is therefore the more suitable normalizer here when recall matters; "
            "lemmatization is preferable when interpretability/precision is the priority."
        )


# --------------------------------------------------------------------------- #
# TAB C: Phrase queries (biword vs positional)
# --------------------------------------------------------------------------- #
with tabs[2]:
    st.header("C. Phrase query processing")
    st.write("Compare **biword** and **positional** index answers for a phrase query.")
    st.info(
        "Try **`wildcard query information`** to see the biword index produce a "
        "**false positive** (it matches a doc that contains the word pairs but not the "
        "contiguous phrase), which the positional index correctly rejects. "
        "Try **`information retrieval`** for a clean exact match."
    )

    phrase = st.text_input("Enter a phrase query", value="wildcard query information",
                           key="phrase_query")
    index = build_index()

    if st.button("Run phrase query"):
        ptok = query_tokens(phrase)
        st.caption(f"Phrase tokens after preprocessing: `{ptok}`")

        biword_docs = ir.phrase_query_biword(ptok, index)
        pos_docs = ir.phrase_query_positional(ptok, index)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Biword index result**")
            st.write(sorted(index.doc_ids[d] for d in biword_docs) or "No matches")
        with c2:
            st.markdown("**Positional index result**")
            st.write(sorted(index.doc_ids[d] for d in pos_docs) or "No matches")

        false_positives = biword_docs - pos_docs
        if false_positives:
            st.error(
                "**False positives from the biword index:** "
                f"{sorted(index.doc_ids[d] for d in false_positives)}. "
                "These documents contain every biword pair but NOT the full phrase in order — "
                "the positional index correctly excludes them."
            )
        else:
            st.info("No false positives for this phrase on the current dataset.")

    st.divider()
    with st.expander("Biword index representation (sample)"):
        sample = list(index.biword.items())[:20]
        st.table(pd.DataFrame(
            [{"Biword": bw, "Docs": str(sorted(index.doc_ids[d] for d in docs))}
             for bw, docs in sample]
        ))
    with st.expander("Positional index representation (sample)"):
        sample_terms = index.vocabulary[:12]
        st.table(pd.DataFrame(
            [{"Term": t, "Positions {docid: [pos...]}":
              str({index.doc_ids[d]: p for d, p in index.positional[t].items()})}
             for t in sample_terms]
        ))

    st.markdown(
        "**Why positional is more accurate:** the biword index only checks that "
        "consecutive word *pairs* exist somewhere in a document. For phrases of three or "
        "more words it cannot guarantee the pairs are contiguous and in order, producing "
        "false positives. The positional index stores exact positions, so it verifies that "
        "the terms appear adjacent in the correct sequence."
    )


# --------------------------------------------------------------------------- #
# TAB D: BST vs B-Tree
# --------------------------------------------------------------------------- #
with tabs[3]:
    st.header("D. Dictionary search: Binary Search Tree vs B-Tree")
    index = build_index()
    vocab = index.vocabulary
    st.write(f"Dictionary built from the collection: **{len(vocab)} distinct terms**.")

    btree_t = st.slider("B-Tree minimum degree (t)", 2, 8, 3)
    default_queries = ", ".join(vocab[:: max(1, len(vocab) // 8)][:8]) if vocab else ""
    query_str = st.text_input(
        "Query terms to look up (comma separated)",
        value=default_queries + ", zzznotfound",
    )
    repeats = st.slider("Timing repeats per query", 50, 1000, 300, step=50)

    if st.button("Run tree benchmark"):
        queries = [q.strip() for q in query_str.split(",") if q.strip()]
        result = ir.benchmark_trees(vocab, queries, btree_t=btree_t, repeats=repeats)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Terms", result["n_terms"])
        m2.metric("BST height", result["bst_height"])
        m3.metric("B-Tree height", result["btree_height"])
        m4.metric("B-Tree t", result["btree_t"])

        c1, c2 = st.columns(2)
        c1.metric("BST build time (ms)", result["bst_build_time_ms"])
        c2.metric("B-Tree build time (ms)", result["btree_build_time_ms"])

        df = pd.DataFrame(result["rows"])
        st.dataframe(df, use_container_width=True, hide_index=True)

        avg_bst_c = df["BST Comparisons"].mean()
        avg_bt_c = df["B-Tree Comparisons"].mean()
        avg_bst_t = df["BST Search Time (us)"].mean()
        avg_bt_t = df["B-Tree Search Time (us)"].mean()
        st.markdown("**Average over all queries**")
        st.table(pd.DataFrame([{
            "Avg BST comparisons": round(avg_bst_c, 2),
            "Avg B-Tree comparisons": round(avg_bt_c, 2),
            "Avg BST time (us)": round(avg_bst_t, 3),
            "Avg B-Tree time (us)": round(avg_bt_t, 3),
        }]))
        faster = "B-Tree" if avg_bt_t < avg_bst_t else "BST"
        st.success(
            f"**Inference:** The B-Tree stays balanced (height {result['btree_height']}) "
            f"while the BST height is {result['bst_height']}. The B-Tree performs fewer key "
            f"comparisons per node visit and is cache/disk friendly. Here **{faster}** is faster "
            "on average. For large, disk-resident dictionaries the B-Tree scales far better "
            "because its low height minimises expensive node accesses."
        )


# --------------------------------------------------------------------------- #
# TAB E: Tolerant retrieval
# --------------------------------------------------------------------------- #
with tabs[4]:
    st.header("E. Tolerant retrieval")
    # Tolerant retrieval (wildcard / spelling / k-gram / phonetic) operates on the
    # *un-stemmed* dictionary of terms: query-term correction and expansion happen
    # before normalization, so we must match against real words (e.g. "retrieval",
    # not the stem "retriev"). Build the dictionary with normalization disabled.
    index = build_index("none")
    vocab = index.vocabulary
    st.caption(
        "Dictionary built without stemming/lemmatization so corrections match real "
        "words (tolerant retrieval is applied to the query term *before* normalization)."
    )

    technique = st.radio(
        "Choose a technique",
        ["Wildcard query", "Spelling correction (edit distance)", "K-gram index", "Phonetic (Soundex)"],
        horizontal=True,
    )

    if technique == "Wildcard query":
        pattern = st.text_input("Wildcard pattern (use *)", value="inform*")
        if st.button("Resolve wildcard"):
            kg = ir.build_kgram_index(vocab, k=2)
            matches = ir.wildcard_query(pattern, vocab, kg, k=2)
            st.write(f"**{len(matches)} matching terms:** {matches}")
            docs = set()
            for t in matches:
                docs |= index.inverted.get(t, set())
            st.caption("Documents containing any matching term:")
            st.write(sorted(index.doc_ids[d] for d in docs) or "None")

    elif technique == "Spelling correction (edit distance)":
        word = st.text_input("Misspelled word", value="retreival")
        max_dist = st.slider("Max edit distance", 1, 3, 2)
        if st.button("Suggest corrections"):
            sugg = ir.spelling_suggestions(word.lower(), vocab, max_dist=max_dist)
            if sugg:
                st.table(pd.DataFrame(
                    [{"Suggestion": t, "Edit distance": d} for t, d in sugg]
                ))
            else:
                st.warning("No suggestions within the edit-distance threshold.")

    elif technique == "K-gram index":
        k = st.slider("k (n-gram size)", 2, 3, 2)
        term = st.text_input("Show k-grams and matching terms for", value="retrieval")
        if st.button("Build / query k-gram index"):
            kg = ir.build_kgram_index(vocab, k=k)
            padded = f"${term.lower()}$"
            grams = [padded[i:i+k] for i in range(len(padded)-k+1)]
            st.caption(f"k-grams of '{term}': {grams}")
            rows = [{"k-gram": g, "#terms": len(kg.get(g, set())),
                     "terms (sample)": str(sorted(kg.get(g, set()))[:8])} for g in grams]
            st.table(pd.DataFrame(rows))

    else:  # Phonetic
        word = st.text_input("Word for phonetic matching", value="retrievel")
        if st.button("Find phonetic matches"):
            st.caption(f"Soundex('{word}') = {ir.soundex(word)}")
            matches = ir.phonetic_matches(word, vocab)
            st.write(f"**Vocabulary terms that sound alike:** {matches or 'None'}")


# --------------------------------------------------------------------------- #
# TAB G: Inferences & Discussion
# --------------------------------------------------------------------------- #
with tabs[5]:
    st.header("G. Inference and Discussion")
    st.markdown(
        """
- **Which preprocessing technique improved retrieval quality?**
  Stop-word removal + normalization (stemming/lemmatization) gave the biggest gains:
  they conflate surface forms (e.g. *retrieval / retrieving / retrieved*) so a query
  matches more relevant documents. Lowercasing and hyphen splitting also help recall.

- **Was stemming or lemmatization better for this dataset?**
  Stemming reduces the vocabulary more aggressively and maximised recall, so it is the
  more suitable choice here. Lemmatization produced cleaner dictionary words (better
  precision/interpretability) but slightly lower recall. See the quantitative comparison
  in **Tab B**.

- **Which phrase query index was more accurate?**
  The **positional index**. The biword index can return false positives for phrases of
  3+ words because it only checks consecutive pairs, not global order/adjacency (Tab C).

- **Which tree structure was faster?**
  The **B-Tree** scales better: it stays balanced (low height) and performs fewer node
  accesses, which matters most for large, disk-resident dictionaries (Tab D).

- **How tolerant was the retrieval model?**
  It handles wildcards (k-gram backed), spelling errors (edit distance), and phonetic
  variants (Soundex), so it recovers gracefully from imperfect queries (Tab E).

- **Limitations.**
  Small in-memory collection; tf-idf vector space model ignores semantics/word order;
  the fallback stemmer/lemmatizer are simpler than NLTK; Soundex is English-only.

- **How can the system be improved?**
  Add BM25 ranking, semantic embeddings (dense retrieval), spelling correction weighted
  by term frequency, query expansion, persistent on-disk indexes, and relevance feedback.
        """
    )

st.divider()
st.caption("Group 63 · Information Retrieval (AIMLCZG537/DSECLZG537) · Assignment 1")
