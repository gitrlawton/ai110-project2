# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
  - The design is organized around three core user actions: (1) entering owner and pet information, (2) adding and editing pet care tasks, and (3) generating a daily care schedule. Each action maps to a distinct layer of the system — a data entry interface, a task management model, and a scheduling engine — so that responsibilities stay separated and each piece can be built and tested independently.
- What classes did you include, and what responsibilities did you assign to each?
  - **Owner / Pet** — holds the profile data a user enters in core action 1 (owner name, pet name/type, daily time available, and any care preferences). This context is passed to the scheduler so it can make personalized decisions.
  - **Task** — represents a single care activity created in core action 2 (e.g., walk, feeding, medication, grooming). Each task stores at minimum a name, estimated duration, and priority level, and supports editing so the user can refine the list over time.
  - **Scheduler** — implements core action 3 by accepting the task list and owner/pet context, applying constraints (available time, priority), and producing a ranked daily plan along with a plain-language explanation of why each task was placed where it was.

**b. Design changes**

- Did your design change during implementation?
  - Yes — reviewing the initial skeleton against the README revealed three gaps that required changes before any logic was written.
- If yes, describe at least one change and why you made it.
  - **Removed `is_schedulable()` from `Task`:** The initial UML placed this method on `Task`, but a task shouldn't need to know the remaining time budget — that's runtime state owned by the scheduler. Moving this check inside `Scheduler.generate_plan()` keeps `Task` a pure data object and avoids leaking scheduling logic into the wrong class.
  - **Added `completed: bool` to `Task`:** The README requires users to add and edit tasks, but the original `Task` had no way to track whether a task had been completed. Without this field, the scheduler can't distinguish pending from done tasks.
  - **Added `preferences: list[str]` to `Owner` and `_plan` to `Scheduler`:** The README explicitly lists "owner preferences" as a scheduler constraint, but the original design had no field to store them. Additionally, `Scheduler.explain()` had no data to work from since `generate_plan()` stored nothing — adding `self._plan` lets `explain()` reference the last generated schedule.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
  - Time budget, task priority, completion status, scheduled start time, and recurrence frequency.
- How did you decide which constraints mattered most?
  - Time is non-negotiable (you can't do more than the budget allows), priority ranks second because missing medication or feeding has real health consequences, and completion status and recurrence were added once it was clear a one-shot plan couldn't model daily pet ownership.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
  - `detect_conflicts()` flags tasks that share the exact same `HH:MM` slot but does not check whether a task's duration overlaps the next task's start time.
- Why is that tradeoff reasonable for this scenario?
  - Tasks only store a single time string, not a start and end timestamp, so duration-based overlap would require extra parsing complexity; pet care tasks are also typically scheduled in rough time blocks rather than back-to-back at minute precision, making exact-match detection sufficient for the real mistake an owner would make.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
  - Creating and updating the Mermaid diagram, generating class and method stubs, and drafting tests.
- What kinds of prompts or questions were most helpful?
  - Detailed, well-formed prompts that gave the AI clear context about what was needed and why.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
  - The AI proposed class changes after the UML was already finalized, and I rejected them to stay consistent with the agreed design.
- How did you evaluate or verify what the AI suggested?
  - Using "Ask before edits" mode to review each proposed change before it was applied, confirming it was actually necessary.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
  - Priority ordering, time budget enforcement, completed-task exclusion, daily and weekly recurrence, conflict detection, and chronological sorting.
- Why were these tests important?
  - These cover the scheduler's core contract — a wrong priority order, missed budget check, or bad recurrence date could cause a pet owner to miss medication or feeding with no visible error.

**b. Confidence**

- How confident are you that your scheduler works correctly?
  - 3 out of 5 — all 16 tests pass, but a known `IndexError` in `sort_by_time()` on empty time strings, no UI-layer tests, and an untested clock-dependent fallback in `mark_task_complete()` limit full confidence.
- What edge cases would you test next if you had more time?
  - Mixed timed and untimed tasks in `sort_by_time()`, `mark_task_complete()` with `due_date=None` using a mocked clock, and both `filter_tasks()` filters applied simultaneously.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
  - Satisfied with the project overall, though the UI could be more polished and practically useful as a real pet scheduling tool.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
  - Use Kotlin and Jetpack Compose instead, to build a native Android app rather than a web-based Streamlit prototype.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
  - Different class designs can all be reasonably justified — there isn't one right answer, and the arguments for a design matter as much as the design itself.
