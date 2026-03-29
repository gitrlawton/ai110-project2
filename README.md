# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Features

- **Priority-based scheduling** — the scheduler sorts all pending tasks by priority (1–5) and greedily fills the owner's time budget highest-first, so critical care always fits before lower-priority tasks are considered.
- **Time budget enforcement** — tasks that would exceed the remaining available minutes are skipped and surfaced in a "Skipped tasks" panel in the UI, so the owner always sees what didn't make the cut and why.
- **Chronological sorting** — the daily plan is displayed in ascending start-time order (`HH:MM`), giving the owner a readable, time-ordered view of their day rather than a priority-ranked list.
- **Conflict detection** — after a plan is generated, the scheduler groups tasks by their scheduled time slot and flags any slot containing more than one task, naming each conflicting task so the owner knows exactly what to reschedule.
- **Daily and weekly recurrence** — marking a task complete automatically creates the next occurrence: `daily` tasks advance by one day, `weekly` tasks by seven days. One-off tasks produce no follow-up.
- **Per-pet task filtering** — tasks can be filtered by pet name (case-insensitive) or completion status, supporting owners who manage care for more than one animal.
- **Plan explanation** — a plain-language summary shows how many tasks were scheduled, how many minutes were used out of the available budget, and which tasks were skipped, giving the owner full visibility into the scheduling decisions.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

| Area                    | Tests | Description                                                                                                                                                                                                 |
| ----------------------- | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Schedule generation** | 5     | Verifies tasks are ordered by descending priority, the time budget is enforced, completed tasks are excluded, and edge cases (zero budget, no tasks) produce empty plans without crashing.                  |
| **Recurrence logic**    | 4     | Confirms that completing a `daily` task creates a new task due the next day, a `weekly` task advances by 7 days, a `"once"` task returns `None`, and the owner's task list actually grows after recurrence. |
| **Conflict detection**  | 3     | Checks that two tasks sharing the same `HH:MM` slot produce a warning naming both tasks, distinct slots produce no warnings, and tasks with no scheduled time are silently ignored.                         |
| **Sorting correctness** | 2     | Validates that `sort_by_time` returns tasks in ascending chronological order, and documents a known crash when a task's `time` field is empty.                                                              |

### Confidence level

**3 / 5 stars**

The core scheduling logic (priority ordering, time budget, recurrence date math, conflict grouping) is well-covered and all 16 tests pass. Confidence is held back by two factors:

1. **Known bug in `sort_by_time`** — tasks with `time=""` raise an `IndexError`. The test suite documents this.
2. **No UI-layer tests** — the Streamlit front-end in `app.py` is untested; user-input paths and session-state interactions are not verified.
3. **`date.today()` not mocked** — the fallback branch in `mark_task_complete` (when `due_date=None`) is tested indirectly at best; a clock-dependent test could produce inconsistent results on different days.

Fixing the `sort_by_time` bug and adding at least one integration test for the UI would bring this to at least 4 stars.
