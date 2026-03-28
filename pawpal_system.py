from dataclasses import dataclass, field
from datetime import date, timedelta


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: str = ""

    def summary(self) -> str:
        """Return a readable one-line description of this pet."""
        needs = f", special needs: {self.special_needs}" if self.special_needs else ""
        return f"{self.name} ({self.species}, age {self.age}{needs})"


@dataclass
class Task:
    name: str
    duration_minutes: int
    priority: int          # 1 (low) to 5 (high)
    category: str
    time: str = ""         # scheduled start time in "HH:MM" format, e.g. "08:30"
    pet_name: str = ""     # name of the pet this task is for; empty means all pets
    frequency: str = "once"        # recurrence: "once", "daily", or "weekly"
    due_date: date | None = None   # date this occurrence is due
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True


class Owner:
    def __init__(self, name: str, available_minutes: int, pet: Pet, preferences: list[str] | None = None):
        self.name = name
        self.available_minutes = available_minutes
        self.pet = pet
        self.preferences: list[str] = preferences or []
        self._tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Add a task to this owner's task list."""
        self._tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this owner's task list."""
        self._tasks.remove(task)

    def get_tasks(self) -> list[Task]:
        """Return a copy of all tasks belonging to this owner."""
        return list(self._tasks)


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self._plan: list[Task] = []

    def generate_plan(self) -> list[Task]:
        """Select and order incomplete tasks by priority until the time budget is exhausted."""
        pending = [t for t in self.owner.get_tasks() if not t.completed]
        sorted_tasks = sorted(pending, key=lambda t: t.priority, reverse=True)

        self._plan = []
        minutes_remaining = self.owner.available_minutes
        self._skipped: list[Task] = []

        for task in sorted_tasks:
            if task.duration_minutes <= minutes_remaining:
                self._plan.append(task)
                minutes_remaining -= task.duration_minutes
            else:
                self._skipped.append(task)

        return self._plan

    def mark_task_complete(self, task: Task) -> Task | None:
        """Mark a task complete and, if it recurs, register the next occurrence.

        The next occurrence is a fresh Task (completed=False) whose due_date is
        advanced by timedelta(days=1) for "daily" tasks or timedelta(weeks=1)
        for "weekly" tasks.  The new task is added to the owner's task list and
        returned so callers can inspect it.  Returns None for one-off tasks.
        """
        task.mark_complete()

        _DELTAS = {
            "daily":  timedelta(days=1),
            "weekly": timedelta(weeks=1),
        }
        delta = _DELTAS.get(task.frequency)
        if delta is None:
            return None

        base_date = task.due_date if task.due_date is not None else date.today()
        next_task = Task(
            name=task.name,
            duration_minutes=task.duration_minutes,
            priority=task.priority,
            category=task.category,
            time=task.time,
            pet_name=task.pet_name,
            frequency=task.frequency,
            due_date=base_date + delta,
        )
        self.owner.add_task(next_task)
        return next_task

    def detect_conflicts(self) -> list[str]:
        """Return a list of warning messages for any tasks sharing the same start time.

        Strategy: group planned tasks by their 'time' field using a dict, then
        report every slot that holds more than one task.  Tasks with no time set
        ("") are skipped — they have no scheduled slot to clash on.  The method
        never raises; an empty list means no conflicts were found.
        """
        time_slots: dict[str, list[Task]] = {}
        for task in self._plan:
            if not task.time:
                continue
            time_slots.setdefault(task.time, []).append(task)

        warnings: list[str] = []
        for slot, tasks in time_slots.items():
            if len(tasks) > 1:
                names = ", ".join(
                    f'"{t.name}"' + (f" ({t.pet_name})" if t.pet_name else "")
                    for t in tasks
                )
                warnings.append(
                    f"WARNING: Time conflict at {slot} -- {len(tasks)} tasks overlap: {names}"
                )
        return warnings

    def filter_tasks(
        self,
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[Task]:
        """Return tasks from the current plan filtered by completion status and/or pet name.

        Args:
            completed: If True, return only completed tasks; if False, only incomplete;
                       if None, skip this filter.
            pet_name:  If provided, return only tasks whose pet_name matches
                       (case-insensitive). If None, skip this filter.
        """
        tasks = self._plan
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet_name.lower() == pet_name.lower()]
        return tasks

    def sort_by_time(self) -> list[Task]:
        """Return tasks sorted by their scheduled start time (HH:MM) ascending."""
        return sorted(
            self._plan,
            key=lambda t: (int(t.time.split(":")[0]), int(t.time.split(":")[1]))
        )

    def explain(self) -> str:
        """Return a plain-language summary of the scheduled and skipped tasks."""
        if not self._plan and not hasattr(self, "_skipped"):
            return "No plan generated yet. Call generate_plan() first."

        planned_minutes = sum(t.duration_minutes for t in self._plan)
        lines = [
            f"Plan for {self.owner.name}  |  budget: {self.owner.available_minutes} min",
            f"Pet: {self.owner.pet.summary()}",
            "",
            f"Scheduled {len(self._plan)} task(s)  —  {planned_minutes} of {self.owner.available_minutes} min used:",
        ]
        for task in self._plan:
            lines.append(f"  [+] [{task.priority}] {task.name} ({task.duration_minutes} min, {task.category})")

        if self._skipped:
            lines.append(f"\nSkipped {len(self._skipped)} task(s) -- insufficient time remaining:")
            for task in self._skipped:
                lines.append(f"  [-] [{task.priority}] {task.name} ({task.duration_minutes} min)")

        lines.append("\nTasks are ordered highest-to-lowest priority so critical care always fits first.")
        return "\n".join(lines)
