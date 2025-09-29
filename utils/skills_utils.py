import json

def load_internal_skills(path="data/internal_team_skills.json"):
    """Load internal team skills from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def skill_gap_analysis(rfp_skills, internal_skills_dict):
    """Compare RFP skills with internal team skills."""
    covered = []
    missing = []

    # Flatten internal skills for quick lookup
    internal_skills_set = set()
    for skills in internal_skills_dict.values():
        internal_skills_set.update([s.lower() for s in skills])

    for skill in rfp_skills:
        if skill.lower() in internal_skills_set:
            covered.append(skill)
        else:
            missing.append(skill)

    return {"covered": covered, "missing": missing}
