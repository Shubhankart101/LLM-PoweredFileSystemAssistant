"""
test_llm_assistant.py - Tests for LLM File Assistant and Tool Calling Integration.

Tests:
- Tool definitions schema conformity
- Tool execution dispatching
- Multi-provider initializations (Mock, OpenAI, Anthropic, Groq)
- End-to-end execution of the 3 required assignment queries:
  1. "Read all resumes in the resumes folder"
  2. "Find resumes mentioning Python experience"
  3. "Create a summary file for resume_john_doe.pdf"
- Dynamic keyword matching and HTTP API endpoints (/health, /query)
"""

import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

import fs_tools
from llm_file_assistant import LLMFileAssistant, make_http_handler


class TestLLMAssistantSchemas:
    def test_tool_definitions_schema(self):
        """Validate OpenAI function calling schema format for all tools."""
        assert len(fs_tools.TOOL_DEFINITIONS) == 4
        expected_names = {"read_file", "list_files", "write_file", "search_in_file"}
        actual_names = {t["function"]["name"] for t in fs_tools.TOOL_DEFINITIONS}
        assert actual_names == expected_names

        for tool in fs_tools.TOOL_DEFINITIONS:
            assert tool["type"] == "function"
            fn = tool["function"]
            assert "name" in fn
            assert "description" in fn
            assert "parameters" in fn
            assert fn["parameters"]["type"] == "object"
            assert "properties" in fn["parameters"]
            assert "required" in fn["parameters"]

    def test_tool_map_matches_definitions(self):
        for tool in fs_tools.TOOL_DEFINITIONS:
            name = tool["function"]["name"]
            assert name in fs_tools.TOOL_MAP
            assert callable(fs_tools.TOOL_MAP[name])


class TestLLMAssistantExecution:
    @pytest.fixture
    def assistant(self):
        return LLMFileAssistant(provider="mock", verbose=False)

    def test_provider_initialization_mock(self):
        mock_asst = LLMFileAssistant(provider="mock", verbose=False)
        assert mock_asst.provider == "mock"

    def test_provider_initialization_anthropic_fallback_without_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        asst = LLMFileAssistant(provider="anthropic", api_key="", verbose=False)
        assert asst.provider == "mock"

    def test_tool_dispatch(self, assistant):
        result = assistant.execute_tool("list_files", {"directory": "resumes"})
        assert isinstance(result, list)
        assert len(result) >= 8

    def test_invalid_tool_dispatch(self, assistant):
        result = assistant.execute_tool("unknown_tool_xyz", {})
        assert result["success"] is False
        assert "not recognized" in result["error"]

    def test_query_read_all_resumes(self, assistant):
        query = "Read all resumes in the resumes folder"
        result = assistant.run(query)

        assert result["query"] == query
        assert result["tool_calls_executed"][0]["tool"] == "list_files"
        read_calls = [
            call
            for call in result["tool_calls_executed"]
            if call["tool"] == "read_file"
        ]
        # Verify all 8 resumes are read, not just a subset
        assert len(read_calls) >= 8
        assert "resume_john_doe.pdf" in result["response"]
        assert "resume_sarah_connor.txt" in result["response"]

    def test_query_find_python_resumes(self, assistant):
        query = "Find resumes mentioning Python experience"
        result = assistant.run(query)

        assert result["query"] == query
        tool_names = [call["tool"] for call in result["tool_calls_executed"]]
        assert "list_files" in tool_names
        assert "search_in_file" in tool_names

        assert "resume_john_doe.pdf" in result["response"]
        assert "resume_alice_smith.pdf" in result["response"]
        assert "resume_sarah_connor.txt" not in result["response"]

    def test_query_dynamic_keyword_search(self, assistant):
        query = "Find resumes mentioning Kubernetes experience"
        result = assistant.run(query)

        assert "Kubernetes" in result["response"]
        assert "resume_david_wilson.txt" in result["response"]
        assert "resume_sarah_connor.txt" not in result["response"]

    def test_query_create_summary_file(self, assistant):
        query = "Create a summary file for resume_john_doe.pdf"
        result = assistant.run(query)

        assert result["query"] == query
        tool_names = [call["tool"] for call in result["tool_calls_executed"]]
        assert "read_file" in tool_names
        assert "write_file" in tool_names

        summary_file = Path("summaries/summary_john_doe.txt")
        assert summary_file.exists()
        content = summary_file.read_text(encoding="utf-8")
        assert "John Doe" in content
        assert "Senior Python Backend Engineer" in content

    def test_conversation_history_updates(self, assistant):
        history = [{"role": "system", "content": "test"}]
        assistant.run(
            "Read all resumes in the resumes folder", conversation_history=history
        )
        assert len(history) == 3
        assert history[1]["role"] == "user"
        assert history[2]["role"] == "assistant"


class TestHTTPServerMode:
    def test_health_and_query_endpoints(self):
        assistant = LLMFileAssistant(provider="mock", verbose=False)
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_http_handler(assistant))
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/health", timeout=5
            ) as resp:
                assert resp.status == 200
                health_data = json.loads(resp.read().decode("utf-8"))
                assert health_data["status"] == "healthy"
                assert health_data["provider"] == "mock"

            req_body = json.dumps(
                {"query": "Find resumes mentioning Python experience"}
            ).encode("utf-8")
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/query",
                data=req_body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                assert resp.status == 200
                query_data = json.loads(resp.read().decode("utf-8"))
                assert "resume_john_doe.pdf" in query_data["response"]

            bad_req = urllib.request.Request(
                f"http://127.0.0.1:{port}/query",
                data=json.dumps({"query": "   "}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                urllib.request.urlopen(bad_req, timeout=5)
            assert exc_info.value.code == 400
        finally:
            server.shutdown()
            server.server_close()
