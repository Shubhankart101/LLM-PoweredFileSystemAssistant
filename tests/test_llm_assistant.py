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
"""

from pathlib import Path
import pytest
import fs_tools
from llm_file_assistant import LLMFileAssistant, SYSTEM_PROMPT


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

    def test_provider_initialization_anthropic_fallback_without_key(self):
        # Without key should gracefully fall back to mock
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
        assert len(result["tool_calls_executed"]) >= 1
        assert result["tool_calls_executed"][0]["tool"] == "list_files"
        assert "resume_john_doe.pdf" in result["response"]
        assert "resume_alice_smith.pdf" in result["response"]

    def test_query_find_python_resumes(self, assistant):
        query = "Find resumes mentioning Python experience"
        result = assistant.run(query)

        assert result["query"] == query
        tool_names = [call["tool"] for call in result["tool_calls_executed"]]
        assert "list_files" in tool_names
        assert "search_in_file" in tool_names

        # Resumes with Python should be present
        assert "resume_john_doe.pdf" in result["response"]
        assert "resume_alice_smith.pdf" in result["response"]
        # Resumes without Python shouldn't be listed as matches
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
