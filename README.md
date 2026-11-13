# AI-Augmented SDLC — Assignment 1: Spec-Driven Development and Harness Engineering

Vanshika Jain, ID 2026NS93005

Submission for SEZG534 (AI-Augmented Software Development Life Cycle), BITS Pilani.

Two small applications are built with the GitHub Spec Kit workflow (constitution, specify, clarify, plan, tasks, analyze, implement). Each is checked by a harness that is independent of the generated code.

| Folder | Application | Kind |
|---|---|---|
| `Part-1A/` | **Expense and Budget Tracker**, a library and command line with monthly category budgets, kept in one JSON file | Deterministic |
| `Part-1B/` | **Natural-Language Expense Logger**, which turns a sentence such as "paid 450 for lunch yesterday" into a structured expense using Google Gemini, with a three-layer evaluation harness | Non-deterministic |

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

This assignment was developed with some help from AI. I used Claude (through Claude Code) as a coding agent to draft the Spec Kit artifacts and to write implementation and harness code, under my direction and review. The harness logs and the reflection answers are written by me from the real evidence, as the assignment requires.

## Part 1A: Expense and Budget Tracker

Records expenses in rupees (kept internally as whole paise), lists and filters them, totals each month by category, and warns when a category goes over its monthly budget. Specification: 23 requirements and 49 acceptance criteria. Checked by a six-gate harness. How to install, run and check it is in [`Part-1A/README.md`](Part-1A/README.md).

## Part 1B: Natural-Language Expense Logger

A command-line assistant that turns one sentence about spending into a structured expense, asks when the amount or the date is missing or unclear, and refuses requests that are not expenses or that try to reveal its instructions. The model's answers vary, so it is judged by a three-layer evaluation harness (structure, properties, comparison with the expected answer) on a dataset of 35 made-up requests, each run three times, against a pass rule fixed in advance. How to install, run and evaluate it is in [`Part-1B/README.md`](Part-1B/README.md).

## Layout

```
Part-1A/
  .specify/ .claude/           Spec Kit templates, scripts and skills, and the project constitution
  specs/001-expense-tracker/   specification, plan, tasks, contracts, analysis, amendments
  src/ tests/                  the code and the tests derived from the acceptance criteria
  .harness/                    the quality gates and the runner
  evidence/                    generated code snapshots, harness results and the harness log
Part-1B/
  .specify/ .claude/           Spec Kit templates, scripts and skills, and the Part 1B constitution
  specs/001-expense-logger/    specification, plan, tasks, contract, analysis
  src/ prompts/ tests/         the application, its system prompt and the tests
  evals/                       the evaluation dataset
  .harness/                    the evaluation runner, the three layers and the scoring
  evidence/                    generated code snapshots, evaluation runs and the held-out check
```
