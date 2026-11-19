"""Merge this run's seen/rejected job files into the latest ones on main.

Used by the GitHub workflow when another commit landed on main while the
crawler was running, so a plain rebase would conflict on the JSON files.

Usage: python merge_state.py <our_seen.json> <our_rejected.json>
The current working-tree seen_jobs.json / rejected_jobs.json (main's copy)
are updated in place: main's entries are kept as-is (they may hold manual
edits), and any job this run added that main doesn't have is appended.
"""
import json
import sys


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def key(job):
    return (job.get("company"), job.get("title"), job.get("url"))


def main(our_seen_path, our_rejected_path):
    theirs_seen = load("seen_jobs.json", [])
    ours_seen = load(our_seen_path, [])
    known = {key(j) for j in theirs_seen}
    added = [j for j in ours_seen if key(j) not in known]
    with open("seen_jobs.json", "w", encoding="utf-8") as f:
        json.dump(theirs_seen + added, f, ensure_ascii=False, indent=2)

    theirs_rej = load("rejected_jobs.json", {})
    ours_rej = load(our_rejected_path, {})
    same_config = ours_rej.get("config_hash") == theirs_rej.get("config_hash")
    # If the search config changed, main's old rejections no longer apply.
    jobs = dict(theirs_rej.get("jobs", {})) if same_config else {}
    for h, d in ours_rej.get("jobs", {}).items():
        if h not in jobs or d > jobs[h]:
            jobs[h] = d
    merged_rej = {
        "config_hash": ours_rej.get("config_hash", theirs_rej.get("config_hash")),
        "jobs": jobs,
    }
    with open("rejected_jobs.json", "w", encoding="utf-8") as f:
        json.dump(merged_rej, f, ensure_ascii=False, indent=2)

    print(f"[merge] kept {len(theirs_seen)} jobs from main, added {len(added)} from this run; "
          f"{len(jobs)} remembered rejections")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
