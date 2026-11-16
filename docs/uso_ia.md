# AI use and critical validation

## Tools and uses

OpenAI ChatGPT/Codex assisted with Python module design, lexical search implementation, prompt/response templates, fixture drafting, test planning, documentation, and review of expected behaviors. The connected GitHub tool was used to inspect the repository and prepare/publish code. Web browsing was used to consult official Brazilian government sources. No external model is called by the finished prototype.

## Validation approach

Each summary was checked against official source descriptions rather than accepted solely because an AI proposed it. Required fields, official-source URL format, dates, and graph edges are validated in Python. The summaries are deliberately short and contain no individualized decisions. Detailed factual provenance and a source inconsistency are recorded in source_review.md.

Evaluation compares expected retrieval IDs/statuses and required answer content with actual output for both versioned templates. Regression tests also exercise input errors, malformed knowledge, cross-theme navigation, source warnings, data maintenance, privacy-safe telemetry, and CLI subprocess flows. Only executed reports count as measured evidence. The environment label distinguishes local execution from GitHub Actions. No timing, participant, satisfaction, YouTube link, or passing result is fabricated.

## What the team must understand and review

Before submission, every member should be able to explain token normalization, query coverage and alias bonuses, ambiguity thresholds, lists/dictionaries, graph edges, source-based template filling, error handling, and metric calculation. The repository explains these decisions and includes reproducible commands. AI assistance does not establish that the team has already understood or independently validated all of them; member review and RM completion remain their responsibility.

Review expected answers critically, rerun tests locally, inspect obtained answer text and source pages, and challenge fixtures with new questions. The same assistant helped author code and tests, so correlated blind spots remain. High fixture accuracy is not proof of production readiness or independent accuracy.

## Privacy and limits

The prototype does not send queries to a model, does not collect application documents, and does not claim agency affiliation. Raw input is not written to logs. Controlled-vocabulary query metadata and synthetic test outputs are documented. The optional scripted video contains only synthetic demo inputs.

If a future version adds a generative model, validate every factual claim and cited URL against the curated record, reject unsupported output, and obtain an explicit privacy design review. Do not treat this prototype's current deterministic guarantees as evidence for a future LLM integration.
