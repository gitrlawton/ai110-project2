from dataclasses import dataclass, field


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: str = ""

    def summary(self) -> str:
        pass


@dataclass
class Task:
    name: str
    duration_minutes: int
    priority: int          # 1 (low) to 5 (high)
    category: str
    completed: bool = False


class Owner:
    def __init__(self, name: str, available_minutes: int, pet: Pet, preferences: list[str] | None = None):
        self.name = name
        self.available_minutes = available_minutes
        self.pet = pet
        self.preferences: list[str] = preferences or []
        self._tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task: Task) -> None:
        pass

    def get_tasks(self) -> list[Task]:
        pass


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self._plan: list[Task] = []

    def generate_plan(self) -> list[Task]:
        pass

    def explain(self) -> str:
        pass
