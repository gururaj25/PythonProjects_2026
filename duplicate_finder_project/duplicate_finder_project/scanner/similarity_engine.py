from rapidfuzz import fuzz

def similarity_score(name1, name2):
    return fuzz.ratio(name1, name2)

def is_similar(name1, name2, threshold=80):
    return similarity_score(name1, name2) >= threshold