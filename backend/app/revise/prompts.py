"""LLM prompts for Revise Mode (flashcard gen, quiz gen, oral exam eval).

All prompts enforce transcript-grounding:
  - Every answer must cite a verbatim excerpt from the provided evidence.
  - No outside facts, examples, or elaborations may be introduced.
  - All timestamp fields must use the exact values provided in the input.
"""

# ── Shared system ─────────────────────────────────────────────────────────────

EXAM_COACH_SYSTEM = """\
You are an expert exam coach creating study materials from a lecture transcript.

GROUNDING RULES (strictly enforced):
1. Every answer/explanation must be supported by the provided lecture evidence.
2. Never add facts, examples, or claims not present in the provided data.
3. timestamp_start fields MUST use the exact float provided — do not change them.
4. Return ONLY valid JSON. No markdown, no preamble.
"""


# ── Flashcard generation ──────────────────────────────────────────────────────

FLASHCARD_GEN_USER = """\
Concept: {name}
Importance: {importance}
Transcript definition: {definition}
Transcript explanation: {explanation}
Examples from lecture: {examples}
Evidence quote: {evidence_quote}
Timestamp: {timestamp:.1f}s

Generate {n_cards} flashcard(s) for this concept.

Card types to produce (in order):
1. surface  — "What is {name}?" → definition from transcript
2. deep     — Why/how/when question that tests understanding, not just recall
3. application — (only if n_cards=3) Give a scenario from the lecture, ask which concept applies or how to use it

For each card return:
{{
  "question_type": "surface" | "deep" | "application",
  "front": "the question",
  "back": "the answer (only from transcript evidence)",
  "difficulty": "easy" | "medium" | "hard",
  "hint": "1-sentence nudge (optional, null if not helpful)",
  "evidence_quote": "verbatim quote from transcript that directly supports the back"
}}

Return: {{"flashcards": [...]}}"""


# ── Quiz generation ───────────────────────────────────────────────────────────

QUIZ_GEN_SYSTEM = """\
You are an exam question writer creating multiple-choice and true/false questions
from a lecture transcript.

GROUNDING RULES:
1. All correct answers must be directly supported by the provided transcript evidence.
2. Wrong options (distractors) must be plausible but clearly wrong per the transcript.
3. Never invent facts — distractors must relate to the topic but be wrong.
4. Every question must include an explanation citing the evidence quote.
5. Return ONLY valid JSON.
"""

QUIZ_GEN_USER = """\
Concept: {name}
Importance: {importance}
Definition: {definition}
Explanation: {explanation}
Examples: {examples}
Evidence quote: {evidence_quote}
Timestamp: {timestamp:.1f}s

Generate {n_questions} quiz question(s).
Mix MCQ (preferred for core concepts) and true/false.

For MCQ:
{{
  "question_type": "multiple_choice",
  "question_text": "...",
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "correct_answer": "A",
  "explanation": "The correct answer is A because... [cite evidence quote]",
  "evidence_quote": "verbatim from transcript",
  "difficulty": "easy" | "medium" | "hard"
}}

For true/false:
{{
  "question_type": "true_false",
  "question_text": "True or false: ...",
  "options": null,
  "correct_answer": "True" | "False",
  "explanation": "...",
  "evidence_quote": "...",
  "difficulty": "easy" | "medium" | "hard"
}}

Return: {{"questions": [...]}}"""


# ── Batch flashcard generation (all concepts in one LLM call) ────────────────
# Replaces N individual FLASHCARD_GEN_USER calls with 1 call per 10-concept batch.

BATCH_FLASHCARD_SYSTEM = """\
You are creating study flashcards for multiple lecture concepts in one pass.
Every answer must be grounded only in the provided lecture evidence.
Return ONLY valid JSON. No markdown, no preamble.
"""

BATCH_FLASHCARD_USER = """\
Generate flashcards for the concepts below. Each entry specifies how many cards to create.

Card types (in priority order):
1. surface  — "What is X?" → definition from the transcript
2. deep     — Why/how/when question that tests understanding, not just recall
3. application — (only for 3-card concepts) A scenario from the lecture; apply the concept

{concepts_block}

Return:
{{
  "results": [
    {{
      "concept_name": "exact concept name",
      "cards": [
        {{
          "question_type": "surface" | "deep" | "application",
          "front": "the question",
          "back": "the answer (transcript-grounded only)",
          "difficulty": "easy" | "medium" | "hard",
          "hint": "1-sentence nudge or null",
          "evidence_quote": "verbatim transcript quote supporting the back"
        }}
      ]
    }}
  ]
}}"""


# ── Batch quiz generation (all concepts in one LLM call) ─────────────────────

BATCH_QUIZ_SYSTEM = """\
You are writing exam questions for multiple lecture concepts in one pass.
All correct answers must be directly supported by the provided transcript evidence.
Distractors must be plausible but clearly wrong per the transcript. No outside facts.
Return ONLY valid JSON.
"""

BATCH_QUIZ_USER = """\
Generate quiz questions for the concepts below. Each entry specifies how many questions.
Mix MCQ (preferred for core) and true/false.

{concepts_block}

For MCQ return options as ["A. ...", "B. ...", "C. ...", "D. ..."] and correct_answer as "A"/"B"/etc.
For true/false return options as null and correct_answer as "True" or "False".

Return:
{{
  "results": [
    {{
      "concept_name": "exact concept name",
      "questions": [
        {{
          "question_type": "multiple_choice" | "true_false",
          "question_text": "...",
          "options": [...] or null,
          "correct_answer": "...",
          "explanation": "why this is correct, citing evidence quote",
          "evidence_quote": "verbatim transcript quote",
          "difficulty": "easy" | "medium" | "hard"
        }}
      ]
    }}
  ]
}}"""


# ── Oral exam questions ───────────────────────────────────────────────────────

ORAL_QUESTION_TEMPLATES = [
    "Define {name} as explained in this lecture and describe its significance.",
    "In your own words, explain how {name} works based on what the lecturer said.",
    "What does the lecturer say distinguishes {name} from related concepts?",
    "Give an example of {name} that the lecturer used and explain why it illustrates the concept.",
    "What are the key properties of {name} according to the lecture?",
]


# ── Oral exam evaluation ──────────────────────────────────────────────────────

ORAL_EVAL_SYSTEM = """\
You are a strict but fair professor evaluating a student's oral exam answer.

EVALUATION RULES:
1. Compare the student's answer ONLY against the provided lecture evidence.
2. Do not penalise for outside knowledge — only check if key lecture points are covered.
3. Be specific: name exactly which points are strong and which are missing.
4. Cite the exact timestamp and quote that supports each piece of feedback.
5. Score: 0=no understanding, 50=partial, 80=good, 100=complete and accurate.
6. Return ONLY valid JSON.
"""

ORAL_EVAL_USER = """\
Concept being tested: {name}
Lecture definition: {definition}
Lecture explanation: {explanation}
Key evidence: {evidence_quote}
Timestamp: {timestamp:.1f}s
Expected key points:
{expected_points}

Student's answer:
"{student_answer}"

Evaluate the answer. Return:
{{
  "score": <0-100 integer>,
  "feedback": "1-2 sentence overall assessment",
  "strong_points": ["point the student got right (cite transcript)", ...],
  "missed_points": ["important point not covered", ...],
  "timestamp_citations": [
    {{"ts": {timestamp:.1f}, "quote": "relevant transcript quote"}}
  ],
  "suggested_review_ts": {timestamp:.1f}
}}"""
