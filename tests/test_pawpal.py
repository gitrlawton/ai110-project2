import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date
from pawpal_system import Pet, Task, Owner, Scheduler


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


def make_scheduler(*tasks) -> Scheduler:
    """Return a Scheduler whose owner already has the given tasks and a 120-min budget."""
    owner = make_owner()
    owner.available_minutes = 120
    for t in tasks:
        owner.add_task(t)
    return Scheduler(owner)


# ---------------------------------------------------------------------------
# generate_plan — happy path & edge cases
# ---------------------------------------------------------------------------

def test_generate_plan_orders_by_priority():
    low  = make_task(name="Low",  priority=1, duration_minutes=10)
    high = make_task(name="High", priority=5, duration_minutes=10)
    mid  = make_task(name="Mid",  priority=3, duration_minutes=10)
    s = make_scheduler(low, high, mid)
    plan = s.generate_plan()
    assert [t.name for t in plan] == ["High", "Mid", "Low"]


def test_generate_plan_respects_time_budget():
    big   = make_task(name="Big",   priority=2, duration_minutes=100)
    small = make_task(name="Small", priority=1, duration_minutes=10)
    owner = make_owner()
    owner.available_minutes = 15          # fits Small but not Big
    owner.add_task(big)
    owner.add_task(small)
    s = Scheduler(owner)
    plan = s.generate_plan()
    assert len(plan) == 1
    assert plan[0].name == "Small"


def test_generate_plan_empty_when_no_tasks():
    s = make_scheduler()
    plan = s.generate_plan()
    assert plan == []


def test_generate_plan_skips_completed_tasks():
    done    = make_task(name="Done",    duration_minutes=10, completed=True)
    pending = make_task(name="Pending", duration_minutes=10)
    s = make_scheduler(done, pending)
    plan = s.generate_plan()
    assert len(plan) == 1
    assert plan[0].name == "Pending"


def test_generate_plan_zero_budget_skips_everything():
    owner = make_owner()
    owner.available_minutes = 0
    owner.add_task(make_task(name="Walk", duration_minutes=1))
    s = Scheduler(owner)
    plan = s.generate_plan()
    assert plan == []


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_daily_recurrence_creates_next_day_task():
    today = date(2026, 3, 27)
    task = make_task(name="Feed", frequency="daily", due_date=today, duration_minutes=5)
    s = make_scheduler(task)
    s.generate_plan()
    next_task = s.mark_task_complete(task)
    assert next_task is not None
    assert next_task.due_date == date(2026, 3, 28)
    assert next_task.completed is False


def test_weekly_recurrence_creates_next_week_task():
    today = date(2026, 3, 27)
    task = make_task(name="Bath", frequency="weekly", due_date=today, duration_minutes=20)
    s = make_scheduler(task)
    s.generate_plan()
    next_task = s.mark_task_complete(task)
    assert next_task is not None
    assert next_task.due_date == date(2026, 4, 3)


def test_once_task_returns_no_next_occurrence():
    task = make_task(name="Vet", frequency="once", duration_minutes=30)
    s = make_scheduler(task)
    s.generate_plan()
    result = s.mark_task_complete(task)
    assert result is None


def test_recurrence_adds_task_to_owner():
    today = date(2026, 3, 27)
    task = make_task(name="Feed", frequency="daily", due_date=today, duration_minutes=5)
    s = make_scheduler(task)
    s.generate_plan()
    before = len(s.owner.get_tasks())
    s.mark_task_complete(task)
    assert len(s.owner.get_tasks()) == before + 1


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_flags_duplicate_time():
    t1 = make_task(name="Walk",  time="08:30", duration_minutes=20)
    t2 = make_task(name="Feed",  time="08:30", duration_minutes=10)
    s = make_scheduler(t1, t2)
    s.generate_plan()
    warnings = s.detect_conflicts()
    assert len(warnings) == 1
    assert "08:30" in warnings[0]
    assert "Walk" in warnings[0]
    assert "Feed" in warnings[0]


def test_detect_conflicts_no_warning_for_distinct_times():
    t1 = make_task(name="Walk", time="08:00", duration_minutes=20)
    t2 = make_task(name="Feed", time="09:00", duration_minutes=10)
    s = make_scheduler(t1, t2)
    s.generate_plan()
    assert s.detect_conflicts() == []


def test_detect_conflicts_ignores_tasks_with_no_time():
    t1 = make_task(name="Walk", time="",     duration_minutes=20)
    t2 = make_task(name="Feed", time="",     duration_minutes=10)
    s = make_scheduler(t1, t2)
    s.generate_plan()
    assert s.detect_conflicts() == []


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    t1 = make_task(name="Evening", time="18:00", duration_minutes=10)
    t2 = make_task(name="Morning", time="08:00", duration_minutes=10)
    t3 = make_task(name="Noon",    time="12:30", duration_minutes=10)
    s = make_scheduler(t1, t2, t3)
    s.generate_plan()
    sorted_tasks = s.sort_by_time()
    assert [t.name for t in sorted_tasks] == ["Morning", "Noon", "Evening"]


def test_sort_by_time_empty_time_raises():
    """Tasks with no scheduled time crash sort_by_time — documents the known bug."""
    import pytest
    t = make_task(name="Unscheduled", time="", duration_minutes=10)
    s = make_scheduler(t)
    s.generate_plan()
    with pytest.raises((IndexError, ValueError)):
        s.sort_by_time()
