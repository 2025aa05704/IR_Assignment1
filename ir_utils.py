"""
ir_utils.py
-----------
Core Information Retrieval logic for the Group 63 Assignment-1 Streamlit app.

This module is intentionally dependency-light. It uses NLTK when it is available
(for the full Porter stemmer / WordNet lemmatizer) but falls back to built-in,
self-contained implementations so the application always runs, even offline.

Sections:
    B. Text preprocessing  (tokenize, lowercase, stop-words, hyphen handling,
                            stemming, lemmatization)
    C. Phrase queries      (inverted, positional and biword indexes)
    D. Dictionary search   (Binary Search Tree and B-Tree with metrics)
    E. Tolerant retrieval  (edit distance, k-gram, wildcard, Soundex)
    Ranking                (tf-idf + cosine similarity used for retrieval and
                            for the stemming-vs-lemmatization comparison)
"""

from __future__ import annotations

import math
import os
import re
import time
from collections import defaultdict

# --------------------------------------------------------------------------- #
# Optional NLTK integration (graceful fallback if not installed / no data)
# --------------------------------------------------------------------------- #
_NLTK_STEMMER = None
_NLTK_LEMMATIZER = None
try:  # pragma: no cover - depends on environment
    from nltk.stem import PorterStemmer as _PorterStemmer
    _NLTK_STEMMER = _PorterStemmer()
except Exception:  # noqa: BLE001
    _NLTK_STEMMER = None

try:  # pragma: no cover - depends on environment / downloaded data
    from nltk.stem import WordNetLemmatizer as _WordNetLemmatizer
    import nltk

    try:
        nltk.data.find("corpora/wordnet.zip")
    except LookupError:
        try:
            nltk.download("wordnet", quiet=True)
            nltk.download("omw-1.4", quiet=True)
        except Exception:  # noqa: BLE001
            pass
    _lem = _WordNetLemmatizer()
    _lem.lemmatize("tests")  # force-load; raises if data unavailable
    _NLTK_LEMMATIZER = _lem
except Exception:  # noqa: BLE001
    _NLTK_LEMMATIZER = None


def nltk_status() -> dict:
    """Report which optional engines are active (shown in the UI)."""
    return {
        "stemmer": "NLTK PorterStemmer" if _NLTK_STEMMER else "built-in fallback stemmer",
        "lemmatizer": "NLTK WordNetLemmatizer" if _NLTK_LEMMATIZER else "built-in rule-based lemmatizer",
    }


# --------------------------------------------------------------------------- #
# B. TEXT PREPROCESSING
# --------------------------------------------------------------------------- #

# A compact, dependency-free English stop-word list.
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "can",
    "could", "did", "do", "does", "for", "from", "had", "has", "have", "he",
    "her", "his", "how", "i", "if", "in", "into", "is", "it", "its", "may",
    "of", "on", "or", "our", "out", "over", "own", "s", "she", "so", "such",
    "than", "that", "the", "their", "them", "then", "there", "these", "they",
    "this", "to", "up", "was", "we", "were", "what", "when", "where", "which",
    "while", "who", "will", "with", "would", "you", "your",
}

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z\-']*[A-Za-z]|[A-Za-z]")


def raw_tokenize(text: str) -> list[str]:
    """Split text into raw word tokens (keeps hyphens for later handling)."""
    return _TOKEN_RE.findall(text)


# ---- Hyphen handling ------------------------------------------------------ #
def apply_hyphen(token: str, mode: str) -> list[str]:
    """Handle a hyphenated token according to ``mode``.

    Modes:
        "keep"   -> keep the token as-is  (e.g. "state-of-the-art")
        "split"  -> split into separate tokens ("state", "of", "the", "art")
        "join"   -> remove the hyphen and join ("stateoftheart")
    """
    if "-" not in token:
        return [token]
    if mode == "split":
        return [p for p in token.split("-") if p]
    if mode == "join":
        return [token.replace("-", "")]
    return [token]  # keep


# ---- Stemming ------------------------------------------------------------- #
def _fallback_stem(word: str) -> str:
    """A small but reasonable suffix-stripping stemmer (Porter-like)."""
    w = word
    if len(w) <= 3:
        return w
    for suf in ("ization", "ational", "fulness", "ousness", "iveness"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    for suf in ("ements", "ements", "ation", "ments", "ingly", "edly"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    for suf in ("ing", "ies", "ied", "ment", "ness", "ous", "ive", "ize", "ise"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            base = w[: -len(suf)]
            if suf == "ies":
                return base + "y"
            return base
    for suf in ("ed", "es", "ly", "er", "or"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        return w[:-1]
    return w


def stem(word: str) -> str:
    if _NLTK_STEMMER is not None:
        try:
            return _NLTK_STEMMER.stem(word)
        except Exception:  # noqa: BLE001
            pass
    return _fallback_stem(word)


# ---- Lemmatization -------------------------------------------------------- #
_IRREGULAR_LEMMAS = {
    "are": "be", "is": "be", "was": "be", "were": "be", "been": "be",
    "has": "have", "had": "have", "having": "have",
    "does": "do", "did": "do", "done": "do",
    "men": "man", "women": "woman", "children": "child", "feet": "foot",
    "teeth": "tooth", "mice": "mouse", "people": "person", "data": "datum",
    "indices": "index", "matrices": "matrix", "analyses": "analysis",
    "better": "good", "best": "good", "worse": "bad", "worst": "bad",
}


def _fallback_lemmatize(word: str) -> str:
    if word in _IRREGULAR_LEMMAS:
        return _IRREGULAR_LEMMAS[word]
    if len(word) <= 3:
        return word
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("ses") or word.endswith("xes") or word.endswith("zes") or word.endswith("ches") or word.endswith("shes"):
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def lemmatize(word: str) -> str:
    if _NLTK_LEMMATIZER is not None:
        try:
            # lemmatize as noun then verb for a slightly better result
            n = _NLTK_LEMMATIZER.lemmatize(word, pos="n")
            return _NLTK_LEMMATIZER.lemmatize(n, pos="v")
        except Exception:  # noqa: BLE001
            pass
    return _fallback_lemmatize(word)


def preprocess(
    text: str,
    lowercase: bool = True,
    remove_stopwords: bool = True,
    hyphen_mode: str = "split",
    normalization: str = "none",  # "none" | "stem" | "lemma"
) -> list[str]:
    """Run the full preprocessing pipeline and return a list of tokens."""
    tokens = raw_tokenize(text)
    out: list[str] = []
    for tok in tokens:
        if lowercase:
            tok = tok.lower()
        for piece in apply_hyphen(tok, hyphen_mode):
            piece = piece.strip("'-")
            if not piece:
                continue
            if remove_stopwords and piece in STOPWORDS:
                continue
            if normalization == "stem":
                piece = stem(piece)
            elif normalization == "lemma":
                piece = lemmatize(piece)
            if piece:
                out.append(piece)
    return out


def preprocess_steps(text: str, hyphen_mode: str = "split") -> dict:
    """Return the intermediate output of each preprocessing stage (for the UI)."""
    raw = raw_tokenize(text)
    lowered = [t.lower() for t in raw]
    hyphenated: list[str] = []
    for t in lowered:
        hyphenated.extend(apply_hyphen(t, hyphen_mode))
    no_stop = [t for t in hyphenated if t not in STOPWORDS]
    stemmed = [stem(t) for t in no_stop]
    lemmatized = [lemmatize(t) for t in no_stop]
    return {
        "1. Tokenization": raw,
        "2. Lowercasing": lowered,
        f"3. Hyphen handling ({hyphen_mode})": hyphenated,
        "4. Stop-word removal": no_stop,
        "5a. Stemming": stemmed,
        "5b. Lemmatization": lemmatized,
    }


# --------------------------------------------------------------------------- #
# INDEX CONSTRUCTION (inverted, positional, biword)
# --------------------------------------------------------------------------- #
class IRIndex:
    """Holds all indexes built from a tokenized document collection."""

    def __init__(self, doc_ids: list[str], doc_tokens: list[list[str]]):
        self.doc_ids = doc_ids
        self.doc_tokens = doc_tokens
        self.inverted: dict[str, set[int]] = defaultdict(set)
        self.positional: dict[str, dict[int, list[int]]] = defaultdict(dict)
        self.biword: dict[str, set[int]] = defaultdict(set)
        self._build()

    def _build(self) -> None:
        for d, tokens in enumerate(self.doc_tokens):
            for pos, term in enumerate(tokens):
                self.inverted[term].add(d)
                self.positional[term].setdefault(d, []).append(pos)
            for i in range(len(tokens) - 1):
                bw = f"{tokens[i]} {tokens[i + 1]}"
                self.biword[bw].add(d)

    @property
    def vocabulary(self) -> list[str]:
        return sorted(self.inverted.keys())

    def postings(self, term: str) -> list[int]:
        return sorted(self.inverted.get(term, set()))


# --------------------------------------------------------------------------- #
# C. PHRASE QUERIES
# --------------------------------------------------------------------------- #
def phrase_query_biword(phrase_tokens: list[str], index: IRIndex) -> set[int]:
    """Answer a phrase query using the biword index.

    Long phrases are decomposed into consecutive biwords and the candidate set
    is the intersection of each biword's postings. This can yield FALSE
    POSITIVES because the biword index does not verify global ordering.
    """
    if len(phrase_tokens) == 0:
        return set()
    if len(phrase_tokens) == 1:
        return set(index.inverted.get(phrase_tokens[0], set()))
    result: set[int] | None = None
    for i in range(len(phrase_tokens) - 1):
        bw = f"{phrase_tokens[i]} {phrase_tokens[i + 1]}"
        docs = index.biword.get(bw, set())
        result = set(docs) if result is None else (result & docs)
        if not result:
            break
    return result or set()


def phrase_query_positional(phrase_tokens: list[str], index: IRIndex) -> set[int]:
    """Answer a phrase query using the positional index (exact, ordered)."""
    if not phrase_tokens:
        return set()
    if len(phrase_tokens) == 1:
        return set(index.inverted.get(phrase_tokens[0], set()))

    postings = [index.positional.get(t, {}) for t in phrase_tokens]
    if any(len(p) == 0 for p in postings):
        return set()

    candidate_docs = set(postings[0].keys())
    for p in postings[1:]:
        candidate_docs &= set(p.keys())

    result: set[int] = set()
    for d in candidate_docs:
        first_positions = postings[0][d]
        for start in first_positions:
            if all((start + offset) in set(postings[offset][d])
                   for offset in range(1, len(phrase_tokens))):
                result.add(d)
                break
    return result


# --------------------------------------------------------------------------- #
# D. DICTIONARY SEARCH: BINARY SEARCH TREE
# --------------------------------------------------------------------------- #
class _BSTNode:
    __slots__ = ("key", "left", "right")

    def __init__(self, key: str):
        self.key = key
        self.left: _BSTNode | None = None
        self.right: _BSTNode | None = None


class BinarySearchTree:
    """Unbalanced BST over dictionary terms; tracks comparison counts."""

    def __init__(self) -> None:
        self.root: _BSTNode | None = None
        self.size = 0

    def insert(self, key: str) -> None:
        if self.root is None:
            self.root = _BSTNode(key)
            self.size += 1
            return
        node = self.root
        while True:
            if key == node.key:
                return
            if key < node.key:
                if node.left is None:
                    node.left = _BSTNode(key)
                    self.size += 1
                    return
                node = node.left
            else:
                if node.right is None:
                    node.right = _BSTNode(key)
                    self.size += 1
                    return
                node = node.right

    def search(self, key: str) -> tuple[bool, int]:
        """Return (found, comparisons)."""
        node, comparisons = self.root, 0
        while node is not None:
            comparisons += 1
            if key == node.key:
                return True, comparisons
            node = node.left if key < node.key else node.right
        return False, comparisons

    def height(self) -> int:
        def _h(n: _BSTNode | None) -> int:
            if n is None:
                return 0
            return 1 + max(_h(n.left), _h(n.right))
        return _h(self.root)


# --------------------------------------------------------------------------- #
# D. DICTIONARY SEARCH: B-TREE
# --------------------------------------------------------------------------- #
class _BTreeNode:
    __slots__ = ("keys", "children", "leaf")

    def __init__(self, leaf: bool = True):
        self.keys: list[str] = []
        self.children: list[_BTreeNode] = []
        self.leaf = leaf


class BTree:
    """A classic B-Tree (minimum degree t); tracks comparison counts."""

    def __init__(self, t: int = 3):
        if t < 2:
            t = 2
        self.t = t
        self.root = _BTreeNode(leaf=True)
        self.size = 0

    def search(self, key: str) -> tuple[bool, int]:
        """Return (found, comparisons)."""
        comparisons = 0
        node = self.root
        while node is not None:
            i = 0
            while i < len(node.keys):
                comparisons += 1
                if key == node.keys[i]:
                    return True, comparisons
                if key < node.keys[i]:
                    break
                i += 1
            if node.leaf:
                return False, comparisons
            node = node.children[i]
        return False, comparisons

    def insert(self, key: str) -> None:
        root = self.root
        if len(root.keys) == 2 * self.t - 1:
            new_root = _BTreeNode(leaf=False)
            new_root.children.append(root)
            self._split_child(new_root, 0)
            self.root = new_root
            self._insert_non_full(new_root, key)
        else:
            self._insert_non_full(root, key)

    def _insert_non_full(self, node: _BTreeNode, key: str) -> None:
        i = len(node.keys) - 1
        if node.leaf:
            if key in node.keys:
                return
            node.keys.append(key)
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                i -= 1
            node.keys[i + 1] = key
            self.size += 1
        else:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            if i >= 0 and key == node.keys[i]:
                return
            i += 1
            if len(node.children[i].keys) == 2 * self.t - 1:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
                elif key == node.keys[i]:
                    return
            self._insert_non_full(node.children[i], key)

    def _split_child(self, parent: _BTreeNode, i: int) -> None:
        t = self.t
        full = parent.children[i]
        new = _BTreeNode(leaf=full.leaf)
        mid_key = full.keys[t - 1]
        new.keys = full.keys[t:]
        full.keys = full.keys[: t - 1]
        if not full.leaf:
            new.children = full.children[t:]
            full.children = full.children[:t]
        parent.children.insert(i + 1, new)
        parent.keys.insert(i, mid_key)

    def height(self) -> int:
        h, node = 1, self.root
        while not node.leaf:
            h += 1
            node = node.children[0]
        return h


def benchmark_trees(vocabulary: list[str], queries: list[str], btree_t: int = 3,
                    repeats: int = 200) -> dict:
    """Build both trees, run search queries and time them.

    ``repeats`` runs each query many times so that the timing is measurable on
    fast machines. Returns per-query rows plus build times and structure stats.
    """
    # Insert in a shuffled (but reproducible) order. Inserting sorted terms would
    # degenerate the BST into a linked list (worst case); shuffling yields a
    # realistic average-case BST for a fairer comparison against the B-Tree.
    import random
    shuffled = list(vocabulary)
    random.Random(42).shuffle(shuffled)

    bst = BinarySearchTree()
    t0 = time.perf_counter()
    for term in shuffled:
        bst.insert(term)
    bst_build = time.perf_counter() - t0

    bt = BTree(t=btree_t)
    t0 = time.perf_counter()
    for term in shuffled:
        bt.insert(term)
    bt_build = time.perf_counter() - t0

    rows = []
    for q in queries:
        # BST
        t0 = time.perf_counter()
        found_bst = comp_bst = 0
        for _ in range(repeats):
            f, c = bst.search(q)
            found_bst, comp_bst = f, c
        bst_time = (time.perf_counter() - t0) / repeats

        # B-Tree
        t0 = time.perf_counter()
        found_bt = comp_bt = 0
        for _ in range(repeats):
            f, c = bt.search(q)
            found_bt, comp_bt = f, c
        bt_time = (time.perf_counter() - t0) / repeats

        rows.append({
            "Query Term": q,
            "Found": bool(found_bst),
            "BST Comparisons": comp_bst,
            "B-Tree Comparisons": comp_bt,
            "BST Search Time (us)": round(bst_time * 1e6, 3),
            "B-Tree Search Time (us)": round(bt_time * 1e6, 3),
        })

    return {
        "rows": rows,
        "bst_build_time_ms": round(bst_build * 1e3, 3),
        "btree_build_time_ms": round(bt_build * 1e3, 3),
        "bst_height": bst.height(),
        "btree_height": bt.height(),
        "n_terms": len(vocabulary),
        "btree_t": btree_t,
    }


# --------------------------------------------------------------------------- #
# E. TOLERANT RETRIEVAL
# --------------------------------------------------------------------------- #
def edit_distance(a: str, b: str) -> int:
    """Levenshtein edit distance (insertion, deletion, substitution = 1)."""
    m, n = len(a), len(b)
    if m == 0:
        return n
    if n == 0:
        return m
    prev = list(range(n + 1))
    for i in range(1, m + 1):
        cur = [i] + [0] * n
        for j in range(1, n + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[n]


def spelling_suggestions(word: str, vocabulary: list[str], max_dist: int = 2,
                         top_k: int = 5) -> list[tuple[str, int]]:
    """Return up to top_k (term, distance) suggestions sorted by distance."""
    scored = []
    for term in vocabulary:
        if abs(len(term) - len(word)) > max_dist:
            continue
        d = edit_distance(word, term)
        if d <= max_dist:
            scored.append((term, d))
    scored.sort(key=lambda x: (x[1], x[0]))
    return scored[:top_k]


def build_kgram_index(vocabulary: list[str], k: int = 2) -> dict[str, set[str]]:
    """Map each character k-gram to the set of terms containing it ($ = boundary)."""
    kgram = defaultdict(set)
    for term in vocabulary:
        padded = f"${term}$"
        for i in range(len(padded) - k + 1):
            kgram[padded[i : i + k]].add(term)
    return kgram


def _kgrams_of(s: str, k: int) -> list[str]:
    return [s[i : i + k] for i in range(len(s) - k + 1)]


def wildcard_query(pattern: str, vocabulary: list[str],
                   kgram_index: dict[str, set[str]] | None = None,
                   k: int = 2) -> list[str]:
    """Resolve a wildcard pattern such as ``inform*`` or ``*tion`` or ``re*ed``."""
    # Build the regex for final verification.
    regex = re.compile("^" + re.escape(pattern).replace(r"\*", ".*") + "$")

    # Use the k-gram index to shrink the candidate set.
    candidates: set[str] | None = None
    if kgram_index is not None:
        padded = "$" + pattern + "$"
        segments = [seg for seg in padded.split("*") if seg]
        grams: list[str] = []
        for seg in segments:
            grams.extend(g for g in _kgrams_of(seg, k) if "*" not in g)
        for g in grams:
            docs = kgram_index.get(g, set())
            candidates = set(docs) if candidates is None else (candidates & docs)
        if candidates is None:
            candidates = set(vocabulary)
    else:
        candidates = set(vocabulary)

    return sorted(t for t in candidates if regex.match(t))


def soundex(word: str) -> str:
    """Compute the 4-character Soundex code of a word."""
    word = re.sub(r"[^A-Za-z]", "", word).upper()
    if not word:
        return ""
    mapping = {
        **dict.fromkeys("BFPV", "1"),
        **dict.fromkeys("CGJKQSXZ", "2"),
        **dict.fromkeys("DT", "3"),
        **dict.fromkeys("L", "4"),
        **dict.fromkeys("MN", "5"),
        **dict.fromkeys("R", "6"),
    }
    first = word[0]
    encoded = first
    prev_code = mapping.get(first, "")
    for ch in word[1:]:
        code = mapping.get(ch, "")
        if ch in "HW":
            continue  # do not reset prev_code
        if code != "" and code != prev_code:
            encoded += code
        prev_code = code if ch not in "AEIOUY" else ""
    encoded = (encoded + "000")[:4]
    return encoded


def phonetic_matches(word: str, vocabulary: list[str]) -> list[str]:
    """Return vocabulary terms whose Soundex code matches ``word``."""
    code = soundex(word)
    return sorted({t for t in vocabulary if soundex(t) == code and t != word.lower()})


# --------------------------------------------------------------------------- #
# RANKING: tf-idf + cosine similarity
# --------------------------------------------------------------------------- #
def build_tfidf(doc_tokens: list[list[str]]) -> tuple[list[dict[str, float]], dict[str, float]]:
    """Return per-document tf-idf weight vectors and the idf table."""
    n = len(doc_tokens)
    df: dict[str, int] = defaultdict(int)
    for tokens in doc_tokens:
        for term in set(tokens):
            df[term] += 1
    idf = {term: math.log((n + 1) / (cnt + 1)) + 1.0 for term, cnt in df.items()}

    vectors: list[dict[str, float]] = []
    for tokens in doc_tokens:
        tf: dict[str, int] = defaultdict(int)
        for t in tokens:
            tf[t] += 1
        vec = {term: (1 + math.log(c)) * idf.get(term, 0.0) for term, c in tf.items()}
        norm = math.sqrt(sum(w * w for w in vec.values())) or 1.0
        vectors.append({t: w / norm for t, w in vec.items()})
    return vectors, idf


def cosine_rank(query_tokens: list[str], doc_vectors: list[dict[str, float]],
                idf: dict[str, float]) -> list[tuple[int, float]]:
    """Rank documents by cosine similarity to the query."""
    tf: dict[str, int] = defaultdict(int)
    for t in query_tokens:
        tf[t] += 1
    qvec = {term: (1 + math.log(c)) * idf.get(term, 0.0) for term, c in tf.items()}
    norm = math.sqrt(sum(w * w for w in qvec.values())) or 1.0
    qvec = {t: w / norm for t, w in qvec.items()}

    scores = []
    for d, dvec in enumerate(doc_vectors):
        s = sum(w * dvec.get(t, 0.0) for t, w in qvec.items())
        scores.append((d, s))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    return len(a & b) / len(union) if union else 0.0


# --------------------------------------------------------------------------- #
# DATASET LOADING
# --------------------------------------------------------------------------- #
def load_default_docs(folder: str = "data") -> tuple[list[str], list[str]]:
    """Load the bundled sample documents. Returns (names, contents)."""
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, folder)
    names, contents = [], []
    if os.path.isdir(path):
        for fn in sorted(os.listdir(path)):
            if fn.lower().endswith(".txt"):
                with open(os.path.join(path, fn), "r", encoding="utf-8") as f:
                    contents.append(f.read())
                    names.append(fn)
    return names, contents
