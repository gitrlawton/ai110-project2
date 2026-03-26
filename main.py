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

# --- Tasks (mix of both pets, varying durations and priorities) ---
owner.add_task(Task(name="Walk Biscuit",              duration_minutes=30, priority=5, category="exercise"))
owner.add_task(Task(name="Feed Biscuit & Mochi",      duration_minutes=10, priority=5, category="feeding"))
owner.add_task(Task(name="Biscuit joint supplement",  duration_minutes=5,  priority=4, category="medication"))
owner.add_task(Task(name="Mochi playtime",            duration_minutes=20, priority=3, category="enrichment"))
owner.add_task(Task(name="Groom Biscuit",             duration_minutes=25, priority=2, category="grooming"))

# --- Generate plan ---
scheduler = Scheduler(owner)
plan = scheduler.generate_plan()

# --- Print Today's Schedule ---
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
