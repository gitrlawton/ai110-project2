from datetime import date
from pawpal_system import Pet, Task, Owner, Scheduler

# --- Pets ---
biscuit = Pet(name="Biscuit", species="Dog", age=4, special_needs="Joint supplement with meals")
mochi = Pet(name="Mochi", species="Cat", age=2)

# --- Owner ---
owner = Owner(
    name="Alex",
    available_minutes=75,
    pet=biscuit,
    preferences=["morning walks", "no tasks after 8pm"],
)

TODAY = date.today()

# --- Tasks added OUT OF ORDER by time (to demonstrate sort_by_time) ---
owner.add_task(Task(name="Mochi playtime",           duration_minutes=20, priority=3, category="enrichment",  time="15:00", pet_name="Mochi",    frequency="daily",  due_date=TODAY))
owner.add_task(Task(name="Biscuit joint supplement", duration_minutes=5,  priority=4, category="medication",  time="08:15", pet_name="Biscuit",  frequency="daily",  due_date=TODAY, completed=True))
owner.add_task(Task(name="Groom Biscuit",            duration_minutes=25, priority=2, category="grooming",    time="11:00", pet_name="Biscuit",  frequency="weekly", due_date=TODAY))
owner.add_task(Task(name="Walk Biscuit",             duration_minutes=30, priority=5, category="exercise",    time="07:00", pet_name="Biscuit",  frequency="daily",  due_date=TODAY))
owner.add_task(Task(name="Feed Biscuit & Mochi",     duration_minutes=10, priority=5, category="feeding",     time="08:00", pet_name="Biscuit",  frequency="daily",  due_date=TODAY))
# Intentional conflict: Mochi vet check shares Mochi's 15:00 playtime slot
owner.add_task(Task(name="Mochi vet check",          duration_minutes=15, priority=4, category="health",      time="15:00", pet_name="Mochi",    frequency="once",   due_date=TODAY))

# --- Generate plan ---
scheduler = Scheduler(owner)
plan = scheduler.generate_plan()

# --- Print Today's Schedule (priority order) ---
WIDTH = 54

print("=" * WIDTH)
print("           TODAY'S SCHEDULE  —  PawPal+")
print("=" * WIDTH)
print(f"  Owner : {owner.name}")
print(f"  Pets  : {biscuit.summary()}")
print(f"          {mochi.summary()}")
print(f"  Budget: {owner.available_minutes} min available")
print("-" * WIDTH)
print(f"  {'#':<4} {'Task':<30} {'Min':>5}  Pri")
print("-" * WIDTH)

for i, task in enumerate(plan, 1):
    stars = "*" * task.priority
    print(f"  {i:<4} {task.name:<30} {task.duration_minutes:>4}m  {stars}")

print("-" * WIDTH)
total = sum(t.duration_minutes for t in plan)
print(f"  Total: {total} of {owner.available_minutes} min scheduled")
print("=" * WIDTH)
print()
print(scheduler.explain())

# --- Conflict detection ---
print()
print("=" * WIDTH)
print("         CONFLICT DETECTION  (detect_conflicts)")
print("=" * WIDTH)
conflicts = scheduler.detect_conflicts()
if conflicts:
    for warning in conflicts:
        print(f"  {warning}")
else:
    print("  No scheduling conflicts found.")
print("=" * WIDTH)

# --- Demo: sort_by_time ---
print()
print("=" * WIDTH)
print("         SORTED BY START TIME  (sort_by_time)")
print("=" * WIDTH)
print(f"  {'Time':<8} {'Task':<28} {'Min':>5}")
print("-" * WIDTH)
for task in scheduler.sort_by_time():
    print(f"  {task.time:<8} {task.name:<28} {task.duration_minutes:>4}m")
print("=" * WIDTH)

# --- Demo: filter_tasks by completion status ---
print()
print("=" * WIDTH)
print("        FILTER: incomplete tasks  (completed=False)")
print("=" * WIDTH)
for task in scheduler.filter_tasks(completed=False):
    print(f"  [ ] {task.name}")

print()
print("=" * WIDTH)
print("        FILTER: completed tasks   (completed=True)")
print("=" * WIDTH)
for task in scheduler.filter_tasks(completed=True):
    print(f"  [x] {task.name}")

# --- Demo: filter_tasks by pet name ---
print()
print("=" * WIDTH)
print("        FILTER: Biscuit's tasks   (pet_name='Biscuit')")
print("=" * WIDTH)
for task in scheduler.filter_tasks(pet_name="Biscuit"):
    print(f"  {task.name}")

print()
print("=" * WIDTH)
print("        FILTER: Mochi's tasks     (pet_name='Mochi')")
print("=" * WIDTH)
for task in scheduler.filter_tasks(pet_name="Mochi"):
    print(f"  {task.name}")
print("=" * WIDTH)

# --- Demo: mark_task_complete with recurrence ---
print()
print("=" * WIDTH)
print("        RECURRENCE  (mark_task_complete)")
print("=" * WIDTH)

walk_task  = next(t for t in plan if t.name == "Walk Biscuit")
mochi_task = next(t for t in plan if t.name == "Mochi playtime")

for task in (walk_task, mochi_task):
    next_occurrence = scheduler.mark_task_complete(task)
    status = "completed"
    print(f"  [{status}] {task.name}  (frequency: {task.frequency}, due: {task.due_date})")
    if next_occurrence:
        print(f"     --> Next occurrence created: due {next_occurrence.due_date}")
    print()

# Groom Biscuit is weekly — it was skipped by the scheduler, so fetch from owner
groom_task = next(t for t in owner.get_tasks() if t.name == "Groom Biscuit")
next_groom = scheduler.mark_task_complete(groom_task)
print(f"  [completed] {groom_task.name}  (frequency: {groom_task.frequency}, due: {groom_task.due_date})")
if next_groom:
    delta = next_groom.due_date - groom_task.due_date
    print(f"     --> Next occurrence created: due {next_groom.due_date}  (+{delta.days} days)")
print("=" * WIDTH)
