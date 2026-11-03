"""
Matching engine: weighted cosine similarity between a candidate and a job.

This file has no Django imports on purpose, so it can be tested on its own.
The views pass in plain dictionaries:

    candidate_skills = {"Python": 0.4, "Git": 1.0, ...}   # skill name -> confidence
    job_skills       = {"Python": 0.40, "Django": 0.30, ...}  # skill name -> weight
"""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def compute_match(candidate_skills, job_skills):
    """
    Returns a dict:
        score      float, 0 to 100
        breakdown  {skill: points}, the points each job skill adds to the score
        gaps       [skill, ...] skills the job asks for that the candidate has no evidence for
    """
    # One position per skill that appears on either side.
    skills = sorted(set(candidate_skills) | set(job_skills))

    cand = np.array([candidate_skills.get(s, 0.0) for s in skills], dtype=float)
    job = np.array([job_skills.get(s, 0.0) for s in skills], dtype=float)

    cand_norm = np.linalg.norm(cand)
    job_norm = np.linalg.norm(job)

    # If either side is empty there is nothing to compare.
    if cand_norm == 0 or job_norm == 0:
        return {"score": 0.0, "breakdown": {}, "gaps": sorted(s for s, w in job_skills.items() if w > 0)}

    # Total score (scikit-learn, as chapter 3 describes).
    score = float(cosine_similarity(cand.reshape(1, -1), job.reshape(1, -1))[0][0]) * 100

    # Per-skill contribution: each skill's share of the dot product,
    # divided by the same denominator. These add up to the total score.
    breakdown = {}
    for s, c, j in zip(skills, cand, job):
        if j > 0:
            breakdown[s] = round(float(c * j / (cand_norm * job_norm)) * 100, 1)

    gaps = sorted(s for s, w in job_skills.items() if w > 0 and candidate_skills.get(s, 0.0) == 0)

    return {"score": round(score, 1), "breakdown": breakdown, "gaps": gaps}
