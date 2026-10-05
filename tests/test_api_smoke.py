"""Offline checks against the published Agno baseline, without model requests."""

import ast
import asyncio
import importlib
import importlib.util
import inspect
import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "plugins/agno/skills/agno/references"
HAS_AGNO = importlib.util.find_spec("agno") is not None


def blocks(name):
    return re.findall(
        r"^```python[^\n]*\n(.*?)^```\s*$", (REFERENCES / name).read_text(), re.M | re.S
    )


@unittest.skipUnless(HAS_AGNO, "Install requirements-smoke.txt for Agno API checks")
class AgnoExampleTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {"AGNO_TELEMETRY": "false"})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        original = Path.cwd()
        os.chdir(temporary.name)
        self.addCleanup(os.chdir, original)
        # Failing closed catches accidental execution while importing doc examples.
        for target in (
            "agno.agent.Agent.run",
            "agno.agent.Agent.arun",
            "agno.team.Team.run",
            "agno.team.Team.arun",
            "socket.socket.connect",
            "httpx.Client.request",
            "httpx.AsyncClient.request",
        ):
            guard = patch(
                target,
                side_effect=AssertionError(
                    "Live calls are forbidden in offline smoke tests"
                ),
            )
            guard.start()
            self.addCleanup(guard.stop)

    def load(self, name, index=0, namespace=None):
        namespace = namespace if namespace is not None else {"__name__": "doc_example"}
        exec(
            compile(blocks(name)[index], f"{name}:block-{index + 1}", "exec"), namespace
        )
        return namespace

    def test_fenced_agno_imports_and_constructor_keywords(self):
        checked = 0
        for path in REFERENCES.glob("*.md"):
            for code in blocks(path.name):
                tree = ast.parse(code)
                imports = {}
                for node in ast.walk(tree):
                    if (
                        isinstance(node, ast.ImportFrom)
                        and node.module
                        and node.module.startswith("agno.")
                    ):
                        module = importlib.import_module(node.module)
                        for alias in node.names:
                            imports[alias.asname or alias.name] = getattr(
                                module, alias.name
                            )
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                        target = imports.get(node.func.id)
                        if inspect.isclass(target):
                            # Bind only the supplied keywords, without constructing external services.
                            with self.subTest(file=path.name, constructor=node.func.id):
                                inspect.signature(target).bind_partial(
                                    **{
                                        arg.arg: None
                                        for arg in node.keywords
                                        if arg.arg
                                    }
                                )
                            checked += 1
        self.assertGreater(checked, 20)

    def test_sdk_starters_construct_without_running_models(self):
        from agno.agent import Agent

        for index in range(len(blocks("examples.md"))):
            with self.subTest(block=index):
                self.assertIsInstance(self.load("examples.md", index)["agent"], Agent)

    def test_streaming_helpers_are_sync_and_async(self):
        namespace = self.load("agents.md")
        self.assertFalse(inspect.iscoroutinefunction(namespace["stream_answer"]))
        self.assertTrue(inspect.iscoroutinefunction(namespace["astream_answer"]))

    def test_team_modes_construct(self):
        from agno.team import TeamMode

        namespace = self.load("teams.md")
        self.load("teams.md", 1, namespace)
        self.assertEqual(namespace["team"].mode, TeamMode.coordinate)
        self.assertEqual(namespace["router"].mode, TeamMode.route)
        self.assertEqual(namespace["review_team"].mode, TeamMode.broadcast)
        self.assertEqual(namespace["task_team"].mode, TeamMode.tasks)

    def test_custom_tools_and_confirmation(self):
        namespace = self.load("tools.md")
        self.assertEqual(namespace["agent"].tool_call_limit, 3)
        namespace = self.load("tools.md", 1)
        toolkit = namespace["HealthTools"]("https://example.invalid")
        self.assertIn("get_health", toolkit.functions)
        namespace = self.load("tools.md", 2)
        self.assertTrue(namespace["send_demo_message"].requires_confirmation)

    def test_agentos_local_routes(self):
        namespace = self.load("agentos.md")
        # Inspect routes without opening a socket or starting a model run.
        schema = namespace["app"].openapi()
        self.assertIn("/health", schema["paths"])
        run = schema["paths"]["/agents/{agent_id}/runs"]["post"]
        self.assertIn("multipart/form-data", run["requestBody"]["content"])

    def test_mcp_publishes_only_explicit_tools_and_opted_in_lifecycle(self):
        from agno.os import MCPConfig

        self.assertFalse(MCPConfig.model_fields["default_tools"].default)
        self.assertFalse(MCPConfig.model_fields["lifecycle_tools"].default)
        namespace = self.load("mcp.md", 1)
        config = namespace["agent_os"].mcp_config
        self.assertFalse(config.default_tools)
        self.assertTrue(config.lifecycle_tools)
        self.assertEqual(len(config.tools), 1)

    def test_knowledge_current_methods(self):
        from agno.knowledge.knowledge import Knowledge

        for name in (
            "insert",
            "ainsert",
            "sync_pages",
            "async_sync_pages",
            "stream_sync_pages",
            "astream_sync_pages",
            "search_pages",
            "asearch_pages",
            "inspect_page_source",
            "migrate_page_source",
        ):
            with self.subTest(method=name):
                self.assertTrue(callable(getattr(Knowledge, name)))
        self.assertIn("reranker", inspect.signature(Knowledge).parameters)
        self.assertIn("content_db", inspect.signature(Knowledge).parameters)

    def test_cel_workflow_without_model(self):
        namespace = self.load("workflows.md", 2)
        result = namespace["workflow"].run(
            "Routine request", additional_data={"priority": 2}
        )
        self.assertIn("regular review queue", result.content)

    def test_async_workflow_progress(self):
        from agno.run.workflow import StepProgressEvent
        from agno.workflow import Step, StepOutput, Workflow
        from agno.workflow.types import StepProgress

        def sync_step(step_input):
            yield StepProgress(content="Indexing docs", data={"completed": 1})
            yield StepOutput(content="done")

        workflow = Workflow(steps=[Step(name="Sync", executor=sync_step)])

        async def exercise():
            result = await workflow.arun("docs")
            self.assertEqual(result.content, "done")
            events = [
                event
                async for event in workflow.arun(
                    "docs", stream=True, stream_events=True
                )
            ]
            progress = [
                event for event in events if isinstance(event, StepProgressEvent)
            ]
            self.assertEqual(len(progress), 1)
            self.assertEqual(progress[0].data, {"completed": 1})

        asyncio.run(exercise())

    def test_workflow_approval_without_model(self):
        with patch("builtins.input", return_value="y"):
            namespace = self.load("workflows.md", 3)
        self.assertFalse(namespace["result"].is_paused)
        self.assertIn("Quarterly summary", namespace["result"].content)


if __name__ == "__main__":
    unittest.main()
