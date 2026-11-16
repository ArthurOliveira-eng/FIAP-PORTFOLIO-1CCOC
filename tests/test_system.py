"""Behavior tests using only Python's unittest."""
import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path
from src.agent import CitizenAgent
from src.config import KNOWLEDGE_PATH, QUESTIONS_PATH, ROOT
from src.evaluation import evaluate_case, load_cases
from src.knowledge_base import KnowledgeBase, KnowledgeBaseError, save_record
from src.response import TemplateError, generate_response
from src.search import search


class GuidanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.memory = KnowledgeBase.load(KNOWLEDGE_PATH)

    def agent(self, **kwargs):
        return CitizenAgent(self.memory, log_path=None, **kwargs)

    def test_all_question_contracts_for_both_templates(self):
        for template in ("template_a_v1", "template_b_v1"):
            for case in load_cases(QUESTIONS_PATH):
                with self.subTest(template=template, case=case["id"]):
                    row = evaluate_case(self.memory, case, template)
                    self.assertTrue(row["correct"], row)

    def test_related_navigation_across_three_subjects(self):
        agent = self.agent()
        self.assertEqual(agent.handle("1").status, "browse")
        self.assertEqual(agent.handle("D02").record_ids, ("D02",))
        self.assertIn("S05", agent.handle("related").record_ids)
        self.assertEqual(agent.handle("S05").record_ids, ("S05",))
        self.assertIn("S03", agent.handle("related").record_ids)
        self.assertEqual(agent.handle("S03").record_ids, ("S03",))

    def test_ambiguous_query_can_be_resolved(self):
        agent = self.agent()
        self.assertEqual(agent.handle("CPF").status, "ambiguous")
        self.assertEqual(agent.handle("D04").status, "match")

    def test_theme_filter_and_back(self):
        agent = self.agent()
        agent.handle("1")
        self.assertEqual(agent.handle("How do I recover my gov.br password?").status, "no_match")
        agent.handle("back")
        self.assertEqual(agent.handle("How do I recover my gov.br password?").record_ids, ("S02",))

    def test_no_prior_record_for_related(self):
        self.assertEqual(self.agent().handle("related").status, "invalid_option")

    def test_unknown_theme_and_non_text_input(self):
        self.assertEqual(search(self.memory, theme="unknown").status, "invalid_option")
        self.assertEqual(self.agent().handle(None).status, "invalid_input")

    def test_no_match_does_not_cite_a_fake_guidance_source(self):
        answer = self.agent().handle("How do I obtain a Canadian driving licence?")
        self.assertNotIn("https://", answer.text)
        self.assertIn("none consulted", answer.text)

    def test_old_records_have_freshness_warning(self):
        result = search(self.memory, "D01")
        today = date.fromisoformat(result.records[0]["verification_date"]) + timedelta(days=181)
        text = generate_response(result, self.memory, "template_b_v1", today=today)
        self.assertIn("Freshness warning:", text)

    def test_unknown_template_is_rejected(self):
        with self.assertRaises(TemplateError):
            self.agent(template="missing")

    def test_privacy_safe_telemetry(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            agent = CitizenAgent(self.memory, log_path=path)
            agent.handle("My CPF is 123.456.789-00 and email is alice@example.com")
            logged = path.read_text(encoding="utf-8")
            self.assertNotIn("123", logged)
            self.assertNotIn("alice", logged)
            self.assertNotIn("example.com", logged)
            event = json.loads(logged)
            for field in ("query", "matched_records", "template", "latency_ms", "status"):
                self.assertIn(field, event)

    def test_logging_failure_does_not_hide_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            parent_file = Path(directory) / "not-a-directory"
            parent_file.write_text("occupied", encoding="utf-8")
            agent = CitizenAgent(self.memory, log_path=parent_file / "events.jsonl")
            answer = agent.handle("D01")
            self.assertEqual(answer.status, "match")
            self.assertIsNotNone(answer.log_error)

    def test_reproducible_results(self):
        for query in ("CPF", "gov.br account", "Where can I access CRAS support?"):
            first = self.agent().handle(query)
            second = self.agent().handle(query)
            self.assertEqual((first.status, first.record_ids, first.text),
                             (second.status, second.record_ids, second.text))


class MemoryValidationTests(unittest.TestCase):
    def setUp(self):
        self.records = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))

    def assert_invalid(self, records):
        with self.assertRaises(KnowledgeBaseError):
            KnowledgeBase(records)

    def test_required_fields_types_and_graph(self):
        for field in ("id", "theme", "question", "summary_guidance", "reference", "verification_date",
                      "confirmation_warning", "keywords", "related_ids"):
            records = deepcopy(self.records)
            del records[0][field]
            with self.subTest(missing=field):
                self.assert_invalid(records)
        for field, value in (("theme", 4), ("keywords", "cin"), ("related_ids", [None]),
                             ("reference", "javascript:alert(1)"), ("reference", "https://gov.br.evil.com"),
                             ("reference", "https://gov.br:bad"), ("verification_date", "tomorrow"),
                             ("verification_date", "2999-01-01"), ("related_ids", ["X99"])):
            records = deepcopy(self.records)
            records[0][field] = value
            with self.subTest(field=field, value=value):
                self.assert_invalid(records)

    def test_duplicate_and_empty_memory(self):
        self.assert_invalid([])
        self.assert_invalid({})
        self.assert_invalid(self.records + [self.records[0]])

    def test_missing_empty_and_malformed_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "base.json"
            with self.assertRaises(KnowledgeBaseError):
                KnowledgeBase.load(path)
            for contents in ("", " ", "{bad", "null", "[42]"):
                path.write_text(contents, encoding="utf-8")
                with self.subTest(contents=contents), self.assertRaises(KnowledgeBaseError):
                    KnowledgeBase.load(path)

    def test_data_changes_need_no_core_rule_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "base.json"
            path.write_text(json.dumps(self.records), encoding="utf-8")
            original = deepcopy(self.records[0])
            new = {**original, "id": "D06", "question": "A newly verified guidance record"}
            save_record(path, new)
            self.assertIn("D06", KnowledgeBase.load(path).by_id)
            changed = {**original, "summary_guidance": "Corrected, verified guidance."}
            save_record(path, changed, replace=True)
            self.assertEqual(KnowledgeBase.load(path).by_id["D01"]["summary_guidance"], changed["summary_guidance"])
            unchanged = path.read_bytes()
            with self.assertRaises(KnowledgeBaseError):
                save_record(path, {**original, "reference": ""}, replace=True)
            self.assertEqual(path.read_bytes(), unchanged)


class CommandLineTests(unittest.TestCase):
    def run_cli(self, commands, *arguments, cwd=ROOT):
        return subprocess.run(
            [sys.executable, str(ROOT / "src" / "sistema.py"), "--no-log", *arguments],
            input=commands, capture_output=True, text=True, cwd=cwd, timeout=15,
        )

    def test_complete_cli_flow(self):
        result = self.run_cli("1\nD02\nrelated\nS05\nrelated\nS03\nback\n\n99\nCPF\nD04\nquit\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        for expected in ("Available themes:", "birth or marriage", "scan the CIN QR code",
                         "Bronze, Silver", "Invalid menu option", "Session ended."):
            self.assertIn(expected, result.stdout)

    def test_missing_file_exits_cleanly(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli("", "--knowledge", str(Path(directory) / "missing.json"))
            self.assertEqual(result.returncode, 1)
            self.assertIn("no guidance was invented", result.stderr)

    def test_runs_outside_repository_and_handles_eof(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli("D01\n", cwd=directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("unique identification number", result.stdout)


if __name__ == "__main__":
    unittest.main()
