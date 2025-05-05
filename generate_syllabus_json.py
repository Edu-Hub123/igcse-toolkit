import os
import re
import json

INPUT_FOLDER = "syllabi_texts"
OUTPUT_FILE = "syllabi_parsed.json"

# Modify this to manually map files to board and subject
FILENAME_MAP = {
    "cambridge-biology.txt": ("Cambridge", "Biology"),
    "cambridge-businessstudies.txt": ("Cambridge", "Business Studies"),
    "cambridge-chemistry.txt": ("Cambridge", "Chemistry"),
    "cambridge-computerscience.txt": ("Cambridge", "Computer Science"),
    "cambridge-economics.txt": ("Cambridge", "Economics"),
    "cambridge-englishfirstlanguage.txt": ("Cambridge", "English - First Language"),
    "cambridge-englishliterature.txt": ("Cambridge", "English - Literature"),
    "cambridge-geography.txt": ("Cambridge", "Geography"),
    "cambridge-history.txt": ("Cambridge", "History"),
    "cambridge-maths.txt": ("Cambridge", "Mathematics"),
    "cambridge-physics.txt": ("Cambridge", "Physics"),
    "edexcel-biology.txt": ("Edexcel", "Biology"),
    "edexcel-business.txt": ("Edexcel", "Business"),
    "edexcel-chemistry.txt": ("Edexcel", "Chemistry"),
    "edexcel-economics.txt": ("Edexcel", "Economics"),
    "edexcel-eenglishlangA.txt": ("Edexcel", "English Language A"),
    "edexcel-eliterature.txt": ("Edexcel", "English Literature"),
    "edexcel-geography.txt": ("Edexcel", "Geography"),
    "edexcel-history.txt": ("Edexcel", "History"),
    "edexcel-infandcomtech.txt": ("Edexcel", "Information and Communication Technology"),
    "edexcel-mathsA.txt": ("Edexcel", "Mathematics A"),
    "edexcel-mathsB.txt": ("Edexcel", "Mathematics B"), 
    "edexcel-physics.txt": ("Edexcel", "Physics")
}

def is_section_heading(line):
    return bool(re.match(r"^\d+(\.\d+)*[a-zA-Z]*[\)]?\s", line))

def extract_sections(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    sections = []
    for line in lines:
        line = line.strip()
        if is_section_heading(line):
            sections.append(line)
    return sections

# --- MAIN ---
structured = {}

for file_name in os.listdir(INPUT_FOLDER):
    if file_name.endswith(".txt") and file_name in FILENAME_MAP:
        board, subject = FILENAME_MAP[file_name]
        file_path = os.path.join(INPUT_FOLDER, file_name)
        sections = extract_sections(file_path)

        if board not in structured:
            structured[board] = {}
        structured[board][subject] = {}

        # Group sections by first number (e.g., "1.1", "1.2", "2.1" = Topic 1, 2)
        for sec in sections:
            topic_key = sec.split()[0].split(".")[0]
            topic_name = f"Topic {topic_key}"

            if topic_name not in structured[board][subject]:
                structured[board][subject][topic_name] = []
            structured[board][subject][topic_name].append(sec)

        print(f"✅ Parsed {file_name}")

# Save to JSON
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(structured, f, indent=2)

print(f"\n Saved structured syllabus to {OUTPUT_FILE}")
