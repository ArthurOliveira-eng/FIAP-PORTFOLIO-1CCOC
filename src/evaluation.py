"""Avaliação reproduzível, comparação A/B e relatórios estruturados."""
import csv
import hashlib
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from time import perf_counter
from src.agent import CitizenAgent
from src.cli import ArgumentParser
from src.config import DEFAULT_TEMPLATE, KNOWLEDGE_PATH, PROMPT_PATHS, QUESTIONS_PATH, RESULTS_PATH, ROOT
from src.knowledge_base import KnowledgeBase, KnowledgeBaseError


def load_cases(path):
    try:
        cases = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Não foi possível carregar as perguntas de teste: {exc}") from exc
    if not isinstance(cases, list) or not cases:
        raise ValueError("As perguntas de teste devem ser uma lista não vazia.")
    ids = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("Cada caso de teste deve ser um objeto.")
        for key in ("id", "category", "input", "expected_status", "expected_answer"):
            if not isinstance(case.get(key), str):
                raise ValueError(f"O campo de teste {key} deve ser um texto.")
        for key in ("expected_ids", "expected_contains"):
            value = case.get(key)
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                raise ValueError(f"O campo de teste {key} deve ser uma lista de textos.")
        if case["id"] in ids:
            raise ValueError("Os IDs dos casos de teste devem ser únicos.")
        ids.add(case["id"])
    return cases


def evaluate_case(memory, case, template):
    agent = CitizenAgent(memory, template=template, log_path=None)
    started = perf_counter()
    answer = agent.handle(case["input"])
    duration = (perf_counter() - started) * 1000
    actual_ids = list(answer.record_ids)
    ids_match = (
        actual_ids == case["expected_ids"] if case.get("ids_ordered", True)
        else sorted(actual_ids) == sorted(case["expected_ids"])
    )
    content_match = all(fragment in answer.text for fragment in case["expected_contains"])
    source_ok = (
        all(memory.by_id[identifier]["reference"] in answer.text for identifier in answer.record_ids)
        and "Aviso:" in answer.text and "não é um canal oficial" in answer.text
    ) if answer.status == "match" else "Fonte:" in answer.text
    correct = answer.status == case["expected_status"] and ids_match and content_match and source_ok
    return {
        "id": case["id"], "category": case["category"], "input": case["input"],
        "template": template, "expected_answer": case["expected_answer"],
        "expected_status": case["expected_status"], "expected_ids": case["expected_ids"],
        "obtained_status": answer.status, "obtained_ids": actual_ids,
        "obtained_answer": answer.text, "classification": "correta" if correct else "erro",
        "correct": correct, "checks": {
            "ids": ids_match, "required_content": content_match, "source_guardrail": source_ok,
        },
        "query_time_ms": round(duration, 6),
    }


def summarize(rows):
    return {
        "total": len(rows), "correct": sum(row["correct"] for row in rows),
        "accuracy_rate": sum(row["correct"] for row in rows) / len(rows),
        "average_query_time_ms": round(mean(row["query_time_ms"] for row in rows), 6),
    }


def template_comparison(rows):
    comparison = {}
    for template in PROMPT_PATHS:
        matches = [row for row in rows if row["template"] == template and row["obtained_status"] == "match"]
        comparison[template] = {
            "matched_answers": len(matches),
            "source_and_warning_rate": mean(row["checks"]["source_guardrail"] for row in matches) if matches else 0,
            "mean_answer_characters": round(mean(len(row["obtained_answer"]) for row in matches), 2) if matches else 0,
            "mean_longest_line_characters": round(mean(
                max(map(len, row["obtained_answer"].splitlines())) for row in matches
            ), 2) if matches else 0,
            "separate_source_line_rate": mean(
                any(line.startswith("Fonte: https://") for line in row["obtained_answer"].splitlines())
                for row in matches
            ) if matches else 0,
        }
    return {
        "method": "Indicadores estruturais de clareza nas mesmas perguntas; não é um estudo de preferência humana.",
        "templates": comparison, "selected_template": DEFAULT_TEMPLATE,
        "justification": "O modelo B separa resposta, fonte, aviso, limitação e navegação. "
        "O modelo A é compacto, mas reúne campos importantes em um parágrafo longo. "
        "Ambos usam os mesmos fatos recuperados; estes indicadores não comprovam usabilidade real.",
        "examples": [row for row in rows if row["id"] in ("Q07", "Q12", "Q22")],
    }


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_readme(report):
    path = ROOT / "README.md"
    if not path.exists():
        return
    start, end = "<!-- METRICS:START -->", "<!-- METRICS:END -->"
    content = path.read_text(encoding="utf-8")
    if start not in content or end not in content:
        return
    rows = [
        "| Modelo de resposta | Corretas / total | Taxa de acerto | Tempo médio de consulta (ms) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for template, values in report["metrics_by_template"].items():
        rows.append(
            f"| {template} | {values['correct']} / {values['total']} | "
            f"{values['accuracy_rate']:.2%} | {values['average_query_time_ms']:.6f} |".replace(".", ",")
        )
    block = (
        "\nExecução em ambiente **" + report["environment"] + "**, com Python " + report["python_version"]
        + ", em " + report["executed_at"] + ".\n\n" + "\n".join(rows)
        + "\n\nCada modelo executa os mesmos casos independentes. A latência exclui o carregamento "
        "da base e a entrada/saída da telemetria, mas inclui a apresentação da resposta. "
        "Consulte `tests/results.json` e `tests/results.csv` para a tabela completa de "
        "resultados esperados e obtidos.\n"
    )
    content = content.split(start, 1)[0] + start + block + end + content.split(end, 1)[1]
    path.write_text(content, encoding="utf-8")


def run_evaluation(cases_path=QUESTIONS_PATH, results_path=RESULTS_PATH):
    memory = KnowledgeBase.load(KNOWLEDGE_PATH)
    cases = load_cases(cases_path)
    rows = [evaluate_case(memory, case, template) for template in PROMPT_PATHS for case in cases]
    metrics = {template: summarize([row for row in rows if row["template"] == template]) for template in PROMPT_PATHS}
    report = {
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "environment": "github-actions" if os.environ.get("GITHUB_ACTIONS") == "true" else "local",
        "python_version": platform.python_version(), "platform": platform.platform(),
        "source_commit": os.environ.get("GITHUB_SHA", "não informado"),
        "knowledge_sha256": hashlib.sha256(KNOWLEDGE_PATH.read_bytes()).hexdigest(),
        "cases_sha256": hashlib.sha256(Path(cases_path).read_bytes()).hexdigest(),
        "methodology": "Comparação exata de estado e IDs, conteúdo obrigatório e verificações de fonte e aviso. "
        "Nova sessão por caso; tempo medido com perf_counter em handle(); sem gravar telemetria.",
        "metrics_by_template": metrics,
        "metrics_by_category": {
            category: summarize([row for row in rows if row["category"] == category])
            for category in sorted({row["category"] for row in rows})
        },
        "results": rows,
    }
    results_path = Path(results_path)
    write_json(results_path, report)
    write_json(results_path.with_name("template_comparison.json"), template_comparison(rows))
    with results_path.with_suffix(".csv").open("w", newline="", encoding="utf-8") as output:
        fields = ["id", "category", "template", "expected_answer", "expected_status", "expected_ids",
                  "obtained_status", "obtained_ids", "obtained_answer", "classification", "query_time_ms"]
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    table = [
        "| Caso | Modelo | Esperado | Obtido | Resultado | Tempo (ms) |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for row in rows:
        expected = row["expected_status"] + " " + ",".join(row["expected_ids"])
        obtained = row["obtained_status"] + " " + ",".join(row["obtained_ids"])
        table.append(f"| {row['id']} | {row['template']} | {expected} | {obtained} | "
                     f"{row['classification']} | {row['query_time_ms']:.6f} |")
    results_path.with_suffix(".md").write_text(
        "# Avaliação registrada\n\nO texto completo das respostas está em results.csv/results.json.\n\n" + "\n".join(table) + "\n",
        encoding="utf-8",
    )
    update_readme(report)
    return report


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--casos", "--cases", dest="cases", type=Path, default=QUESTIONS_PATH,
                        metavar="ARQUIVO", help="Arquivo JSON com os casos de teste.")
    parser.add_argument("--saida", "--output", dest="output", type=Path, default=RESULTS_PATH,
                        metavar="ARQUIVO", help="Arquivo de saída dos resultados.")
    args = parser.parse_args()
    try:
        report = run_evaluation(args.cases, args.output)
    except (KnowledgeBaseError, ValueError, OSError) as exc:
        parser.exit(2, f"Não foi possível executar a avaliação: {exc}\n")
    print(json.dumps(report["metrics_by_template"], indent=2))
    return 0 if all(row["correct"] for row in report["results"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
