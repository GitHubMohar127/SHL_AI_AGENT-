import os
import json
import faiss
import numpy as np

from sentence_transformers import SentenceTransformer

# =========================================================
# FILE PATHS
# =========================================================

INDEX_FILE = "shl_faiss.index"
METADATA_FILE = "catalog_metadata.json"
CATALOG_FILE = "catalog.json"

# =========================================================
# LOAD EMBEDDING MODEL
# =========================================================

print("Loading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

# =========================================================
# LOAD EXISTING INDEX
# =========================================================

if os.path.exists(INDEX_FILE) and os.path.exists(METADATA_FILE):

    print("Loading existing FAISS index...")

    index = faiss.read_index(INDEX_FILE)

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    print("FAISS index loaded successfully.")

# =========================================================
# CREATE INDEX ONLY ONCE
# =========================================================

else:

    print("Creating FAISS index for first time...")

    # -----------------------------------------------------
    # Load catalog
    # -----------------------------------------------------

    with open(CATALOG_FILE, "r", encoding="utf-8") as f:

        data = json.load(f)

    print(f"Total assessments loaded: {len(data)}")

    texts = []

    metadata = []

    # -----------------------------------------------------
    # Prepare searchable text
    # -----------------------------------------------------

    for item in data:

        combined_text = f"""
        {item.get('name', '')}
        {item.get('description', '')}
        {' '.join(item.get('skills', []))}
        {item.get('test_type', '')}
        """

        texts.append(combined_text)

        metadata.append(item)

    # -----------------------------------------------------
    # Generate embeddings
    # -----------------------------------------------------

    print("Generating embeddings...")

    embeddings = model.encode(
        texts,
        show_progress_bar=True
    )

    embeddings = np.array(embeddings).astype("float32")

    # -----------------------------------------------------
    # Create FAISS index
    # -----------------------------------------------------

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)

    print("FAISS index created successfully.")

    # -----------------------------------------------------
    # Save index
    # -----------------------------------------------------

    faiss.write_index(index, INDEX_FILE)

    print(f"FAISS index saved as {INDEX_FILE}")

    # -----------------------------------------------------
    # Save metadata
    # -----------------------------------------------------

    with open(METADATA_FILE, "w", encoding="utf-8") as f:

        json.dump(metadata, f, indent=2)

    print(f"Metadata saved as {METADATA_FILE}")

# =========================================================
# SEARCH FUNCTION
# =========================================================

def search_assessments(query, top_k=5):

    query_embedding = model.encode([query])

    query_embedding = np.array(query_embedding).astype("float32")

    distances, indices = index.search(query_embedding, top_k)

    results = []

    for idx in indices[0]:

        if idx < len(metadata):

            results.append(metadata[idx])

    return results

# =========================================================
# COMPARE FUNCTION
# =========================================================

def compare_assessments(name1, name2):

    result1 = None
    result2 = None

    name1_lower = name1.lower()
    name2_lower = name2.lower()

    for item in metadata:

        item_name = item.get("name", "").lower()

        if name1_lower in item_name:
            result1 = item

        if name2_lower in item_name:
            result2 = item

    if not result1 or not result2:

        return {
            "error": "One or both assessments not found."
        }

    comparison = {

        "assessment_1": {
            "name": result1.get("name"),
            "test_type": result1.get("test_type"),
            "duration": result1.get("duration"),
            "skills": result1.get("skills"),
            "description": result1.get("description")
        },

        "assessment_2": {
            "name": result2.get("name"),
            "test_type": result2.get("test_type"),
            "duration": result2.get("duration"),
            "skills": result2.get("skills"),
            "description": result2.get("description")
        }
    }

    return comparison