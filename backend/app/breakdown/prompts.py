"""LLM prompts for Break It Down explanations.

All prompts enforce grounding: explanations may only use information
present in the provided concept definition, explanation, and examples.
No new facts may be introduced.

Each prompt also supports multilingual output — pass language_instruction
to the user prompt to request output in a specific language.
"""

# ── Shared system prompt ──────────────────────────────────────────────────────

BREAKDOWN_SYSTEM = """\
You are a patient, expert tutor helping a student understand a difficult concept
from a lecture they are watching.

STRICT RULES:
1. Only use facts, examples, and context from the provided concept data.
2. Do not introduce outside knowledge, real-world facts, or examples not
   mentioned in the lecture.
3. Keep your explanation concise: 2-4 sentences unless the style demands more.
4. If asked for a non-English language, write the ENTIRE response in that
   language — do not mix languages.
5. Always return ONLY valid JSON. No markdown, no preamble.
"""

# ── Per-style user prompts ────────────────────────────────────────────────────

_CONCEPT_BLOCK = """\
Concept name: {name}
Lecture definition: {definition}
Lecture explanation: {explanation}
Examples from lecture: {examples}
Evidence quote: {evidence_quote}
Timestamp in lecture: {timestamp:.0f}s
"""

_RETURN_BLOCK = """\
Return:
{{
  "explanation": "<your explanation here>",
  "source_quote": "<the single most relevant sentence from the evidence quote above>"
}}"""

BREAKDOWN_USER_SIMPLE = (
    _CONCEPT_BLOCK
    + """
Style: SIMPLER EXPLANATION
Rewrite the definition and explanation using everyday language.
Strip all technical jargon. Use short sentences. Avoid acronyms.
{language_instruction}
"""
    + _RETURN_BLOCK
)

BREAKDOWN_USER_ANALOGY = (
    _CONCEPT_BLOCK
    + """
Style: ANALOGY
Explain this concept by comparing it to something familiar and relatable
(everyday objects, common experiences). The analogy must relate to the
concept as described in the lecture — do not invent unrelated analogies.
{language_instruction}
"""
    + _RETURN_BLOCK
)

BREAKDOWN_USER_EXAMPLE = (
    _CONCEPT_BLOCK
    + """
Style: REAL-WORLD EXAMPLE
Show how this concept applies in a concrete scenario. Draw the scenario
directly from the examples the lecturer mentions, or extrapolate minimally
from the lecture explanation.
{language_instruction}
"""
    + _RETURN_BLOCK
)

BREAKDOWN_USER_PREREQUISITE = (
    _CONCEPT_BLOCK
    + """
Style: PREREQUISITE EXPLANATION
What background knowledge does a student need before they can understand
this concept? Based ONLY on the lecture definition and explanation,
identify 1-3 prerequisite ideas and briefly explain each in 1 sentence.
{language_instruction}
"""
    + _RETURN_BLOCK
)

BREAKDOWN_USER_DIAGRAM = (
    _CONCEPT_BLOCK
    + """
Style: DIAGRAM
Build a structured diagram that shows how this concept's components relate.
Use 3–7 nodes total. Assign level 0 to the root/central concept, level 1
to its direct sub-components, and level 2 to any details or sub-sub-components.
Edges should have short, verb-phrase labels (e.g. "feeds into", "produces").
Base ALL content strictly on the lecture data provided.
{language_instruction}

Return ONLY valid JSON — no markdown, no prose outside the JSON:
{{
  "explanation": {{
    "title": "<concept name>",
    "nodes": [
      {{"id": "1", "label": "<component>",     "description": "<5–8 word desc>", "level": 0}},
      {{"id": "2", "label": "<sub-component>", "description": "<5–8 word desc>", "level": 1}}
    ],
    "edges": [
      {{"from": "1", "to": "2", "label": "<relationship>"}}
    ]
  }},
  "source_quote": "<the single most relevant sentence from the evidence quote above>"
}}
"""
)

BREAKDOWN_USER_ELI5 = (
    _CONCEPT_BLOCK
    + """
Style: ELI5 (Explain Like I'm 5)
Explain this concept as if talking to a curious 5-year-old child.
Use very simple words, a friendly tone, and short sentences.
A metaphor involving toys, animals, or familiar childhood experiences
is encouraged — but only if it maps directly to the concept.
{language_instruction}
"""
    + _RETURN_BLOCK
)

# Map ExplanationStyle enum values → prompt templates
STYLE_PROMPT_MAP: dict[str, str] = {
    "simple":       BREAKDOWN_USER_SIMPLE,
    "analogy":      BREAKDOWN_USER_ANALOGY,
    "example":      BREAKDOWN_USER_EXAMPLE,
    "prerequisite": BREAKDOWN_USER_PREREQUISITE,
    "diagram":      BREAKDOWN_USER_DIAGRAM,
    "eli5":         BREAKDOWN_USER_ELI5,
}

# ── Language instruction fragment ─────────────────────────────────────────────

def language_instruction(lang_code: str, lang_name: str) -> str:
    if lang_code == "en":
        return ""
    return f"IMPORTANT: Write your ENTIRE response (all text values in the JSON) in {lang_name}. Do not use English."
