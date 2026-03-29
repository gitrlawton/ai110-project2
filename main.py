import sys
sys.stdout.reconfigure(encoding="utf-8")

from datetime import date
from tabulate import tabulate
from pawpal_system import Pet, Task, Owner, Scheduler

# ── Presentation helpers ──────────────────────────────────────────────────────

CATEGORY_EMOJI: dict[str, str] = {
    "exercise":   "🏃",
    "feeding":    "🍽️",
    "medication": "💊",
    "enrichment": "🎾",
    "grooming":   "✂️",
    "other":      "📋",
    "health":     "🏥",
}

SPECIES_EMOJI: dict[str, str] = {
    "Dog":   "🐕",
    "Cat":   "🐈",
    "Bird":  "🐦",
    "other": "🐾",
}

PRIORITY_LABEL: dict[int, str] = {
    5: "🔴 High",
    4: "🔴 High",
    3: "🟡 Med",
    2: "🟢 Low",
    1: "🟢 Low",
}


def _cat(category: str) -> str:
    return f"{CATEGORY_EMOJI.get(category, '📋')} {category}"


# ── Pets ──────────────────────────────────────────────────────────────────────

biscuit = Pet(name="Biscuit", species="Dog", age=4, special_needs="Joint supplement with meals")
mochi   = Pet(name="Mochi",   species="Cat", age=2)

# ── Owner ─────────────────────────────────────────────────────────────────────

owner = Owner(
    name="Alex",
    available_minutes=75,
    pet=biscuit,
    preferences=["morning walks", "no tasks after 8pm"],
)

TODAY = date.today()

# ── Tasks added OUT OF ORDER by time (to demonstrate sort_by_time) ────────────
owner.add_task(Task(name="Mochi playtime",           duration_minutes=20, priority=3, category="enrichment",  time="15:00", pet_name="Mochi",   frequency="daily",  due_date=TODAY))
owner.add_task(Task(name="Biscuit joint supplement", duration_minutes=5,  priority=4, category="medication",  time="08:15", pet_name="Biscuit", frequency="daily",  due_date=TODAY, completed=True))
owner.add_task(Task(name="Groom Biscuit",            duration_minutes=25, priority=2, category="grooming",    time="11:00", pet_name="Biscuit", frequency="weekly", due_date=TODAY))
owner.add_task(Task(name="Walk Biscuit",             duration_minutes=30, priority=5, category="exercise",    time="07:00", pet_name="Biscuit", frequency="daily",  due_date=TODAY))
owner.add_task(Task(name="Feed Biscuit & Mochi",     duration_minutes=10, priority=5, category="feeding",     time="08:00", pet_name="Biscuit", frequency="daily",  due_date=TODAY))
# Intentional conflict: Mochi vet check shares Mochi's 15:00 playtime slot
owner.add_task(Task(name="Mochi vet check",          duration_minutes=15, priority=4, category="health",      time="15:00", pet_name="Mochi",   frequency="once",   due_date=TODAY))

# ── Generate plan ─────────────────────────────────────────────────────────────
scheduler = Scheduler(owner)
plan = scheduler.generate_plan()

# ── Today's Schedule ──────────────────────────────────────────────────────────
print(f"\n🐾  PawPal+  —  TODAY'S SCHEDULE")
print(f"Owner : {owner.name}   {SPECIES_EMOJI.get(biscuit.species, '🐾')} {biscuit.summary()}")
print(f"         {SPECIES_EMOJI.get(mochi.species, '🐾')} {mochi.summary()}")
print(f"Budget: {owner.available_minutes} min available\n")

schedule_rows = [
    [
        i,
        task.time or "—",
        task.name,
        f"{task.duration_minutes}m",
        PRIORITY_LABEL.get(task.priority, str(task.priority)),
        _cat(task.category),
    ]
    for i, task in enumerate(plan, 1)
]
print(tabulate(
    schedule_rows,
    headers=["#", "Time", "Task", "Dur", "Priority", "Category"],
    tablefmt="fancy_grid",
))
total = sum(t.duration_minutes for t in plan)
print(f"\nTotal: {total} of {owner.available_minutes} min scheduled")

# ── Plan explanation ──────────────────────────────────────────────────────────
print()
print(scheduler.explain())

# ── Conflict detection ────────────────────────────────────────────────────────
print("\n⚠️   CONFLICT DETECTION")
conflicts = scheduler.detect_conflicts()
if conflicts:
    for warning in conflicts:
        print(f"  {warning}")
else:
    print("  ✅ No scheduling conflicts found.")

# ── Sorted by start time ──────────────────────────────────────────────────────
print("\n🕐  SORTED BY START TIME")
time_rows = [
    [task.time or "—", task.name, f"{task.duration_minutes}m", _cat(task.category)]
    for task in scheduler.sort_by_time()
]
print(tabulate(time_rows, headers=["Time", "Task", "Dur", "Category"], tablefmt="simple"))

# ── Filter: by completion status ──────────────────────────────────────────────
print("\n⏳  PENDING TASKS")
for task in scheduler.filter_tasks(completed=False):
    print(f"  ⏳  {_cat(task.category):<18}  {task.name}")

print("\n✅  COMPLETED TASKS")
for task in scheduler.filter_tasks(completed=True):
    print(f"  ✅  {_cat(task.category):<18}  {task.name}")

# ── Filter: by pet name ───────────────────────────────────────────────────────
print(f"\n{SPECIES_EMOJI.get(biscuit.species, '🐾')}  BISCUIT'S TASKS")
for task in scheduler.filter_tasks(pet_name="Biscuit"):
    print(f"  {_cat(task.category):<18}  {task.name}")

print(f"\n{SPECIES_EMOJI.get(mochi.species, '🐾')}  MOCHI'S TASKS")
for task in scheduler.filter_tasks(pet_name="Mochi"):
    print(f"  {_cat(task.category):<18}  {task.name}")

# ── Recurrence demo ───────────────────────────────────────────────────────────
print("\n🔁  RECURRENCE  (mark_task_complete)")
print("-" * 54)

walk_task  = next(t for t in plan if t.name == "Walk Biscuit")
mochi_task = next(t for t in plan if t.name == "Mochi playtime")

for task in (walk_task, mochi_task):
    next_occurrence = scheduler.mark_task_complete(task)
    print(f"  ✅  {task.name}  (frequency: {task.frequency}, due: {task.due_date})")
    if next_occurrence:
        print(f"       ↳ Next occurrence: due {next_occurrence.due_date}")
    print()

# Groom Biscuit is weekly — it was skipped by the scheduler, so fetch from owner
groom_task = next(t for t in owner.get_tasks() if t.name == "Groom Biscuit")
next_groom = scheduler.mark_task_complete(groom_task)
print(f"  ✅  {groom_task.name}  (frequency: {groom_task.frequency}, due: {groom_task.due_date})")
if next_groom:
    delta = next_groom.due_date - groom_task.due_date
    print(f"       ↳ Next occurrence: due {next_groom.due_date}  (+{delta.days} days)")
print("-" * 54)
