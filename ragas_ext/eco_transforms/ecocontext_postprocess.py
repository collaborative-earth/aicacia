import re
from collections import defaultdict
from rapidfuzz import process, fuzz

# Set of nlp manipulation to uniform and improve ecological context

def build_ecocontext_sets(kg):
    """
    Returns a dict mapping each ecocontext field to a Python set of unique terms.
    """
    def normalize_term(s):
        s = s.lower().strip()
        s = re.sub(r'[^a-z0-9\s-]', '', s)  # remove punctuation
        s = re.sub(r'\s+', ' ', s)          # collapse whitespace
        s = s.rstrip('s') if len(s) > 7 else s  # crude plural reduction
        return s
    
    vocab = defaultdict(set)

    for node in kg.nodes:
        ctx = node.properties.get("ecocontext", {}) or {}
        for key in ("locations", "ecosystems", "species", "challenges"):
            vals = ctx.get(key) or []
            for v in vals:
                if isinstance(v, str) and v.strip():
                    vocab[key].add(normalize_term(v.strip()))

    # Cast defaultdict -> dict but keep values as sets
    return {k: v for k, v in vocab.items()}


def merge_synonyms(term_set, score_cutoff=90):
    """
    term_set: set of normalized strings
    Returns a set of canonical terms after merging near-duplicates.

    """
    terms = list(term_set)
    merged = {}
    canonical = []

    for term in terms:
        if term in merged:
            continue
        # find all near matches
        matches = process.extract(term, terms, scorer=fuzz.token_sort_ratio, limit=None)
        cluster = [t for t, score, _ in matches if score >= score_cutoff]
        # pick canonical (shortest term)
        canon = min(cluster, key=len)
        canonical.append(canon)
        # mark all cluster members as merged
        for t in cluster:
            merged[t] = canon

    return set(canonical)

def repair_node_ecocontext(node, vocab, min_signal_to_skip=1):
    """
    Fill missing ecocontext fields using the vocabulary sets.
    Only fill if node has low signal (few existing terms).
    Usage example:
    # Apply to all nodes
    for node in kg.nodes:
        node.properties["ecocontext"] = repair_node_ecocontext(node, vocab_sets)
    """
    ctx = node.properties.get("ecocontext", {}) or {}
    signal = sum(1 for v in ctx.values() if v)
    if signal >= min_signal_to_skip:
        return ctx  # skip if already has sufficient info

    text = node.properties.get("page_content", "").lower()
    new_ctx = {}
    for key in ("locations", "ecosystems", "species", "challenges"):
        matches = [term for term in vocab[key] if term in text]
        new_ctx[key] = ctx.get(key) or matches
    return new_ctx