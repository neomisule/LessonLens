"""All LLM prompts for the Learn Mode pipeline.

Every prompt enforces grounding rules:
  - Only reference information present in the provided transcript context.
  - Always include the exact timestamp_start from the segment you're describing.
  - Never invent examples, definitions, or claims not in the transcript.
"""

# ── Concept extraction ────────────────────────────────────────────────────────

CONCEPT_EXTRACTION_SYSTEM = """\
You are an expert educational content analyst extracting concepts from lecture transcripts.

GROUNDING RULES (strictly enforced):
1. Only extract concepts that are explicitly defined, explained, or introduced in the provided segment.
2. Definitions must be paraphrased or quoted from the transcript — no outside knowledge.
3. Examples must come from the transcript — list only examples the lecturer mentions.
4. The timestamp_start field MUST be the exact start time provided in the segment header.
5. If a concept is only briefly mentioned without explanation, mark it as "supplemental".

Return ONLY valid JSON. No markdown, no commentary."""

CONCEPT_EXTRACTION_USER = """\
Segment [{index}] — timestamp {start:.1f}s to {end:.1f}s:
---
{text}
---

Extract up to 3 key concepts from this segment. For each concept return:
{{
  "name": "exact term as used",
  "definition": "definition as stated in the lecture",
  "explanation": "how it is explained in this segment",
  "examples": ["any examples the lecturer mentions"],
  "importance": "core" | "supporting" | "supplemental",
  "tags": ["1-3 subject area tags"],
  "timestamp_start": {start:.1f},
  "evidence_quote": "verbatim sentence from transcript that best defines/introduces this concept"
}}

Return: {{"concepts": [...]}}"""


# ── Chapter detection ─────────────────────────────────────────────────────────

CHAPTER_DETECTION_SYSTEM = """\
You are analyzing a lecture to identify its natural chapter structure.

RULES:
1. A chapter is a sustained focus on a distinct topic — not every paragraph.
2. Identify 3-8 chapters total (more for long lectures, fewer for focused ones).
3. Chapter titles should be descriptive noun phrases (5-8 words).
4. The timestamp_start of a chapter MUST match the exact start time of the
   first segment in that chapter (from the data provided).
5. Summaries must only summarize what is present in the listed segments.

Return ONLY valid JSON."""

CHAPTER_DETECTION_USER = """\
Lecture segments (index | start_time | preview):
{segments_outline}

Total segments: {total}
Approximate lecture duration: {duration_str}

Identify the chapter structure. Return:
{{
  "chapters": [
    {{
      "title": "Descriptive Chapter Title",
      "summary": "1-2 sentence summary of what this chapter covers.",
      "first_segment_index": <int>,
      "last_segment_index": <int>
    }}
  ]
}}"""


# ── Summary generation ────────────────────────────────────────────────────────

SUMMARY_SYSTEM = """\
You are creating structured educational summaries of a lecture.

GROUNDING RULES (strictly enforced):
1. Every section MUST correspond to an actual part of the lecture.
2. timestamp_start MUST be the start time of the first segment this section covers.
3. Never add claims, facts, or examples not present in the provided transcript context.
4. key_points must be bullet-form claims directly supported by the transcript.
5. The overall content field must read as a coherent standalone paragraph.

Return ONLY valid JSON."""

SUMMARY_USER_BRIEF = """\
Lecture title: {title}
Duration: {duration_str}

Transcript context (semantic segments with timestamps):
{context}

Generate a BRIEF summary (90-second read, ~400 words).
Cover only the 3-5 most essential points of the entire lecture.

Return:
{{
  "title": "Concise lecture title",
  "content": "2-3 paragraph executive summary of the entire lecture.",
  "sections": [
    {{
      "heading": "Section heading",
      "content": "1-2 sentences covering this key point.",
      "timestamp_start": <float from context>,
      "timestamp_end": <float or null>,
      "key_points": ["one bullet claim per key point"]
    }}
  ]
}}
Aim for 3-4 sections."""

SUMMARY_USER_STANDARD = """\
Lecture title: {title}
Duration: {duration_str}

Transcript context (semantic segments with timestamps):
{context}

Key concepts already extracted:
{concepts_brief}

Generate a STANDARD summary (5-minute read, ~1200 words).
Cover all main topics with clear explanations.

Return:
{{
  "title": "Descriptive lecture title",
  "content": "3-4 paragraph overview summarizing the entire lecture.",
  "sections": [
    {{
      "heading": "Section heading",
      "content": "2-4 sentences explaining this topic.",
      "timestamp_start": <float>,
      "timestamp_end": <float or null>,
      "key_points": ["up to 4 bullet points per section"]
    }}
  ]
}}
Aim for 5-7 sections."""

SUMMARY_USER_DETAILED = """\
Lecture title: {title}
Duration: {duration_str}

Full transcript context (all semantic segments):
{context}

All extracted concepts:
{concepts_full}

Generate a DETAILED summary (full coverage, ~2500 words).
Cover every concept, all examples the lecturer gives, and transitions between topics.

Return:
{{
  "title": "Full descriptive title",
  "content": "4-5 paragraph comprehensive overview.",
  "sections": [
    {{
      "heading": "Section heading",
      "content": "Full explanation of this topic with all context provided.",
      "timestamp_start": <float>,
      "timestamp_end": <float or null>,
      "key_points": ["all key points and examples from this section"]
    }}
  ]
}}
Aim for 8-12 sections."""


# ── Multi-segment concept extraction (batch mode) ────────────────────────────
# Replaces the old single-segment CONCEPT_EXTRACTION_USER prompt.
# Sends BATCH_SIZE segments in one LLM call to reduce API round-trips.

CONCEPT_EXTRACTION_MULTI_USER = """\
Below are {n_segments} lecture segments from {first_start:.1f}s to {last_end:.1f}s.

{segments_block}

GROUNDING RULES:
1. Only extract concepts explicitly defined or introduced in the segment shown.
2. Definitions must come from the transcript — no outside knowledge.
3. The timestamp_start field MUST be the exact start time from the segment header.
4. For each result, segment_index must match the index in the === header.

For each segment, extract up to 3 key concepts. Return:
{{
  "results": [
    {{
      "segment_index": <int matching the segment header>,
      "concepts": [
        {{
          "name": "exact term as used",
          "definition": "definition as stated in the lecture",
          "explanation": "how it is explained in this segment",
          "examples": ["examples the lecturer mentions"],
          "importance": "core" | "supporting" | "supplemental",
          "tags": ["1-3 subject area tags"],
          "timestamp_start": <exact float from segment header>,
          "evidence_quote": "verbatim sentence from transcript"
        }}
      ]
    }}
  ]
}}"""


# ── Combined concept enrichment (why-it-matters + relations, single batch) ────
# Replaces N individual why_it_matters calls + 1 relations call with 1 call.

CONCEPT_ENRICHMENT_SYSTEM = """\
You are enriching metadata for lecture concepts. For each concept:
1. Write a specific why_it_matters statement (1-2 sentences, real-world relevance, no generic phrases).
2. List prerequisite concept names from this lecture that must be understood first.
3. List related concept names from this lecture discussed alongside this one.
Base everything only on the data provided. Return ONLY valid JSON."""

CONCEPT_ENRICHMENT_USER = """\
Concepts from this lecture:
{concepts_block}

Return:
{{
  "results": [
    {{
      "name": "exact concept name",
      "why_it_matters": "1-2 sentence specific real-world relevance",
      "prerequisites": ["other concept name from list", ...],
      "related": ["other concept name from list", ...]
    }}
  ]
}}"""


# ── Why it matters ────────────────────────────────────────────────────────────

WHY_IT_MATTERS_SYSTEM = """\
You are a student advisor explaining real-world relevance of academic concepts.
Write for a student who wants to understand WHY they should care about this concept.
Be specific — connect the concept to its practical applications or significance.
Keep it to 1-2 sentences. Do not use generic phrases like "this is important because…"
Return ONLY valid JSON."""

WHY_IT_MATTERS_USER = """\
Concept: {name}
Definition (from lecture): {definition}
Lecture context: {explanation}
Tags: {tags}

Return: {{"why_it_matters": "1-2 sentence explanation of real-world relevance."}}"""


# ── Concept relationship detection ────────────────────────────────────────────

CONCEPT_RELATIONS_SYSTEM = """\
You are analyzing relationships between concepts extracted from a lecture.
Only identify relationships that are supported by the lecture content.
A prerequisite is a concept that must be understood before the current one.
A related concept appears alongside or is contrasted with the current one in the lecture.
Return ONLY valid JSON."""

CONCEPT_RELATIONS_USER = """\
All concepts from this lecture:
{all_concepts}

For each concept, identify:
- prerequisites: concept names that must be understood first
- related: concept names frequently discussed alongside this one

Return:
{{
  "relations": [
    {{
      "name": "concept name",
      "prerequisites": ["name1", ...],
      "related": ["name2", ...]
    }}
  ]
}}"""
