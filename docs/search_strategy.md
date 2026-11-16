# Retrieval and navigation

The top-level list of JSON records is indexed in two dictionaries: by_id[id] → record and by_theme[theme] → list of records. A graph dictionary maps each ID to related IDs. Theme order follows first appearance in the base, so existing menu choices remain Documents, Digital services, Community support. New themes appear automatically.

Free-text algorithm:

1. Trim input. Empty/overlong input and menu errors are handled before retrieval.
2. Normalize Unicode accents, lowercase text, replace punctuation with word boundaries, remove documented stop words, and apply explicit synonyms in src/search.py.
3. For each record in the selected theme (or all records), build a token set from its question and keywords. Summaries are not searched, to avoid incidental personal or policy words dominating retrieval.
4. Coverage = matching distinct query tokens / distinct query tokens. Add 0.20 if a complete keyword alias with at least two informative tokens occurs in the query token set. The alias is a token-set comparison, not a word-order comparison. Maximum score is 1.20, not a probability.
5. Discard candidates below 0.46. Rank by descending score, then ID for stable ordering.
6. If more than one candidate is within 0.12 of the best score, return up to five clarification choices. A one-word query also requests clarification. Do not silently select the first tie.
7. Otherwise return the highest-ranked stored record and render its source and limitations.

Examples: CPF produces D03/D04 choices. CPF registration gives the registration record an alias bonus over status consultation. gov.br account yields creation/level clarification. A foreign driving-licence question yields no match. Changing the base does not require rule edits; adding synonyms is optional and must be evaluated.

An exact ID bypasses text ranking and may cross an active theme, supporting the related graph. A theme selection lists subtopics without claiming any guidance source was consulted yet. A free-text question within a theme stays filtered until back; this state cost is included in the task script.

Graph path: D02 → S05 → S03 connects issuing a CIN, using CIN in account validation, and understanding account security levels. S03 → C01 continues to a consumer service requiring an account level. C03/C04/C05 connect registration, updating, and local CRAS support. Edges mean useful related subjects and do not add facts or automatic eligibility rules.

Complexity: preprocessing is linear in input length. A query scans n records and compares small sets; roughly O(n × average record vocabulary), appropriate for this 15-record dataset. ID lookup is average O(1). Theme lookup is dictionary access followed by its record list. No search index service is needed.

Limitations: no embeddings, trained classifier, semantic entailment, fuzzy spelling, or automatic translation. A lexical match can be incomplete or fail on unfamiliar wording. Generic words can create ambiguity. Conservative fallbacks and fixed factual summaries reduce invention risk but do not guarantee perfect intent detection. The development-authored fixtures are not an independent benchmark.
