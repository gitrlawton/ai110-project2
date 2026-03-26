from dataclasses import dataclass, field


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
            lines.append(f"  ✓ [{task.priority}] {task.name} ({task.duration_minutes} min, {task.category})")

        if self._skipped:
            lines.append(f"\nSkipped {len(self._skipped)} task(s) — insufficient time remaining:")
            for task in self._skipped:
                lines.append(f"  ✗ [{task.priority}] {task.name} ({task.duration_minutes} min)")

        lines.append("\nTasks are ordered highest-to-lowest priority so critical care always fits first.")
        return "\n".join(lines)
