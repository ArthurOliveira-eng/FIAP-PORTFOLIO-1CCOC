# Citizen Assist AI

An independent, textual citizen-guidance prototype for Brazilian public services. English interface and documentation; original Brazilian service names and Portuguese source pages are retained where needed. No paid APIs, external language models, model training, or runtime network calls.

## 1. Team and submission status

| Field | Value |
| --- | --- |
| Project / provisional team name | Citizen Assist AI — team name awaiting confirmation |
| Repository owner | Arthur Apolonio de Oliveira |
| RM | Not supplied; must be completed before submission |
| Other members and RMs | Not supplied; confirm the full membership before submission |
| Public repository | https://github.com/ArthurOliveira-eng/FIAP-PORTFOLIO-1CCOC |
| YouTube demonstration (Unlisted) | Pending upload by the team; no fabricated link |

The prototype, evaluation runner, task scripts, and video generator are implemented. Submission is incomplete until the actual team/RMs and a working Unlisted YouTube URL are supplied. Local execution has been verified on Windows with Python 3.14; see [local validation](docs/local_validation.md). GitHub Actions results are labeled separately.

## 2. Problem, audience, and themes

Citizens often need to identify the relevant agency and the next safe step without navigating many portals. This assistant provides concise, source-linked orientation, not application processing, official support, personal legal advice, or eligibility decisions.

Target audience: people seeking basic Brazilian citizen-service orientation, students demonstrating responsible retrieval, and reviewers inspecting sources and algorithms. The English-only prototype is an academic constraint and a barrier for many Brazilian users.

| Theme | Records | Subjects |
| --- | --- | --- |
| Documents | D01–D05 | CIN overview and issuing, CPF registration and status, Digital Work Card |
| Digital services | S01–S05 | gov.br account creation, recovery, security levels, electronic signing, CIN validation |
| Community support | C01–C05 | Consumer complaints and evidence, Cadastro Unico registration and updating, CRAS |

## 3. Knowledge organization and retrieval

The JSON base contains 15 records. Each includes id, theme, question, keywords, summary_guidance, reference, verification_date, confirmation_warning, and related_ids. Sources were consulted on 2026-11-16; see [source review](docs/source_review.md). A verification date is a snapshot, not a guarantee that a live page remains unchanged.

Lists preserve record display order. Dictionaries index records by ID and theme. The hierarchy is theme → subject record; a directed adjacency dictionary links related records across themes. For example: D02 (CIN issuing) → S05 (CIN account validation) → S03 (security levels) → C01 (consumer complaint access). A related edge means useful continuation, not an official prerequisite in every case.

Search normalizes case, accents, and punctuation, removes common question words, applies a small explicit synonym dictionary, and compares token sets. The score is query-token coverage plus a 0.20 bonus for a complete multi-token keyword phrase. It is a ranking score, not a probability. Minimum score: 0.46. Candidates within 0.12 of the best score trigger clarification; ID order breaks display-order ties. A single informative word always requests clarification. Exact record IDs and theme selection support direct navigation. Full details: [search strategy](docs/search_strategy.md).

Add or correct the JSON records without editing search rules. Validation checks required fields/types, non-empty strings and keywords, duplicate IDs, official HTTPS source URLs, ISO verification dates, and valid graph references. Invalid snapshots fail closed with a readable message. The administrative save_record helper validates the whole snapshot before atomic replacement. See [maintenance](docs/maintenance.md).

## 4. Response rules and agent architecture

| Agent part | Implementation |
| --- | --- |
| Perception | CitizenAgent.perceive parses commands, theme numbers, IDs, and text |
| Reasoning | search normalizes input, filters a selected theme, ranks candidates, and requests clarification |
| Action | response renders a validated record with a versioned template |
| Memory | KnowledgeBase loads the verified JSON snapshot and indexes |
| Guardrails | No free-form fact generation; mandatory source, verification date, confirmation warning, limitation, and non-official notice |
| Observability | Privacy-safe JSONL query metadata, matched records, template name, status, and latency |

[Template A](prompts/template_a.txt) places the answer and required fields into a compact paragraph. [Template B](prompts/template_b.txt) uses separate labeled sections and is the default. Both share the same grounded facts and limits. Their instruction headers and rendering layouts are versioned as template_a_v1 and template_b_v1; only the text following the response delimiter is rendered. This is deterministic template filling, not an LLM prompt invocation. The evaluation compares the same questions under both templates and reports source/warning compliance, separate source lines, answer length, and maximum line length. Template B is preferred for scanability; structural proxies do not establish human preference.

Empty input and punctuation-only input request a useful question. Invalid menu options show available themes. Ambiguity lists possible record IDs. No match explicitly reports that no guidance source was consulted and suggests questions/themes. Input cannot alter system rules. The instruction-override filter is a limited extra safeguard; safety primarily comes from returning stored records instead of generating facts. Unknown instructions, fees, local addresses, deadlines, and personal decisions are never synthesized.

Every matched response includes the source and a confirmation warning. Records older than 180 days receive an additional freshness warning. Live sources are not fetched when answering. A loosely related result can still be incomplete: users must read the scope limitation and confirm details with the agency.

## 5. Test plan, measured indicators, and interpretation

The evaluation fixture contains 31 cases: all 15 records, rephrased questions, normalization, out-of-scope questions, empty and punctuation-only input, ambiguous queries, invalid menu input, overlong input, and an instruction-override request. Each is run for both templates (62 evaluations). Correctness requires the expected status, exact expected record IDs, expected answer fragments, and source/warning checks. These are functional retrieval tests, not an independent semantic accuracy benchmark.

Accuracy = correct / total. Query time uses perf_counter around a full agent handle call with the knowledge base already loaded and telemetry disabled; template file loading/rendering is included. Latency varies by hardware, cache state, and filesystem. CI and local results must not be compared as if environments were identical.

<!-- METRICS:START -->
Executed in **local**, Python 3.14.10, at 2026-11-16T23:19:49.066175+00:00.

| Template | Correct / total | Accuracy | Mean query time (ms) |
| --- | ---: | ---: | ---: |
| template_a_v1 | 31 / 31 | 100.00% | 0.529052 |
| template_b_v1 | 31 / 31 | 100.00% | 0.565581 |

Each template runs the same independent cases. Latency excludes knowledge loading and telemetry I/O, and includes rendering. See tests/results.json and tests/results.csv for the full expected/obtained table.
<!-- METRICS:END -->

The recorded table exports expected answer, obtained answer, correct/error classification, matched IDs, and individual time in tests/results.json and tests/results.csv; tests/results.md is a compact review table. tests/template_comparison.json records A/B comparison and example responses. Tests also cover missing/empty/malformed knowledge files, invalid schemas, graph references, updates, private logging, logging failures, EOF, running outside the project folder, and complete CLI flows.

Usability is evaluated using eight predefined task scripts through the real CLI, as permitted by the assignment. tests/usability_results.json records task completion rate, action counts, process time, and transcripts. There are zero human participants; process time is not human task time and no satisfaction score is invented. Anticipated difficulties include clarifying broad queries, selecting record IDs, and leaving theme filters. See [usability methodology](docs/usability.md).

Interpretation: high fixture accuracy demonstrates that the chosen examples obey their contracts. It does not establish broad language understanding, current policy completeness, eligibility correctness, or accessibility for real users. Template comparisons share retrieval and facts; they test formatting consistency rather than a model's reasoning.

## 6. How to run and test locally

Requires Python 3.10 or later. The application and tests use only the Python standard library. From the repository root:

```bash
python src/sistema.py
```

On Windows, use py -3 if python is not on PATH.

```bash
python -m unittest discover -s tests -v
python -m src.evaluation
python -m tests.run_usability
python scripts/create_demo.py --text-only
```

The first command verifies behavior. The next commands create the recorded evaluation, A/B comparison, usability report, and captured demonstration transcript. The evaluation also updates the measured-metrics block in this README. A failed comparison exits nonzero. Generated results reflect the environment in which they were actually run.

```bash
python src/sistema.py --template template_a_v1 --no-log
python src/sistema.py --knowledge data/knowledge_base.json
```

Commands: 1/2/3 select themes; a record ID (such as D02) opens guidance; related offers continuation; back clears the theme filter; help shows theme choices; quit or 0 exits. Free-text questions are filtered by the selected theme until back is used. Exact record IDs can cross themes, enabling related navigation.

GitHub Actions executes the same tests on Python 3.12 and uploads measured reports, a demonstration MP4, and an evidence bundle as artifacts. The workflow has read-only repository access and never commits generated files. Video generation alone additionally requires FFmpeg and a DejaVu Sans Mono font in the documented Linux location. These optional tools are not application dependencies. Actions artifacts expire after 30 days; download the video and upload it to YouTube before submission.

## 7. Examples, sources, and invalid input

Input: How do I recover my gov.br password?

> Use 'Esqueci minha senha' in the official gov.br sign-in flow. Follow the recovery methods offered for your account; use official support if those methods are unavailable.

Source: [Official gov.br recovery guidance](https://www.gov.br/governodigital/pt-br/acessibilidade-e-usuario/atendimento-gov.br/duvidas-na-conta-gov.br/recuperar-senha-da-conta-gov.br). The application additionally shows verification date, password/code privacy warning, limitations, and related subjects.

Input: Where can I access CRAS support?

> CRAS provides free basic social-assistance guidance, including information about social services, rights, and Cadastro Unico. Consult your municipality for the appropriate unit and appointment arrangements.

Source: [Official CRAS service page](https://www.gov.br/pt-br/servicos/acessar-o-cras-centro-de-referencia-da-assistencia-social). Confirm local opening hours and appointments with the municipality.

| Input | Behavior |
| --- | --- |
| Empty text | Requests a question or theme |
| 99 | Explains the invalid menu choice and lists themes |
| CPF | Offers registration/status clarification; choose D03 or D04 |
| Canadian driving licence question | States no reliable answer is stored and offers supported alternatives |
| 1 → D02 → related → S05 → related → S03 | Demonstrates three related subjects across themes |

## 8. Clarity, accessibility, privacy, and ethics

Plain labeled output works without colors, graphics, paid services, or network connectivity. The interface does not request names, RMs, CPF numbers, passwords, codes, addresses, or income. RMs are academic submission metadata, not application inputs. Consult official services directly when they legitimately require personal details.

Default logs contain only input length and controlled-vocabulary terms plus operational metadata; raw queries are never persisted. Logs are local, untracked, and can be disabled with --no-log. Even minimized logs may reveal topics of interest: delete logs/ when no longer needed and do not publish logs. There is no analytics service or external model transmission. Synthetic evaluation questions and outputs are intentionally public.

The prototype is not affiliated with government. It cannot schedule visits, authenticate users, access personal files, submit claims, or promise benefits. Sources are original Portuguese official pages; summaries are English paraphrases. Source conflicts, translations, and evolving policies require human review. See [AI-use disclosure](docs/uso_ia.md).

## 9. Demonstration and links file

The Actions evidence artifact includes citizen-assist-demo.mp4 when video generation succeeds. It is an automatically rendered demonstration of actual captured CLI output, not a human screen recording or user study. A local text-only demonstration requires no additional dependencies. See [video guide](docs/demo_script.md).

Unlisted YouTube URL: **pending team upload**. Replace the pending value here and in [SUBMISSION_LINKS.TXT](SUBMISSION_LINKS.TXT) with the real working URL. Publishing to YouTube requires the team's account; this repository does not claim that it has occurred.

## 10. Conclusions, limitations, and improvements

The agent demonstrates a complete perception → validation → retrieval → rendering → source/limitation flow using lists, dictionaries, file reading, logical operations, graph navigation, and reproducible procedures. These directly exercise foundational programming and the assignment's phase 4/5/6 emphasis; course-specific phase materials were not provided, so no unsupported syllabus mapping is asserted.

Limitations: only 15 curated records, English queries, lexical matching without learned semantics, no typo correction, no automatic policy refresh, no live integration, small development-authored fixtures, scripted rather than human usability testing, and environment-dependent timing. A related answer can be incomplete for a detailed question.

Prioritized improvements:

1. Run an independent test set and a real usability/accessibility session with Portuguese-speaking citizens; measure comprehension, completion, and difficulty.
2. Add reviewed Portuguese queries, broader paraphrases, and typo handling; tune thresholds on a development split and report results on an untouched test split.
3. Add a source-review queue with freshness tracking and curator approval; never accept automatically scraped policy changes without validation.
4. Improve navigation by making active theme state more visible and offering numbered clarification choices.

## Acceptance evidence

| Requirement | Evidence / remaining action |
| --- | --- |
| Public repository | Repository URL above |
| Minimum 15 records / 3 themes | data/knowledge_base.json |
| Modular Python and configurable memory | src/ and prompts/ |
| Hierarchy and three-subject continuation | Graph data, search_strategy.md, navigation regression |
| Two prompt templates and comparison | prompts/; evaluation-generated template_comparison.json |
| Direct/rephrased/out-of-scope + limitation tests | tests/test_questions.json; regression suite |
| Accuracy, time, expected/obtained table | Generated results.json/.csv/.md and README metrics block |
| Usability with task script | Eight tasks and generated usability_results.json |
| AI-use and critical verification | docs/uso_ia.md; docs/source_review.md |
| Local testing | Verified on Windows / Python 3.14; see docs/local_validation.md |
| Video / Unlisted YouTube | MP4 generator supplied; YouTube upload and actual URL still required |
| Team/RMs and TXT submission | Fill missing member data and YouTube URL before submission |

Repository layout follows the supplied structure. The original assignment's missing Table 2 was not reconstructed or invented.
