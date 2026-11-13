# AI-Augmented SDLC — Assignment 1: Spec-Driven Development and Harness Engineering

Vanshika Jain, ID 2026NS93005

Submission for SEZG534 (AI-Augmented Software Development Life Cycle), BITS Pilani.

Two small applications are built with the GitHub Spec Kit workflow (constitution, specify, clarify, plan, tasks, analyze, implement). Each is checked by a harness that is independent of the generated code.

| Folder | Application | Kind |
|---|---|---|
| `Part-1A/` | **Expense and Budget Tracker**, a library and command line with monthly category budgets, kept in one JSON file | Deterministic |
| `Part-1B/` | **Natural-Language Expense Logger**, which turns a sentence such as "paid 450 for lunch yesterday" into a structured expense, with a three-layer evaluation harness | Non-deterministic (in progress) |

## Setup environment

| Item | Version or choice |
|---|---|
| Operating system | macOS 26.6.2 (Darwin 25.6.0), shell zsh |
| GitHub Spec Kit | `specify` 1.2.6.dev0, initialised in each part with the Claude Code integration (commands installed as skills) and the `sh` scripts; the choices are recorded in each part's `.specify/init-options.json` |
| Coding agent | Claude Code, in VS Code |
| Python and packages | Python 3.12 (`requires-python >=3.12,<3.13`), managed with uv 0.12.24 |
| Tools used by the harnesses | Ruff 0.17.5, Bandit 1.9.4, pytest 9.2.0, gitleaks 8.30.1 |
| Git | 2.54.0 |

## Use of AI assistance

This assignment was developed with AI assistance. Claude (through Claude Code) was used as a coding agent to draft the Spec Kit artifacts and to write the implementation, tests and harness code. The decisions behind them were mine: the choice of problems, the constitution principles, and the answers to every clarification question. The harness logs and the reflection answers are written by me from the real evidence. The commands were run on another person's computer, which relayed my decisions to the agent.

## Part 1A: Expense and Budget Tracker

Records expenses in rupees (kept internally as whole paise), lists and filters them, totals each month by category, and warns when a category goes over its monthly budget. Specification: 23 requirements and 49 acceptance criteria. Checked by a six-gate harness. How to install, run and check it is in [`Part-1A/README.md`](Part-1A/README.md).

## Layout

```
Part-1A/
  .specify/ .claude/           Spec Kit templates, scripts and skills, and the project constitution
  specs/001-expense-tracker/   specification, plan, tasks, contracts, analysis, amendments
  src/ tests/                  the code and the tests derived from the acceptance criteria
  .harness/                    the quality gates and the runner
  evidence/                    generated code snapshots, harness results and the harness log
Part-1B/                       in progress
```
