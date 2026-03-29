import json
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

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "special_needs": self.special_needs,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Pet":
        return cls(
            name=d["name"],
            species=d["species"],
            age=d["age"],
            special_needs=d.get("special_needs", ""),
        )


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

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "category": self.category,
            "time": self.time,
            "pet_name": self.pet_name,
            "frequency": self.frequency,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        raw_date = d.get("due_date")
        return cls(
            name=d["name"],
            duration_minutes=d["duration_minutes"],
            priority=d["priority"],
            category=d["category"],
            time=d.get("time", ""),
            pet_name=d.get("pet_name", ""),
            frequency=d.get("frequency", "once"),
            due_date=date.fromisoformat(raw_date) if raw_date else None,
            completed=d.get("completed", False),
        )


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

    def save_to_json(self, path: str = "data.json") -> None:
        """Persist owner, pet, and all tasks to a JSON file."""
        data = {
            "name": self.name,
            "available_minutes": self.available_minutes,
            "preferences": self.preferences,
            "pet": self.pet.to_dict(),
            "tasks": [t.to_dict() for t in self.get_tasks()],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_json(cls, path: str = "data.json") -> "Owner":
        """Reconstruct an Owner (with pet and tasks) from a JSON file.

        Raises FileNotFoundError if the file does not exist.
        """
        with open(path) as f:
            data = json.load(f)
        pet = Pet.from_dict(data["pet"])
        owner = cls(
            name=data["name"],
            available_minutes=data["available_minutes"],
            pet=pet,
            preferences=data.get("preferences", []),
        )
        for task_dict in data.get("tasks", []):
            owner.add_task(Task.from_dict(task_dict))
        return owner


class Scheduler:
    def __init__(self, owner: Owner, priority_weight: float = 1.0, urgency_weight: float = 1.0):
        self.owner = owner
        self.priority_weight = priority_weight
        self.urgency_weight = urgency_weight
        self._plan: list[Task] = []

    _CATEGORY_BOOST: dict[str, float] = {
        "medication": 2.0,
        "feeding": 1.0,
        "exercise": 0.0,
        "enrichment": 0.0,
        "grooming": 0.0,
        "other": 0.0,
    }

    def score_task(self, task: Task, today: date | None = None) -> float:
        """Compute a composite scheduling score for a task.

        score = (priority * priority_weight) + (urgency * urgency_weight) + category_boost

        urgency is derived from days until due_date:
            overdue       -> 6.0
            due today     -> 5.0
            1 day out     -> 4.0
            2 days out    -> 3.0
            3 days out    -> 2.0
            4-6 days out  -> 1.0
            7+ days / None -> 0.0

        category_boost: medication=+2.0, feeding=+1.0, all others=+0.0
        """
        if today is None:
            today = date.today()

        if task.due_date is None:
            urgency = 0.0
        else:
            days = (task.due_date - today).days
            if days < 0:
                urgency = 6.0
            elif days == 0:
                urgency = 5.0
            elif days == 1:
                urgency = 4.0
            elif days == 2:
                urgency = 3.0
            elif days == 3:
                urgency = 2.0
            elif days <= 6:
                urgency = 1.0
            else:
                urgency = 0.0

        category_boost = self._CATEGORY_BOOST.get(task.category, 0.0)
        return (task.priority * self.priority_weight) + (urgency * self.urgency_weight) + category_boost

    def generate_plan(self) -> list[Task]:
        """Select and order incomplete tasks by priority until the time budget is exhausted."""
        pending = [t for t in self.owner.get_tasks() if not t.completed]
        today = date.today()
        sorted_tasks = sorted(pending, key=lambda t: self.score_task(t, today), reverse=True)

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
        """Return the plan sorted by start time (HH:MM) ascending; untimed tasks sort last."""
        def _key(t: Task) -> tuple[int, int]:
            if not t.time:
                return (24, 0)   # sentinel — after any valid HH:MM
            h, m = t.time.split(":")
            return (int(h), int(m))
        return sorted(self._plan, key=_key)

    def sort_by_priority_then_time(self) -> list[Task]:
        """Return the plan sorted by priority descending, then by start time ascending.

        Within the same priority level, timed tasks are ordered chronologically;
        untimed tasks appear after all timed tasks in that priority group.
        """
        def _key(t: Task) -> tuple[int, int, int]:
            if not t.time:
                h, m = 24, 0   # sentinel — after any valid HH:MM
            else:
                h, m = t.time.split(":")
                h, m = int(h), int(m)
            return (-t.priority, h, m)
        return sorted(self._plan, key=_key)

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
        today = date.today()
        for task in self._plan:
            score = self.score_task(task, today)
            urgency_note = ""
            if task.due_date is not None:
                days = (task.due_date - today).days
                if days < 0:
                    urgency_note = f" [OVERDUE by {abs(days)}d]"
                elif days == 0:
                    urgency_note = " [DUE TODAY]"
                elif days <= 3:
                    urgency_note = f" [due in {days}d]"
            lines.append(
                f"  [+] [{task.priority}] {task.name} ({task.duration_minutes} min, {task.category})"
                f"  score={score:.2f}{urgency_note}"
            )

        if self._skipped:
            lines.append(f"\nSkipped {len(self._skipped)} task(s) -- insufficient time remaining:")
            for task in self._skipped:
                score = self.score_task(task, today)
                lines.append(f"  [-] [{task.priority}] {task.name} ({task.duration_minutes} min)  score={score:.2f}")

        lines.append(
            f"\nTasks are ordered by composite score = "
            f"(priority x {self.priority_weight}) + (urgency x {self.urgency_weight}) + category_boost."
        )
        return "\n".join(lines)
