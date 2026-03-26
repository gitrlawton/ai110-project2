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
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
