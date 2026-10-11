# nlp/

**Owner:** P3 Integration & language lead

**Stack:** Python 3.12 · rule-based parser + exact-match location resolver (primary, offline) · optional LLM extractor (Anthropic API, JSON output) behind a flag, with timeout + fallback (star)

| File | Purpose |
|------|---------|
| `nlp/__init__.py` | text -> structured disruption proposal |
| `nlp/resolver.py` | exact-match location/vehicle resolver: normalize case/space/punctuation, aliases, ambiguous -> reject |
| `nlp/time_grammar.py` | "10:30", "3pm", "until 14:00", "for 2 hours", "in 30 min" -> minutes since midnight |
| `nlp/rules.py` | rule-based extraction for road_closure / vehicle_failure / urgent_delivery |
| `nlp/interpreter.py` | interpret(text) -> Proposal with spans, assumptions, warnings, rejections |
| `nlp/llm_extractor.py` | OPTIONAL (star): Anthropic API extractor behind a flag; mention must appear verbatim and resolve exactly |
