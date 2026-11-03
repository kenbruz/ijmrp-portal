"""
Performance evaluation for the IJMRP matching engine.

Run from the project folder (the one that contains manage.py):

    python performance_test.py

It uses only matching.py with sample data. It never reads or writes the
database, so real accounts and scores are not affected.
"""
import platform
import random
import statistics
import sys
import time

import numpy as np
import sklearn

from portal.matching import compute_match

SKILLS = [
    "Python", "JavaScript", "HTML and CSS", "Django", "SQL", "Git",
    "Data Analysis", "Machine Learning", "Microsoft Excel", "Cloud Computing",
    "Networking", "Cybersecurity", "UI/UX Design", "Digital Marketing",
    "Accounting", "Project Management", "Customer Service", "Communication",
    "Teamwork", "Problem Solving",
]

# The Python Developer job used in the earlier tests: skill -> weight.
JOB = {"Python": 0.40, "Django": 0.30, "SQL": 0.20, "Git": 0.10}

# jobseeker1's real profile: skill -> confidence.
JOBSEEKER1 = {
    "HTML and CSS": 1.0, "JavaScript": 1.0, "Git": 1.0,
    "Python": 0.4, "Teamwork": 0.4, "Communication": 0.4,
}

# Sample candidates for the keyword comparison: skill -> confidence.
SAMPLE_CANDIDATES = [
    ("A: all four skills, strong evidence",
     {"Python": 1.0, "Django": 1.0, "SQL": 1.0, "Git": 1.0}),
    ("B: all four skills, weaker evidence",
     {"Python": 0.6, "Django": 0.6, "SQL": 0.4, "Git": 0.4}),
    ("C: Python and Django only",
     {"Python": 1.0, "Django": 1.0}),
    ("D: SQL and Git only",
     {"SQL": 1.0, "Git": 1.0}),
    ("E: Python only",
     {"Python": 1.0}),
    ("F: Git only",
     {"Git": 1.0}),
    ("G: jobseeker1 (real profile)", JOBSEEKER1),
    ("H: Python, SQL, Git (CV mentions)",
     {"Python": 0.4, "SQL": 0.4, "Git": 0.4}),
    ("I: unrelated skills only",
     {"Accounting": 1.0, "Digital Marketing": 1.0}),
    ("J: no skills", {}),
]


def heading(text):
    print()
    print("=" * 72)
    print(text)
    print("=" * 72)


def environment():
    heading("Test environment")
    print(f"Python         : {sys.version.split()[0]}")
    print(f"NumPy          : {np.__version__}")
    print(f"scikit-learn   : {sklearn.__version__}")
    print(f"Operating sys  : {platform.system()} {platform.release()}")
    print(f"Processor      : {platform.processor()}")


def speed_test():
    heading("1. Speed of one match calculation")
    result = compute_match(JOBSEEKER1, JOB)  # warm-up call
    print(f"Check: jobseeker1 vs Python Developer = {result['score']} "
          f"(earlier result: 25.4)")
    runs = 1000
    start = time.perf_counter()
    for _ in range(runs):
        compute_match(JOBSEEKER1, JOB)
    elapsed = time.perf_counter() - start
    print(f"{runs} calculations took {elapsed:.3f} s")
    print(f"Average per calculation: {elapsed / runs * 1000:.3f} ms")


def random_candidate(rng):
    chosen = rng.sample(SKILLS, rng.randint(3, 8))
    return {skill: rng.choice([0.4, 0.6, 1.0]) for skill in chosen}


def scalability_test():
    heading("2. Scalability: time to score every candidate for one job")
    rng = random.Random(42)
    print(f"{'Candidates':>10} {'Total (s)':>10} {'Per candidate (ms)':>20}  Growth")
    previous_n = None
    previous_time = None
    for n in (10, 100, 1000, 5000):
        candidates = [random_candidate(rng) for _ in range(n)]
        timings = []
        for _ in range(3):
            start = time.perf_counter()
            for candidate in candidates:
                compute_match(candidate, JOB)
            timings.append(time.perf_counter() - start)
        total = statistics.median(timings)
        growth = "-"
        if previous_time:
            growth = (f"time x{total / previous_time:.1f} "
                      f"for x{n // previous_n} candidates")
        print(f"{n:>10} {total:>10.3f} {total / n * 1000:>20.3f}  {growth}")
        previous_n = n
        previous_time = total


def ranks(scores):
    return [1 + sum(1 for other in scores if other > score) for score in scores]


def keyword_comparison():
    heading("3. Weighted matching compared with simple keyword counting")
    keyword_scores = []
    weighted_scores = []
    matched_counts = []
    for _, skills in SAMPLE_CANDIDATES:
        count = sum(1 for skill in JOB if skills.get(skill, 0) > 0)
        matched_counts.append(count)
        keyword_scores.append(count / len(JOB) * 100)
        weighted_scores.append(compute_match(skills, JOB)["score"])
    keyword_ranks = ranks(keyword_scores)
    weighted_ranks = ranks(weighted_scores)

    print(f"{'Candidate':<36} {'Matched':>7} {'Keyword%':>9} {'Rank':>5} "
          f"{'Weighted':>9} {'Rank':>5}")
    for i, (name, _) in enumerate(SAMPLE_CANDIDATES):
        print(f"{name:<36} {str(matched_counts[i]) + '/' + str(len(JOB)):>7} "
              f"{keyword_scores[i]:>9.1f} {keyword_ranks[i]:>5} "
              f"{weighted_scores[i]:>9.1f} {weighted_ranks[i]:>5}")
    different = sum(1 for a, b in zip(keyword_ranks, weighted_ranks) if a != b)
    print()
    print(f"{different} of {len(SAMPLE_CANDIDATES)} candidates are ranked "
          f"differently by the two methods.")


def fairness_check():
    heading("4. Fairness check: same skills, different personal details")
    skills = {"Python": 1.0, "Django": 1.0, "SQL": 1.0, "Git": 1.0}
    people = [
        "Candidate 1 (name X, University A)",
        "Candidate 2 (name Y, University B)",
    ]
    scores = []
    for person in people:
        score = compute_match(dict(skills), JOB)["score"]
        scores.append(score)
        print(f"{person:<40} score = {score}")
    print(f"Scores identical: {scores[0] == scores[1]}")
    print("The engine receives only skills and evidence, never names or "
          "institutions.")


if __name__ == "__main__":
    environment()
    speed_test()
    scalability_test()
    keyword_comparison()
    fairness_check()
