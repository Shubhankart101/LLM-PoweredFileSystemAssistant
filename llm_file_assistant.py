"""
llm_file_assistant.py - LLM-Powered File System Assistant

Integrates file system tools with an LLM using function calling / tool calling.
Features:
- Structured OpenAI & Anthropic-compatible tool calling interface.
- Supports live LLMs (OpenAI, Anthropic, Groq, custom OpenAI-compatible endpoints)
  and a deterministic Mock engine for offline evaluation.
- Autonomous multi-step tool execution loop (discovers files, reads resumes, searches content, writes summaries).
- Interactive CLI mode, guided demo, and programmatic API.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from dotenv import load_dotenv

import fs_tools

# Load environment variables from .env file if available
load_dotenv(override=False)

SYSTEM_PROMPT = """You are an intelligent File System Assistant specializing in document processing, file management, and resume screening.
You have access to a suite of file system tools:
- list_files(directory, extension): Discover files in directories with metadata (name, size, modified date).
- read_file(filepath): Extract text content and metadata from PDF, DOCX, and TXT files.
- write_file(filepath, content): Write generated summaries or reports to disk (automatically creates parent directories).
- search_in_file(filepath, keyword): Search for specific keywords with surrounding line context.

OPERATING GUIDELINES:
1. Always use the appropriate tools to inspect files and directories. Never assume or make up file contents.
2. For queries regarding a folder (e.g., 'all resumes in the resumes folder'), first call list_files to identify available documents.
3. When searching for candidates with specific skills or keywords (e.g. 'Python'), call search_in_file or read_file on candidate resumes, then synthesize your findings with clear candidate names and evidence.
4. When asked to create a summary file (e.g., 'Create a summary file for resume_john_doe.pdf'), read the source file, formulate an executive summary, and call write_file to save the summary to disk.
5. Provide concise, polished, professional responses with clear headers.
"""


class MockLLMEngine:
    """
    Deterministic offline engine for automated testing and demonstrations without an API key.

    Implements realistic tool calling decisions for standard queries:
    - Listing resumes
    - Searching resumes for keywords (e.g. Python, AWS)
    - Reading resumes and writing summary files
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def process(
        self,
        query: str,
        tool_executor: Callable[[str, dict[str, Any]], Any],
    ) -> tuple[str, list[dict[str, Any]]]:
        """Simulate LLM tool-calling logic based on user intent."""
        query_lower = query.lower()
        tool_records: list[dict[str, Any]] = []

        # Intent 1: Create a summary file
        if "summary" in query_lower and ("create" in query_lower or "write" in query_lower or "generate" in query_lower):
            target_file = "resumes/resume_john_doe.pdf"
            for word in query.replace("'", "").replace('"', "").split():
                if word.endswith((".pdf", ".docx", ".txt")):
                    target_file = word if "/" in word or "\\" in word else f"resumes/{word}"
                    break

            # Step 1: Read the target file
            read_args = {"filepath": target_file}
            read_res = tool_executor("read_file", read_args)
            tool_records.append({"tool": "read_file", "arguments": read_args, "result": read_res})

            candidate_name = Path(target_file).stem.replace("resume_", "").replace("_", " ").title()
            content = read_res.get("content", "") if read_res.get("success") else "No content extracted."

            # Formulate structured summary
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
                f"- Word count: {read_res.get('metadata', {}).get('word_count', 'N/A')}\n"
                f"- Page/Section count: {read_res.get('metadata', {}).get('page_count', read_res.get('metadata', {}).get('paragraph_count', 'N/A'))}\n\n"
                f"EXCERPT:\n{content[:400]}...\n"
                f"{'=' * 50}\n"
            )

            # Step 2: Write summary file
            dest_file = f"summaries/summary_{Path(target_file).stem.replace('resume_', '')}.txt"
            write_args = {"filepath": dest_file, "content": summary_content}
            write_res = tool_executor("write_file", write_args)
            tool_records.append({"tool": "write_file", "arguments": write_args, "result": write_res})

            answer = (
                f"I have successfully created a summary file for **{target_file}**.\n\n"
                f"**Actions Taken:**\n"
                f"1. Read content and metadata using `read_file('{target_file}')`.\n"
                f"2. Synthesized key skills, experience, and candidate profile for {candidate_name}.\n"
                f"3. Saved structured summary report to `{dest_file}` using `write_file`.\n\n"
                f"**Summary File Path:** `{dest_file}`\n"
                f"**Status:** {write_res.get('message', 'Completed')}"
            )
            return answer, tool_records

        # Intent 2: Search for keyword (e.g. Python, React, DevOps)
        elif "mentioning" in query_lower or "search" in query_lower or "find" in query_lower:
            directory = "resumes" if "resumes" in query_lower or Path("resumes").exists() else "."
            keyword = "Python"
            if "python" in query_lower:
                keyword = "Python"
            elif "react" in query_lower:
                keyword = "React"
            elif "aws" in query_lower:
                keyword = "AWS"

            # Step 1: list files
            list_args = {"directory": directory}
            files = tool_executor("list_files", list_args)
            tool_records.append({"tool": "list_files", "arguments": list_args, "result": files})

            matching_candidates: list[dict[str, Any]] = []

            # Step 2: search in each file
            for file_info in files:
                fpath = file_info["filepath"]
                search_args = {"filepath": fpath, "keyword": keyword}
                search_res = tool_executor("search_in_file", search_args)
                tool_records.append({"tool": "search_in_file", "arguments": search_args, "result": search_res})

                if search_res.get("success") and search_res.get("matches_count", 0) > 0:
                    matching_candidates.append({
                        "name": file_info["name"],
                        "matches_count": search_res["matches_count"],
                        "snippets": [m["line_text"] for m in search_res["matches"][:2]],
                    })

            lines = [
                f"I searched all resume files in the `{directory}` folder for experience with **'{keyword}'**.",
                f"Found **{len(matching_candidates)} matching candidate(s)** out of {len(files)} files scanned:\n",
            ]
            for cand in matching_candidates:
                lines.append(f"- **{cand['name']}** ({cand['matches_count']} matches):")
                for snip in cand["snippets"]:
                    lines.append(f"  > *\"{snip}\"*")

            return "\n".join(lines), tool_records

        # Intent 3: Read all resumes / list files
        else:
            directory = "resumes" if "resumes" in query_lower or Path("resumes").exists() else "."
            list_args = {"directory": directory}
            files = tool_executor("list_files", list_args)
            tool_records.append({"tool": "list_files", "arguments": list_args, "result": files})

            read_summaries = []
            for file_info in files[:4]:
                read_args = {"filepath": file_info["filepath"]}
                read_res = tool_executor("read_file", read_args)
                tool_records.append({"tool": "read_file", "arguments": read_args, "result": read_res})
                if read_res.get("success"):
                    preview = read_res.get("content", "")[:120].replace("\n", " ").strip()
                    read_summaries.append((file_info["name"], file_info["extension"], preview))

            lines = [
                f"Found **{len(files)} resume files** in the `{directory}` directory:\n",
            ]
            for f in files:
                lines.append(f"- **{f['name']}** ({f['extension'].upper()}, {f['size_kb']} KB, modified {f['modified_date']})")

            lines.append("\n**Preview of candidate profiles:**")
            for name, ext, prev in read_summaries:
                lines.append(f"- **{name}**: {prev}...")

            return "\n".join(lines), tool_records


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

    def _initialize_provider(self) -> None:
        """Resolve and initialize provider client."""
        openai_key = self.api_key or os.getenv("OPENAI_API_KEY", "").strip()
        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

        if self.provider == "auto":
            if openai_key:
                self.provider = "openai"
                self.api_key = openai_key
            elif anthropic_key:
                self.provider = "anthropic"
                self.api_key = anthropic_key
            elif groq_key:
                self.provider = "groq"
                self.api_key = groq_key
            else:
                self.provider = "mock"

        if self.provider == "openai":
            if not self.api_key:
                self.api_key = openai_key
            if not self.api_key:
                self._log("Notice: No OPENAI_API_KEY found. Falling back to Mock engine.")
                self.provider = "mock"
                return

            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
                self.model = self.model or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
            except ImportError:
                self._log("Notice: openai package not available. Falling back to Mock engine.")
                self.provider = "mock"

        elif self.provider == "anthropic":
            key = self.api_key or anthropic_key
            if not key:
                self._log("Notice: No ANTHROPIC_API_KEY found. Falling back to Mock engine.")
                self.provider = "mock"
                return

            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=key)
                self.model = self.model or os.getenv("ANTHROPIC_MODEL") or "claude-3-5-sonnet-latest"
            except ImportError:
                self._log("Notice: anthropic package not available. Falling back to Mock engine.")
                self.provider = "mock"

        elif self.provider == "groq":
            key = self.api_key or groq_key
            if not key:
                self._log("Notice: No GROQ_API_KEY found. Falling back to Mock engine.")
                self.provider = "mock"
                return

            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=key,
                    base_url="https://api.groq.com/openai/v1",
                )
                self.model = self.model or "llama-3.3-70b-versatile"
            except ImportError:
                self._log("Notice: OpenAI client not available for Groq. Falling back to Mock engine.")
                self.provider = "mock"

        elif self.provider == "mock":
            self.model = "mock-deterministic-v1"

    def _log(self, text: str, prefix: str = "[Assistant]") -> None:
        """Helper to print formatted logs when verbose is active."""
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
                status = "Success" if result.get("success") else f"Failed: {result.get('error')}"
                matches = result.get("matches_count")
                extra = f", matches: {matches}" if matches is not None else ""
                self._log(f"-> {status}{extra}", prefix="[Tool Result]")
            return result
        except Exception as exc:
            err_msg = f"{type(exc).__name__}: {str(exc)}"
            self._log(f"-> Exception: {err_msg}", prefix="[Tool Error]")
            return {"success": False, "error": err_msg}

    def _run_anthropic(
        self, query: str, max_iterations: int = 10
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

        messages: list[dict[str, Any]] = [{"role": "user", "content": query}]
        tool_records: list[dict[str, Any]] = []
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            response = self.client.messages.create(
                model=self.model,
                system=SYSTEM_PROMPT,
                messages=messages,
                tools=anthropic_tools,
                max_tokens=2048,
            )

            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            text_blocks = [b.text for b in response.content if b.type == "text"]

            if not tool_use_blocks:
                final_answer = "\n".join(text_blocks)
                return {
                    "query": query,
                    "response": final_answer.strip(),
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
                tool_records.append({
                    "tool": fn_name,
                    "arguments": fn_args,
                    "result": result,
                })
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str),
                })

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
            self._log(f"Running via Deterministic Mock Engine (Model: {self.model})", prefix="[Mode]")
            response_text, tool_records = self.mock_engine.process(
                query=query,
                tool_executor=self.execute_tool,
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
            return self._run_anthropic(query=query, max_iterations=max_iterations)

        self._log(f"Running via Live LLM Provider: {self.provider.upper()} (Model: {self.model})", prefix="[Mode]")

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
                self._log(f"LLM API Call Error: {exc}. Falling back to deterministic engine.", prefix="[Error]")
                fb_text, fb_records = self.mock_engine.process(query, self.execute_tool)
                return {
                    "query": query,
                    "response": fb_text,
                    "tool_calls_executed": fb_records,
                    "iterations": iteration,
                    "provider": f"{self.provider}-fallback-mock",
                    "model": self.model or "fallback",
                }

            choice = response.choices[0]
            message = choice.message

            if message.tool_calls:
                messages.append(message)

                for tool_call in message.tool_calls:
                    fn_name = tool_call.function.name
                    raw_args = tool_call.function.arguments or "{}"
                    try:
                        fn_args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        fn_args = {}

                    result = self.execute_tool(fn_name, fn_args)
                    tool_calls_executed.append({
                        "tool": fn_name,
                        "arguments": fn_args,
                        "result": result,
                    })

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, default=str),
                    })
                continue
            else:
                final_content = message.content or ""
                return {
                    "query": query,
                    "response": final_content.strip(),
                    "tool_calls_executed": tool_calls_executed,
                    "iterations": iteration,
                    "provider": self.provider,
                    "model": self.model,
                }

        return {
            "query": query,
            "response": "The assistant reached the maximum tool execution limit before completing.",
            "tool_calls_executed": tool_calls_executed,
            "iterations": iteration,
            "provider": self.provider,
            "model": self.model,
        }


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


def main():
    parser = argparse.ArgumentParser(description="LLM-Powered File System Assistant")
    parser.add_argument("query", nargs="*", help="Optional query to execute directly")
    parser.add_argument("--interactive", "-i", action="store_true", help="Launch interactive chat mode")
    parser.add_argument("--provider", "-p", default="auto", choices=["auto", "openai", "anthropic", "groq", "mock"], help="LLM backend provider")
    parser.add_argument("--model", "-m", default=None, help="Specific model name (e.g. gpt-4o-mini, llama-3.3-70b-versatile, claude-3-5-sonnet-latest)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress tool execution logs")
    args = parser.parse_args()

    assistant = LLMFileAssistant(
        provider=args.provider,
        model=args.model,
        verbose=not args.quiet,
    )

    if args.interactive or not args.query:
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
