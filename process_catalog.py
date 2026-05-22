import json
import requests
import re

# ==============================
# SHL Catalog JSON URL
# ==============================

CATALOG_URL = "https://tcp-us-prod-rnd.shl.com/voiceRater/shl-ai-hiring/shl_product_catalog.json"

# ==============================
# Important skill keywords
# ==============================

SKILL_KEYWORDS = [
    # Programming
    "Java",
    "Python",
    ".NET",
    "C#",
    "SQL",
    "JavaScript",
    "React",
    "Node.js",
    "AWS",
    "Cloud",
    "DevOps",
    "Data Science",
    "Machine Learning",
    "AI",
    "Cybersecurity",

    # Soft skills
    "Leadership",
    "Communication",
    "Teamwork",
    "Problem Solving",
    "Critical Thinking",
    "Collaboration",
    "Analytical",
    "Stakeholder Management",
    "Decision Making",
    "Creativity",
    "Adaptability",
    "Time Management",

    # Business
    "Sales",
    "Marketing",
    "Finance",
    "Customer Service",
    "Management"
]

# ==============================
# Download SHL catalog
# ==============================

print("Downloading SHL catalog...")

response = requests.get(CATALOG_URL)

if response.status_code != 200:
    raise Exception(f"Failed to download catalog: {response.status_code}")

# ==============================
# Read raw text
# ==============================

raw_text = response.text

# ==============================
# Fix malformed JSON issues
# ==============================

try:
    data = json.loads(raw_text, strict=False)

except Exception as e:
    print("Initial JSON parsing failed.")
    print("Trying cleanup approach...")

    cleaned_text = (
        raw_text
        .replace("\r", " ")
        .replace("\t", " ")
    )

    data = json.loads(cleaned_text, strict=False)

# ==============================
# Process catalog
# ==============================

cleaned_catalog = []

print("Processing assessments...")

for item in data:

    # --------------------------
    # Basic fields
    # --------------------------

    assessment_id = item.get("entity_id", "")
    name = item.get("name", "").strip()
    url = item.get("link", "").strip()
    description = item.get("description", "").strip()

    # --------------------------
    # Additional fields
    # --------------------------

    job_levels = item.get("job_levels", [])
    languages = item.get("languages", [])

    duration = item.get("duration", "").strip()

    remote = item.get("remote", "no")
    adaptive = item.get("adaptive", "no")

    keys = item.get("keys", [])

    # --------------------------
    # Convert yes/no to boolean
    # --------------------------

    remote = True if remote.lower() == "yes" else False
    adaptive = True if adaptive.lower() == "yes" else False

    # --------------------------
    # Convert keys to string
    # --------------------------

    test_type = ", ".join(keys)

    # --------------------------
    # Extract skills
    # --------------------------

    combined_text = f"{name} {description}"

    extracted_skills = []

    for skill in SKILL_KEYWORDS:
        pattern = rf"\b{re.escape(skill)}\b"

        if re.search(pattern, combined_text, re.IGNORECASE):
            extracted_skills.append(skill)

    # Remove duplicates
    extracted_skills = list(set(extracted_skills))

    # --------------------------
    # Create search text
    # VERY IMPORTANT FOR EMBEDDINGS
    # --------------------------

    search_text = f"""
    Assessment Name: {name}

    Description:
    {description}

    Test Type:
    {test_type}

    Skills:
    {' '.join(extracted_skills)}

    Job Levels:
    {' '.join(job_levels)}

    Duration:
    {duration}

    Remote Testing:
    {remote}

    Adaptive Testing:
    {adaptive}

    Languages:
    {' '.join(languages)}
    """

    search_text = search_text.strip()

    # --------------------------
    # Final cleaned object
    # --------------------------

    cleaned_item = {
        "id": assessment_id,
        "name": name,
        "url": url,
        "description": description,
        "test_type": test_type,
        "skills": extracted_skills,
        "job_levels": job_levels,
        "duration": duration,
        "remote": remote,
        "adaptive": adaptive,
        "languages": languages,
        "search_text": search_text
    }

    cleaned_catalog.append(cleaned_item)

# ==============================
# Save cleaned catalog
# ==============================

output_file = "catalog.json"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(cleaned_catalog, f, indent=2, ensure_ascii=False)

# ==============================
# Final output
# ==============================

print("\n===================================")
print(f"Total assessments processed: {len(cleaned_catalog)}")
print(f"Saved cleaned catalog to: {output_file}")
print("===================================\n")

# ==============================
# Preview sample
# ==============================

if len(cleaned_catalog) > 0:

    print("Sample Processed Entry:\n")

    print(json.dumps(cleaned_catalog[0], indent=2, ensure_ascii=False))