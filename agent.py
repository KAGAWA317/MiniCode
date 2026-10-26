#!/usr/bin/env python3
"""MiniCode: minimal agent loop. Standard library only.

Goal -> policy picks a tool -> tool result feeds the next decision -> answer.
"""
from __future__ import annotations

import argparse
import ast
import operator
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def calc(expr: str, state: dict) -> str:
    """Evaluate arithmetic; `last` refers to the previous result."""

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Name) and node.id == "last" and state.get("last") is not None:
            return state["last"]
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.operand))
        raise ValueError(f"unsupported expression: {ast.dump(node)}")

    value = ev(ast.parse(expr, mode="eval"))
    state["last"] = value
    return str(value)


def _resolve(path: str) -> Path:
    p = (ROOT / path).resolve()
    if p != ROOT and ROOT not in p.parents:
        raise ValueError(f"path escapes workspace: {path}")
    return p


def read(path: str, state: dict) -> str:
    return _resolve(path).read_text(encoding="utf-8")


def write(path: str, text: str, state: dict) -> str:
    p = _resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return f"wrote {len(text)} chars to {path}"


TOOLS = {"calc": calc, "read": read, "write": write}


def demo_policy(goal: str, history: list, state: dict) -> dict:
    """Deterministic stand-in for an LLM. Swap this callable for a real model."""
    clauses = [c.strip() for c in re.split(r"\s+then\s+", goal, flags=re.I) if c.strip()]
    i = state.setdefault("clause", 0)
    if i >= len(clauses):
        last = state.get("last")
        if last is None and history:
            last = history[-1]["observation"]
        return {"answer": str(last if last is not None else "done")}

    clause = clauses[i]
    state["clause"] = i + 1
    if m := re.fullmatch(r"(?:calc(?:ulate)?\s+)?([\d\s+\-*/().%]+|last(?:\s*[+\-*/%]\s*[\d.]+)?)", clause, re.I):
        return {"tool": "calc", "args": {"expr": m.group(1)}}
    if m := re.fullmatch(r"read\s+(.+)", clause, re.I):
        return {"tool": "read", "args": {"path": m.group(1).strip()}}
    if m := re.fullmatch(r"write\s+(\S+)\s*:\s*(.+)", clause, re.I | re.S):
        text = m.group(2).replace("{last}", str(state.get("last", "")))
        return {"tool": "write", "args": {"path": m.group(1), "text": text}}
    return {"answer": f"demo policy can't handle: {clause!r}"}


class Agent:
    def __init__(self, policy=demo_policy, max_steps: int = 8):
        self.policy = policy
        self.max_steps = max_steps

    def run(self, goal: str) -> tuple:
        state = {}
        history = []
        for _ in range(self.max_steps):
            action = self.policy(goal, history, state)
            if "answer" in action:
                return action["answer"], history
            name = action.get("tool")
            try:
                if name not in TOOLS:
                    raise ValueError(f"unknown tool: {name!r}")
                observation = TOOLS[name](state=state, **action.get("args", {}))
            except Exception as exc:  # tool errors are observations, not crashes
                observation = f"ERROR: {exc}"
            history.append({"tool": name, "args": action.get("args", {}), "observation": observation})
        return "ERROR: max steps reached", history


def self_check() -> None:
    agent = Agent()

    answer, history = agent.run("calc 2+2")
    assert answer == "4" and history[0]["tool"] == "calc"

    answer, history = agent.run("calc 6*7 then calc last+1")
    assert answer == "43" and len(history) == 2

    try:
        calc("__import__('os').system('echo pwned')", {})
    except ValueError:
        pass
    else:
        raise AssertionError("calc must reject non-arithmetic input")

    try:
        read("../outside.txt", {})
    except ValueError:
        pass
    else:
        raise AssertionError("read must stay inside the workspace")

    path = ROOT / ".selfcheck.txt"
    try:
        answer, _ = agent.run("write .selfcheck.txt: hello then read .selfcheck.txt")
        assert answer == "hello", answer
    finally:
        path.unlink(missing_ok=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="MiniCode - minimal agent demo")
    parser.add_argument("goal", nargs="*", help="e.g. 'calc 6*7 then write out.txt: {last}'")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)

    if args.self_check:
        self_check()
        print("self-check: OK")
        return 0
    if not args.goal:
        parser.print_help()
        return 2

    answer, history = Agent().run(" ".join(args.goal))
    for i, step in enumerate(history, 1):
        print(f"[{i}] {step['tool']}({step['args']}) -> {step['observation']!r}")
    print(f"answer: {answer}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
