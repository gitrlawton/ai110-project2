import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
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


def test_sort_by_priority_then_time():
    """Higher priority tasks appear first; ties broken by start time ascending."""
    high_late  = make_task(name="HighLate",  priority=5, time="18:00", duration_minutes=10)
    high_early = make_task(name="HighEarly", priority=5, time="08:00", duration_minutes=10)
    low_early  = make_task(name="LowEarly",  priority=1, time="07:00", duration_minutes=10)
    s = make_scheduler(high_late, high_early, low_early)
    s.generate_plan()
    result = s.sort_by_priority_then_time()
    assert [t.name for t in result] == ["HighEarly", "HighLate", "LowEarly"]


def test_sort_by_time_places_untimed_tasks_last():
    """Tasks with no time set (time == '') sort after all timed tasks without crashing."""
    timed   = make_task(name="Morning", time="08:00", duration_minutes=10)
    untimed = make_task(name="Unscheduled", time="", duration_minutes=10)
    s = make_scheduler(timed, untimed)
    s.generate_plan()
    result = s.sort_by_time()
    assert [t.name for t in result] == ["Morning", "Unscheduled"]


# ── score_task tests ──────────────────────────────────────────────────────────

def test_score_task_no_due_date():
    """When due_date is None, urgency=0 and score = priority * priority_weight + category_boost."""
    task = make_task(priority=3, category="exercise")
    s = make_scheduler(task)
    score = s.score_task(task, today=date(2026, 3, 29))
    assert score == 3.0  # 3*1.0 + 0*1.0 + 0.0


def test_score_task_medication_boost():
    """Medication tasks receive +2.0 category_boost regardless of due_date."""
    task = make_task(priority=2, category="medication")
    s = make_scheduler(task)
    score = s.score_task(task, today=date(2026, 3, 29))
    assert score == 4.0  # 2*1.0 + 0*1.0 + 2.0


def test_overdue_task_beats_higher_priority():
    """An overdue medication task (urgency=6) outranks a higher-priority no-due-date task."""
    today = date(2026, 3, 29)
    overdue_med = make_task(
        name="OldMed", priority=2, category="medication",
        duration_minutes=10, due_date=date(2026, 3, 27),
    )
    high_prio = make_task(
        name="Groom", priority=5, category="grooming",
        duration_minutes=10,
    )
    s = make_scheduler(overdue_med, high_prio)
    s.owner.available_minutes = 120

    score_overdue = s.score_task(overdue_med, today)  # 2 + 6.0 + 2.0 = 10.0
    score_high    = s.score_task(high_prio,   today)  # 5 + 0.0 + 0.0 = 5.0
    assert score_overdue > score_high

    plan = s.generate_plan()
    assert plan[0].name == "OldMed"


def test_priority_weight_zero_ignores_priority():
    """With priority_weight=0.0, a low-priority urgent task ranks above a high-priority non-urgent one."""
    today = date(2026, 3, 29)
    urgent_low = make_task(
        name="UrgentLow", priority=1, category="exercise",
        duration_minutes=10, due_date=today,
    )
    calm_high = make_task(
        name="CalmHigh", priority=5, category="exercise",
        duration_minutes=10,
    )
    s = make_scheduler(urgent_low, calm_high)
    s.priority_weight = 0.0
    s.owner.available_minutes = 120

    score_urgent = s.score_task(urgent_low, today)  # 0 + 5.0 + 0 = 5.0
    score_calm   = s.score_task(calm_high,  today)  # 0 + 0.0 + 0 = 0.0
    assert score_urgent > score_calm

    plan = s.generate_plan()
    assert plan[0].name == "UrgentLow"


def test_urgency_ladder_values():
    """Verify that the urgency lookup produces the documented values for each bucket."""
    today = date(2026, 3, 29)
    task = make_task(priority=0, category="other")
    s = make_scheduler(task)

    cases = [
        (date(2026, 3, 28), 6.0),   # 1 day overdue
        (date(2026, 3, 29), 5.0),   # today
        (date(2026, 3, 30), 4.0),   # 1 day out
        (date(2026, 4,  1), 2.0),   # 3 days out
        (date(2026, 4,  4), 1.0),   # 6 days out (4-6 bucket)
        (date(2026, 4,  6), 0.0),   # 8 days out -> urgency=0
    ]
    for due, expected_urgency in cases:
        task.due_date = due
        score = s.score_task(task, today)
        assert score == pytest.approx(expected_urgency), (
            f"due={due}: expected urgency {expected_urgency}, got score {score}"
        )


def test_category_boost_feeding_vs_other():
    """feeding category gets +1.0 boost; exercise gets +0.0."""
    today = date(2026, 3, 29)
    feeding  = make_task(priority=2, category="feeding")
    exercise = make_task(priority=2, category="exercise")
    s = make_scheduler(feeding, exercise)

    assert s.score_task(feeding,  today) == pytest.approx(3.0)  # 2 + 0 + 1.0
    assert s.score_task(exercise, today) == pytest.approx(2.0)  # 2 + 0 + 0.0


# ---------------------------------------------------------------------------
# JSON persistence
# ---------------------------------------------------------------------------

def test_task_to_dict_round_trip():
    """to_dict / from_dict reconstructs an identical Task."""
    original = make_task(
        name="Evening walk",
        priority=4,
        category="exercise",
        time="18:00",
        pet_name="Biscuit",
        frequency="daily",
        due_date=date(2026, 4, 1),
        completed=False,
    )
    restored = Task.from_dict(original.to_dict())
    assert restored.name == original.name
    assert restored.duration_minutes == original.duration_minutes
    assert restored.priority == original.priority
    assert restored.due_date == original.due_date
    assert restored.completed == original.completed


def test_task_to_dict_serializes_due_date_as_iso_string():
    """due_date is stored as 'YYYY-MM-DD' string in the dict."""
    task = make_task(due_date=date(2026, 6, 15))
    d = task.to_dict()
    assert d["due_date"] == "2026-06-15"


def test_task_to_dict_null_due_date():
    """due_date=None is stored as None (JSON null) and round-trips correctly."""
    task = make_task()   # default due_date=None
    d = task.to_dict()
    assert d["due_date"] is None
    restored = Task.from_dict(d)
    assert restored.due_date is None


def test_owner_save_and_load_round_trip(tmp_path):
    """save_to_json / load_from_json preserves all owner, pet, and task data."""
    owner = make_owner()
    owner.add_task(make_task(name="Feed", due_date=date(2026, 4, 2), completed=True))
    owner.add_task(make_task(name="Walk", frequency="daily"))

    path = str(tmp_path / "data.json")
    owner.save_to_json(path)

    restored = Owner.load_from_json(path)

    assert restored.name == owner.name
    assert restored.available_minutes == owner.available_minutes
    assert restored.pet.name == owner.pet.name
    assert restored.pet.species == owner.pet.species

    tasks = restored.get_tasks()
    assert len(tasks) == 2
    assert tasks[0].name == "Feed"
    assert tasks[0].due_date == date(2026, 4, 2)
    assert tasks[0].completed is True
    assert tasks[1].frequency == "daily"


def test_owner_load_from_missing_file_raises(tmp_path):
    """load_from_json raises FileNotFoundError when the file does not exist."""
    with pytest.raises(FileNotFoundError):
        Owner.load_from_json(str(tmp_path / "nonexistent.json"))
