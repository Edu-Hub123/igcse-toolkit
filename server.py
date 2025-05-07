from flask import Flask, jsonify, request, send_from_directory, Response, stream_with_context
from flask_cors import CORS
import re
import openai
from topics import TOPICS
import json
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime
import time
import sys

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

with open("IGCSE Syllabi.json", "r") as f:
    syllabus_data = json.load(f)

def strip_markdown(text):
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"#+\s*", "", text)
    text = re.sub(r"`(.*?)`", r"\1", text)
    return text.strip()

def clean_mermaid_code(raw):
    lines = raw.strip().splitlines()
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("```") or line.lower().startswith("mermaid"):
            continue
        if ":" in line or ";" in line or "classDef" in line:
            continue
        cleaned.append(line)
    return "\n".join(cleaned)

CAMBRIDGE_SUBJECTS = sorted([
    "Biology", "Business Studies", "Chemistry", "Computer Science", "Economics",
    "Geography", "History", "Mathematics", "Physics"
])

EDEXCEL_SUBJECTS = sorted([
    "Biology", "Business", "Chemistry", "Economics", "Geography", "History",
    "Information and Communication Technology", "Mathematics A", "Mathematics B",
    "Physics"
])

@app.before_request
def restrict_time_window():
    now = datetime.utcnow()
    start_time = datetime(2025, 5, 3)
    end_time = datetime(2025, 5, 12)
    if not (start_time <= now <= end_time):
        return jsonify({"error": "Access to the prototype has expired."}), 403

@app.route("/get_subjects/<board>", methods=["GET"])
def get_subjects(board):
    if board == "Cambridge":
        return jsonify({"subjects": CAMBRIDGE_SUBJECTS})
    elif board == "Edexcel":
        return jsonify({"subjects": EDEXCEL_SUBJECTS})
    else:
        return jsonify({"error": "Invalid board"}), 400

@app.route("/get_topics", methods=["POST", "OPTIONS"])
def get_topics():
    if request.method == "OPTIONS":
        return '', 204
    data = request.json
    board = data.get("board")
    subject = data.get("subject")
    if not board or not subject:
        return jsonify({"error": "Missing board or subject"}), 400
    try:
        topics = list(syllabus_data[board][subject].keys())
        return jsonify({"topics": topics})
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/get_topics/<board>/<subject>", methods=["GET"])
def get_topics_get(board, subject):
    try:
        topics = list(syllabus_data[board][subject].keys())
        return jsonify({"topics": topics})
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/get_subtopics", methods=["POST"])
def get_subtopics():
    data = request.json
    board = data.get("board", "").strip()
    subject = data.get("subject", "").strip()
    topic = data.get("topic", "").strip()
    try:
        subs = syllabus_data[board][subject][topic]
        return jsonify({"subtopics": list(subs.keys())})
    except KeyError:
        return jsonify({"error": "Board, subject, or topic not found.", "subtopics": []}), 404

@app.route("/generate_notes", methods=["POST"])
def generate_notes():
    data = request.get_json()
    board = data.get('board')
    subject = data.get('subject')
    topic = data.get('topic')
    subtopic = data.get('subtopic')
    learner_type = data.get('learner_type')

    if learner_type not in ["reading_and_writing", "visual"]:
        return jsonify({"notes": "This learner type is not supported yet."})

    try:
        if subtopic == "full":
            topic_data = syllabus_data[board][subject][topic]
            points = []
            for pts in topic_data.values():
                points.extend(pts)
        else:
            points = syllabus_data[board][subject][topic][subtopic]
    except KeyError:
        return jsonify({"error": "Invalid syllabus selection"}), 404

    syllabus_str = "\n".join(f"- {p}" for p in points)

    if learner_type == "reading_and_writing":
        word_limit = max(1000, len(points) * 40)
        prompt = f"""
You are an expert IGCSE {subject} tutor. Generate comprehensive revision notes strictly based on the syllabus points below.

Syllabus points:
{syllabus_str}

Guidelines:
- Important: You must ensure that the generated notes fully and completely cover every syllabus point listed below. Do not omit or skip any point. All syllabus content must be addressed in detail, with no gaps.
- Write each point in STRICT accordance with the given syllabus points, using real-world examples and definitions where relevant.
- Where relevant, ALWAYS include real-world examples. 
- Use bold headings that state which topic/sub-topic is being discussed, and explain the content below each heading using bullet points and short paragraphs.
- Make each point as detailed as possible: don't just state what something is, explain it, provide context, give examples if relevant etc. 
- When writing each point, try and achieve the goal of maximising learner understanding as if they were learning each concept for the first time. 
- Do not include intros, summaries, or disclaimers.
- Your notes must be exam-focused and syllabus-aligned.
- Your response must not exceed {word_limit} words in total, while ensuring that every single syllabus point is still fully covered and explained.
"""
    else:
        prompt = f"""
You are an expert IGCSE {subject} tutor. Create a valid Mermaid.js flowchart based ONLY on the syllabus points below.

Syllabus points:
{syllabus_str}

Rules:
- Use the format: flowchart TD
- Use node connections to represent ideas.
- Keep it clear, simple, and structured.
- Do not wrap in triple backticks or include commentary.
"""

    def stream_notes():
        yield " " * 256
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                max_tokens=6000,
                temperature=0.5
            )

            last_yield_time = time.time()

            for chunk in response:
                content = chunk.choices[0].delta.content or ""
                print("STREAM CHUNK:", repr(content))  # Debug output
                if content:
                    yield content
                    last_yield_time = time.time()
                elif time.time() - last_yield_time > 3:
                    print("[Ping emitted]")
                    yield "[ping]\n"
                    sys.stdout.flush()
                    last_yield_time = time.time()
            print("[Stream ended]")
        except Exception as e:
            print("[Stream error]:", str(e))
            yield "\n[ERROR OCCURRED: {}]\n".format(str(e))

    return Response(stream_with_context(stream_notes()), mimetype="text/plain")

@app.route("/generate_paper", methods=["POST"])
def generate_paper():
    data = request.get_json()
    board = data.get('board')
    subject = data.get('subject')
    topic = data.get('topic')
    subtopic = data.get('subtopic')

    try:
        if topic == "all":
            topic_data = syllabus_data[board][subject]
            points = []
            for topic_section in topic_data.values():
                for pt in topic_section.values():
                    points.extend(pt)
        else:
            if subtopic == "full":
                topic_data = syllabus_data[board][subject][topic]
                points = []
                for pt in topic_data.values():
                    points.extend(pt)
            else:
                points = syllabus_data[board][subject][topic][subtopic]
    except KeyError:
        return jsonify({"error": "Invalid syllabus selection"}), 404

    syllabus_str = "\n".join(f"- {p}" for p in points)

    if topic == "all":
        paper_prompt = f"""
You are an experienced IGCSE examiner.

Generate a full-length IGCSE {subject} exam paper for {board}, using ONLY the syllabus points below:
{syllabus_str}

Instructions:
IMPORTANT: YOU MUST NOT EXCEED 7 QUESTION COMPONENTS TOTAL. Each question and each sub-question (e.g., 1a, 1b, 2a) counts as one full component. Do not write more than 7 in total. If you exceed 7 components, the task is considered incorrect.

1. Match the exact format and style of official past papers.
2. Include paper number, sections, question numbering, and instructions.
3. Use a variety of question types appropriate for the subject, exam board and IGCSE.
4. Show marks for each question (e.g., [3 marks]).
5. Do NOT include answers.
6. Be formal and concise.
7. Do NOT include any hints or state any suggestions for answers within the question. 
8. Do NOT write any text that is not directly related to the paper, including intros, warning messages etc.
Return only the paper content.
"""
    else:
        paper_prompt = f"""
You are an experienced IGCSE examiner.

Generate exam-style practice questions on the topic '{topic}' in {subject} for {board}, using ONLY the syllabus points below:
{syllabus_str}

Instructions:
IMPORTANT: YOU MUST NOT EXCEED 7 QUESTION COMPONENTS TOTAL. Each question and each sub-question (e.g., 1a, 1b, 2a) counts as one full component. Do not write more than 7 in total. If you exceed 7 components, the task is considered incorrect.

1. Include paper number, sections, question numbering, and instructions.
2. Use a variety of question types appropriate for the subject, exam board and IGCSE.
3. Show marks for each question (e.g., [3 marks]).
4. Do NOT include answers.
5. Be formal and concise.
6. Do NOT include any hints or state any suggestions for answers within the question.
7. Do NOT hallucinate information about the paper number (e.g, don't say 'Paper 2 ....' at the top of the questions).
8. Do NOT split the questions up into 'sections'. 
9. State the total number of marks available for the paper at the start of it. 
10. Do NOT write any text that is not directly related to the paper, including intros or warning messages etc.
Return only the questions.
"""

    def stream_paper():
        yield " " * 256
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": paper_prompt}],
            stream=True
        )

        last_yield_time = time.time()

        for chunk in response:
            content = chunk.choices[0].delta.content or ""
            if content:
                yield content
                last_yield_time = time.time()
            elif time.time() - last_yield_time > 5:
                yield "[ping]\n"
                sys.stdout.flush()
                last_yield_time = time.time()

    return Response(stream_with_context(stream_paper()), mimetype="text/plain")

@app.route("/generate_markscheme", methods=["POST"])
def generate_markscheme():
    data = request.get_json()
    paper_text = data.get("paper_text")

    if not paper_text:
        return jsonify({"error": "Missing paper content"}), 400

    prompt = f"""
Generate the complete mark scheme for the paper below.

Paper:
---
{paper_text}
---

Instructions: 
1. Use the same numbering and format. 
2. Provide correct answers in as much detail as possible. 
3. Provide exact mark allocations for every single mark within each question so that the user has complete clarity on how to score full marks.
4. When delivering mark allocation, give examples of what answers would score that mark for each mark for the question. 
5. ALWAYS deliver the mark scheme for ALL questions in the question paper. Every single question must be dealt with in the mark scheme without fail. 
6. Do NOT write any text that is not directly related to the mark scheme, including intros or warning messages.
"""

    def stream_markscheme():
        yield " " * 256
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            max_tokens=6000,
            temperature=0.5
        )

        last_yield_time = time.time()

        for chunk in response:
            content = chunk.choices[0].delta.content or ""
            if content:
                yield content
                last_yield_time = time.time()
            elif time.time() - last_yield_time > 5:
                yield "[ping]\n"
                sys.stdout.flush()
                last_yield_time = time.time()

    return Response(stream_with_context(stream_markscheme()), mimetype="text/plain")


@app.route("/chat_refine_notes", methods=["POST"])
def chat_refine_notes():
    data = request.json
    original_notes = data.get("original_notes")
    user_message = data.get("message")
    if not original_notes or not user_message:
        return jsonify({"error": "Missing input"}), 400
    prompt = f"""
You are an expert IGCSE study assistant.

Original Notes:
---
{original_notes}
---

Student Request: {user_message}

Instructions:
- Modify the relevant sections based on the student's request, but always return the full revised notes — not just the edited parts.
- Keep all other sections unchanged.
- Always return the full revised notes, not just a snippet.
- Preserve structure, headings, and formatting.
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful, precise IGCSE revision assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=3000
        )
        return jsonify({"refined_notes": resp.choices[0].message.content.strip()})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.route("/")
def serve_homepage():
    return send_from_directory("BETA", "index-1.html")

@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(os.path.join("BETA", "assets"), filename)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
