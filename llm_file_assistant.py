"""
llm_file_assistant.py - LLM-Powered File System Assistant

Integrates file system tools with an LLM using function calling / tool calling.
Features:
- Structured OpenAI & Anthropic-compatible tool calling interface.
- Supports live LLMs (OpenAI, Anthropic, Groq, custom OpenAI-compatible endpoints)
  and a deterministic Mock engine for offline evaluation.
- Autonomous multi-step tool execution loop (discovers files, reads resumes,
  searches content, writes summaries).
- Interactive CLI mode, direct query CLI, guided demo integration, and HTTP server mode.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Optional

from dotenv import load_dotenv

import fs_tools

# Load environment variables from .env file if available
load_dotenv(override=False)

SYSTEM_PROMPT = """You are an intelligent File System Assistant specializing in document
processing, file management, and resume screening.
You have access to a suite of file system tools:
- list_files(directory, extension): Discover files in directories with metadata.
- read_file(filepath): Extract text content and metadata from PDF, DOCX, and TXT files.
- write_file(filepath, content): Write summaries or reports (creates directories).
- search_in_file(filepath, keyword): Search for keywords with surrounding line context.

OPERATING GUIDELINES:
1. Always use the provided tools to inspect files and directories. Never fabricate contents.
2. For queries regarding a folder (e.g., 'all resumes in the resumes folder'), first call
   list_files to identify available documents.
3. When searching for candidates with specific skills or keywords (e.g. 'Python'), call
   search_in_file or read_file on resumes, then synthesize findings with evidence.
4. When asked to create a summary file (e.g., 'Create a summary file for
   resume_john_doe.pdf'), read the source file, formulate a summary, and call write_file.
5. Provide concise, polished, professional responses with clear headers.
"""

_STOP_WORDS = {
    "all",
    "any",
    "candidate",
    "candidates",
    "experience",
    "file",
    "files",
    "folder",
    "in",
    "resume",
    "resumes",
    "skill",
    "skills",
    "the",
}


class MockLLMEngine:
    """
    Deterministic offline engine for automated testing and demonstrations without an API key.

    Implements realistic tool calling decisions for standard queries:
    - Listing and reading resumes
    - Searching resumes for keywords (e.g., Python, AWS, Docker)
    - Reading resumes and writing summary files
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    @staticmethod
    def _extract_target_file(query: str) -> str:
        """Extract resume filepath referenced in a query, defaulting to John Doe."""
        for token in query.replace("'", "").replace('"', "").split():
            cleaned = token.strip(".,!?;:")
            if cleaned.endswith((".pdf", ".docx", ".txt")):
                if "/" in cleaned or "\\" in cleaned:
                    return cleaned
                return f"resumes/{cleaned}"
        return "resumes/resume_john_doe.pdf"

    @staticmethod
    def _extract_search_keyword(query: str) -> str:
        """Extract search term from queries like 'Find resumes mentioning Python experience'."""
        match = re.search(
            r"(?:mentioning|containing|with|for|about)\s+([A-Za-z0-9_.+#-]+)",
            query,
            flags=re.IGNORECASE,
        )
        if match:
            candidate = match.group(1).strip(".,!?;:")
            if candidate.lower() not in _STOP_WORDS:
                return candidate
        return "Python"

    @staticmethod
    def _resolve_directory(query_lower: str) -> str:
        """Resolve target directory from query or fallback to 'resumes' if present."""
        if "resumes" in query_lower or Path("resumes").exists():
            return "resumes"
        return "."

    def _handle_summary_intent(
        self,
        query: str,
        tool_executor: Callable[[str, dict[str, Any]], Any],
    ) -> tuple[str, list[dict[str, Any]]]:
        """Execute read_file -> summarize -> write_file multi-step workflow."""
        tool_records: list[dict[str, Any]] = []
        target_file = self._extract_target_file(query)

        read_args = {"filepath": target_file}
        read_res = tool_executor("read_file", read_args)
        tool_records.append(
            {"tool": "read_file", "arguments": read_args, "result": read_res}
        )

        stem = Path(target_file).stem.replace("resume_", "")
        candidate_name = stem.replace("_", " ").title()
        success = read_res.get("success")
        content = read_res.get("content", "") if success else "No content extracted."
        meta = read_res.get("metadata", {})
        page_or_para = meta.get("page_count", meta.get("paragraph_count", "N/A"))

        summary_content = (
            f"CANDIDATE SUMMARY REPORT\n"
            f"{'=' * 50}\n"
            f"Candidate: {candidate_name}\n"
            f"Source File: {target_file}\n"
            f"Format: {Path(target_file).suffix.upper()}\n"
            f"Generated: File System Assistant LLM\n\n"
            f"EXECUTIVE SUMMARY:\n"
            f"Extracted candidate profile with key competencies and experience details.\n\n"
            f"DOCUMENT DETAILS:\n"
            f"- Word count: {meta.get('word_count', 'N/A')}\n"
            f"- Page/Section count: {page_or_para}\n\n"
            f"EXCERPT:\n{content[:400]}...\n"
            f"{'=' * 50}\n"
        )

        dest_file = f"summaries/summary_{stem}.txt"
        write_args = {"filepath": dest_file, "content": summary_content}
        write_res = tool_executor("write_file", write_args)
        tool_records.append(
            {"tool": "write_file", "arguments": write_args, "result": write_res}
        )

        answer = (
            f"I have successfully created a summary file for **{target_file}**.\n\n"
            f"**Actions Taken:**\n"
            f"1. Read content and metadata using `read_file('{target_file}')`.\n"
            f"2. Synthesized key skills, experience, and profile for {candidate_name}.\n"
            f"3. Saved structured summary report to `{dest_file}` via `write_file`.\n\n"
            f"**Summary File Path:** `{dest_file}`\n"
            f"**Status:** {write_res.get('message', 'Completed')}"
        )
        return answer, tool_records

    def _handle_search_intent(
        self,
        query: str,
        tool_executor: Callable[[str, dict[str, Any]], Any],
    ) -> tuple[str, list[dict[str, Any]]]:
        """Execute list_files -> search_in_file across all files in directory."""
        tool_records: list[dict[str, Any]] = []
        directory = self._resolve_directory(query.lower())
        keyword = self._extract_search_keyword(query)

        list_args = {"directory": directory}
        files = tool_executor("list_files", list_args)
        tool_records.append(
            {"tool": "list_files", "arguments": list_args, "result": files}
        )

        matching_candidates: list[dict[str, Any]] = []
        for file_info in files:
            fpath = file_info["filepath"]
            search_args = {"filepath": fpath, "keyword": keyword}
            search_res = tool_executor("search_in_file", search_args)
            tool_records.append(
                {
                    "tool": "search_in_file",
                    "arguments": search_args,
                    "result": search_res,
                }
            )

            if search_res.get("success") and search_res.get("matches_count", 0) > 0:
                matching_candidates.append(
                    {
                        "name": file_info["name"],
                        "matches_count": search_res["matches_count"],
                        "snippets": [m["line_text"] for m in search_res["matches"][:2]],
                    }
                )

        lines = [
            f"I searched all resume files in `{directory}` for **'{keyword}'**.",
            f"Found **{len(matching_candidates)} matching candidate(s)** "
            f"out of {len(files)} files scanned:\n",
        ]
        for cand in matching_candidates:
            lines.append(f"- **{cand['name']}** ({cand['matches_count']} matches):")
            for snip in cand["snippets"]:
                lines.append(f'  > *"{snip}"*')

        return "\n".join(lines), tool_records

    def _handle_read_all_intent(
        self,
        query_lower: str,
        tool_executor: Callable[[str, dict[str, Any]], Any],
    ) -> tuple[str, list[dict[str, Any]]]:
        """Execute list_files -> read_file across every file in the target folder."""
        tool_records: list[dict[str, Any]] = []
        directory = self._resolve_directory(query_lower)

        list_args = {"directory": directory}
        files = tool_executor("list_files", list_args)
        tool_records.append(
            {"tool": "list_files", "arguments": list_args, "result": files}
        )

        read_summaries: list[tuple[str, str, str]] = []
        for file_info in files:
            read_args = {"filepath": file_info["filepath"]}
            read_res = tool_executor("read_file", read_args)
            tool_records.append(
                {"tool": "read_file", "arguments": read_args, "result": read_res}
            )
            if read_res.get("success"):
                preview = read_res.get("content", "")[:120].replace("\n", " ").strip()
                read_summaries.append(
                    (file_info["name"], file_info["extension"], preview)
                )

        lines = [
            f"Found **{len(files)} resume files** in the `{directory}` directory:\n"
        ]
        for f in files:
            lines.append(
                f"- **{f['name']}** ({f['extension'].upper()}, "
                f"{f['size_kb']} KB, modified {f['modified_date']})"
            )

        lines.append("\n**Preview of candidate profiles:**")
        for name, _ext, prev in read_summaries:
            lines.append(f"- **{name}**: {prev}...")

        return "\n".join(lines), tool_records

    def process(
        self,
        query: str,
        tool_executor: Callable[[str, dict[str, Any]], Any],
    ) -> tuple[str, list[dict[str, Any]]]:
        """Route user query to the matching deterministic tool workflow."""
        query_lower = query.lower()
        is_summary = "summary" in query_lower and any(
            verb in query_lower for verb in ("create", "write", "generate", "make")
        )
        if is_summary:
            return self._handle_summary_intent(query, tool_executor)

        is_search = any(
            kw in query_lower for kw in ("mentioning", "search", "find", "matching")
        )
        if is_search:
            return self._handle_search_intent(query, tool_executor)

        return self._handle_read_all_intent(query_lower, tool_executor)


class LLMFileAssistant:
    """
    Core File System Assistant orchestrating LLM tool calling.
    Supports OpenAI, Anthropic, Groq, or Mock offline execution.
    """

    def __init__(
        self,
        provider: str = "auto",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        verbose: bool = True,
    ):
        self.verbose = verbose
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.client: Any = None
        self.mock_engine = MockLLMEngine(verbose=verbose)

        self._initialize_provider()

    def _init_openai(self, fallback_key: str) -> None:
        key = self.api_key or fallback_key
        if not key:
            self._log("Notice: No OPENAI_API_KEY found. Falling back to Mock engine.")
            self.provider = "mock"
            self.model = "mock-deterministic-v1"
            return

        try:
            from openai import OpenAI

            self.api_key = key
            self.client = OpenAI(api_key=key, base_url=self.base_url)
            self.model = self.model or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
        except ImportError:
            self._log(
                "Notice: openai package unavailable. Falling back to Mock engine."
            )
            self.provider = "mock"
            self.model = "mock-deterministic-v1"

    def _init_anthropic(self, fallback_key: str) -> None:
        key = self.api_key or fallback_key
        if not key:
            self._log(
                "Notice: No ANTHROPIC_API_KEY found. Falling back to Mock engine."
            )
            self.provider = "mock"
            self.model = "mock-deterministic-v1"
            return

        try:
            import anthropic

            self.api_key = key
            self.client = anthropic.Anthropic(api_key=key)
            self.model = (
                self.model or os.getenv("ANTHROPIC_MODEL") or "claude-3-5-sonnet-latest"
            )
        except ImportError:
            self._log(
                "Notice: anthropic package unavailable. Falling back to Mock engine."
            )
            self.provider = "mock"
            self.model = "mock-deterministic-v1"

    def _init_groq(self, fallback_key: str) -> None:
        key = self.api_key or fallback_key
        if not key:
            self._log("Notice: No GROQ_API_KEY found. Falling back to Mock engine.")
            self.provider = "mock"
            self.model = "mock-deterministic-v1"
            return

        try:
            from openai import OpenAI

            self.api_key = key
            self.client = OpenAI(
                api_key=key,
                base_url="https://api.groq.com/openai/v1",
            )
            self.model = (
                self.model or os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile"
            )
        except ImportError:
            self._log(
                "Notice: OpenAI client unavailable for Groq. Falling back to Mock engine."
            )
            self.provider = "mock"
            self.model = "mock-deterministic-v1"

    def _initialize_provider(self) -> None:
        """Resolve and initialize provider client."""
        openai_key = self.api_key or os.getenv("OPENAI_API_KEY", "").strip()
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        groq_key = os.getenv("GROQ_API_KEY", "").strip()

        if self.provider == "auto":
            if openai_key:
                self.provider = "openai"
            elif anthropic_key:
                self.provider = "anthropic"
            elif groq_key:
                self.provider = "groq"
            else:
                self.provider = "mock"

        if self.provider == "openai":
            self._init_openai(openai_key)
        elif self.provider == "anthropic":
            self._init_anthropic(anthropic_key)
        elif self.provider == "groq":
            self._init_groq(groq_key)
        else:
            self.provider = "mock"
            self.model = "mock-deterministic-v1"

    def _log(self, text: str, prefix: str = "[Assistant]") -> None:
        """Print formatted logs when verbose is active."""
        if self.verbose:
            print(f"{prefix} {text}")

    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Execute a tool function from fs_tools safely."""
        func = fs_tools.TOOL_MAP.get(tool_name)
        if not func:
            return {"success": False, "error": f"Tool '{tool_name}' is not recognized."}

        self._log(f"Calling tool: {tool_name}({arguments})", prefix="[Tool Call]")
        try:
            result = func(**arguments)
            if isinstance(result, list):
                self._log(f"-> Returned {len(result)} items", prefix="[Tool Result]")
            elif isinstance(result, dict):
                status = (
                    "Success"
                    if result.get("success")
                    else f"Failed: {result.get('error')}"
                )
                matches = result.get("matches_count")
                extra = f", matches: {matches}" if matches is not None else ""
                self._log(f"-> {status}{extra}", prefix="[Tool Result]")
            return result
        except Exception as exc:
            err_msg = f"{type(exc).__name__}: {str(exc)}"
            self._log(f"-> Exception: {err_msg}", prefix="[Tool Error]")
            return {"success": False, "error": err_msg}

    def _run_anthropic(
        self,
        query: str,
        conversation_history: Optional[list[dict[str, Any]]] = None,
        max_iterations: int = 10,
    ) -> dict[str, Any]:
        """Run tool calling loop with Anthropic Messages API."""
        anthropic_tools = [
            {
                "name": t["function"]["name"],
                "description": t["function"]["description"],
                "input_schema": t["function"]["parameters"],
            }
            for t in fs_tools.TOOL_DEFINITIONS
        ]

        messages: list[dict[str, Any]] = [
            msg
            for msg in (conversation_history or [])
            if msg.get("role") in ("user", "assistant")
        ]
        messages.append({"role": "user", "content": query})
        tool_records: list[dict[str, Any]] = []
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            try:
                response = self.client.messages.create(
                    model=self.model,
                    system=SYSTEM_PROMPT,
                    messages=messages,
                    tools=anthropic_tools,
                    max_tokens=2048,
                )
            except Exception as exc:
                self._log(
                    f"Anthropic API Call Error: {exc}. Falling back to mock engine.",
                    prefix="[Error]",
                )
                fb_text, fb_records = self.mock_engine.process(query, self.execute_tool)
                return {
                    "query": query,
                    "response": fb_text,
                    "tool_calls_executed": fb_records,
                    "iterations": iteration,
                    "provider": "anthropic-fallback-mock",
                    "model": self.model or "fallback",
                }

            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            text_blocks = [b.text for b in response.content if b.type == "text"]

            if not tool_use_blocks:
                final_answer = "\n".join(text_blocks).strip()
                if conversation_history is not None:
                    conversation_history.append({"role": "user", "content": query})
                    conversation_history.append(
                        {"role": "assistant", "content": final_answer}
                    )
                return {
                    "query": query,
                    "response": final_answer,
                    "tool_calls_executed": tool_records,
                    "iterations": iteration,
                    "provider": "anthropic",
                    "model": self.model,
                }

            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in tool_use_blocks:
                fn_name = block.name
                fn_args = block.input or {}
                result = self.execute_tool(fn_name, fn_args)
                tool_records.append(
                    {"tool": fn_name, "arguments": fn_args, "result": result}
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, default=str),
                    }
                )

            messages.append({"role": "user", "content": tool_results})

        return {
            "query": query,
            "response": "Maximum tool iterations reached.",
            "tool_calls_executed": tool_records,
            "iterations": iteration,
            "provider": "anthropic",
            "model": self.model,
        }

    def run(
        self,
        query: str,
        conversation_history: Optional[list[dict[str, Any]]] = None,
        max_iterations: int = 10,
    ) -> dict[str, Any]:
        """Process a user query using LLM tool calling."""
        self._log(f"User Query: '{query}'\n", prefix="[Query]")

        if self.provider == "mock" or not self.client:
            self._log(
                f"Running via Deterministic Mock Engine (Model: {self.model})",
                prefix="[Mode]",
            )
            response_text, tool_records = self.mock_engine.process(
                query=query,
                tool_executor=self.execute_tool,
            )
            if conversation_history is not None:
                conversation_history.append({"role": "user", "content": query})
                conversation_history.append(
                    {"role": "assistant", "content": response_text}
                )
            return {
                "query": query,
                "response": response_text,
                "tool_calls_executed": tool_records,
                "iterations": len(tool_records),
                "provider": "mock",
                "model": self.model or "mock-deterministic-v1",
            }

        if self.provider == "anthropic":
            return self._run_anthropic(
                query=query,
                conversation_history=conversation_history,
                max_iterations=max_iterations,
            )

        self._log(
            f"Running via Live LLM Provider: {self.provider.upper()} "
            f"(Model: {self.model})",
            prefix="[Mode]",
        )

        messages: list[dict[str, Any]] = []
        if conversation_history:
            messages.extend(conversation_history)
        else:
            messages.append({"role": "system", "content": SYSTEM_PROMPT})

        messages.append({"role": "user", "content": query})

        tool_calls_executed: list[dict[str, Any]] = []
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=fs_tools.TOOL_DEFINITIONS,
                    tool_choice="auto",
                )
            except Exception as exc:
                self._log(
                    f"LLM API Call Error: {exc}. Falling back to deterministic engine.",
                    prefix="[Error]",
                )
                fb_text, fb_records = self.mock_engine.process(query, self.execute_tool)
                return {
                    "query": query,
                    "response": fb_text,
                    "tool_calls_executed": fb_records,
                    "iterations": iteration,
                    "provider": f"{self.provider}-fallback-mock",
                    "model": self.model or "fallback",
                }

            message = response.choices[0].message

            if message.tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in message.tool_calls
                        ],
                    }
                )

                for tool_call in message.tool_calls:
                    fn_name = tool_call.function.name
                    raw_args = tool_call.function.arguments or "{}"
                    try:
                        fn_args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        fn_args = {}

                    result = self.execute_tool(fn_name, fn_args)
                    tool_calls_executed.append(
                        {"tool": fn_name, "arguments": fn_args, "result": result}
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result, default=str),
                        }
                    )
                continue

            final_content = (message.content or "").strip()
            if conversation_history is not None:
                conversation_history.append({"role": "user", "content": query})
                conversation_history.append(
                    {"role": "assistant", "content": final_content}
                )
            return {
                "query": query,
                "response": final_content,
                "tool_calls_executed": tool_calls_executed,
                "iterations": iteration,
                "provider": self.provider,
                "model": self.model,
            }

        return {
            "query": query,
            "response": "The assistant reached the maximum tool execution limit.",
            "tool_calls_executed": tool_calls_executed,
            "iterations": iteration,
            "provider": self.provider,
            "model": self.model,
        }


def make_http_handler(assistant: LLMFileAssistant) -> type[BaseHTTPRequestHandler]:
    """Create a request handler bound to an LLMFileAssistant instance."""

    class AssistantHTTPHandler(BaseHTTPRequestHandler):
        def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, default=str).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            if assistant.verbose:
                super().log_message(format, *args)

        def do_GET(self) -> None:
            if self.path in ("/", "/health"):
                self._send_json(
                    200,
                    {
                        "status": "healthy",
                        "service": "llm-file-system-assistant",
                        "provider": assistant.provider,
                        "model": assistant.model,
                    },
                )
            else:
                self._send_json(404, {"error": f"Endpoint '{self.path}' not found"})

        def do_POST(self) -> None:
            if self.path != "/query":
                self._send_json(404, {"error": f"Endpoint '{self.path}' not found"})
                return

            length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length)
            try:
                data = json.loads(raw_body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._send_json(400, {"error": "Invalid JSON request body"})
                return

            query = str(data.get("query", "")).strip()
            if not query:
                self._send_json(400, {"error": "Field 'query' must be non-empty"})
                return

            result = assistant.run(query)
            self._send_json(200, result)

    return AssistantHTTPHandler


def serve_http(assistant: LLMFileAssistant, host: str, port: int) -> None:
    """Start an HTTP server exposing /health and /query endpoints."""
    server = ThreadingHTTPServer((host, port), make_http_handler(assistant))
    print(f"Serving LLM File System Assistant HTTP API on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down HTTP server.")
    finally:
        server.server_close()


def run_interactive(assistant: LLMFileAssistant) -> None:
    """Run an interactive conversation loop in the terminal."""
    print("=" * 70)
    print("🤖 LLM-Powered File System Assistant (Interactive Mode)")
    print(f"Provider: {assistant.provider.upper()} | Model: {assistant.model}")
    print("Type your query or 'exit' / 'quit' to stop.")
    print("Example queries:")
    print("  1. Read all resumes in the resumes folder")
    print("  2. Find resumes mentioning Python experience")
    print("  3. Create a summary file for resume_john_doe.pdf")
    print("=" * 70)

    history: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("Goodbye!")
                break

            result = assistant.run(user_input, conversation_history=history)
            print("\n🤖 Assistant:\n")
            print(result["response"])
            print("-" * 70)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting interactive session.")
            break


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM-Powered File System Assistant")
    parser.add_argument("query", nargs="*", help="Optional query to execute directly")
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Launch interactive chat mode"
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Run HTTP API server (/health, /query) for cloud/container deployments",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("ASSISTANT_HOST", "127.0.0.1"),
        help="Bind host for --serve mode",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8000")),
        help="Bind port for --serve mode",
    )
    parser.add_argument(
        "--provider",
        "-p",
        default="auto",
        choices=["auto", "openai", "anthropic", "groq", "mock"],
        help="LLM backend provider",
    )
    parser.add_argument(
        "--model",
        "-m",
        default=None,
        help="Model name (e.g. gpt-4o-mini, llama-3.3-70b-versatile)",
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress tool execution logs"
    )
    args = parser.parse_args()

    assistant = LLMFileAssistant(
        provider=args.provider,
        model=args.model,
        verbose=not args.quiet,
    )

    if args.serve:
        serve_http(assistant, host=args.host, port=args.port)
    elif args.interactive or not args.query:
        run_interactive(assistant)
    else:
        full_query = " ".join(args.query)
        result = assistant.run(full_query)
        print("\n" + "=" * 70)
        print("FINAL ASSISTANT RESPONSE:")
        print("=" * 70)
        print(result["response"])


if __name__ == "__main__":
    main()
