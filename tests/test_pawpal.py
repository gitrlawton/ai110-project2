import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Pet, Task, Owner


def make_task(**kwargs) -> Task:
    defaults = dict(name="Walk", duration_minutes=20, priority=3, category="exercise")
    return Task(**{**defaults, **kwargs})


def make_owner() -> Owner:
    pet = Pet(name="Biscuit", species="Dog", age=4)
    return Owner(name="Alex", available_minutes=60, pet=pet)


def test_mark_complete_changes_status():
    task = make_task()
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_count():
    owner = make_owner()
    assert len(owner.get_tasks()) == 0
    owner.add_task(make_task(name="Feed"))
    owner.add_task(make_task(name="Groom"))
    assert len(owner.get_tasks()) == 2
