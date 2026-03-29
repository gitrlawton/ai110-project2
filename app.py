import streamlit as st
from datetime import date
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
    "dog":   "🐕",
    "cat":   "🐈",
    "bird":  "🐦",
    "other": "🐾",
}


def _priority_label(priority: int) -> str:
    if priority >= 4:
        return "🔴 High"
    elif priority >= 2:
        return "🟡 Medium"
    return "🟢 Low"


def _category_label(category: str) -> str:
    return f"{CATEGORY_EMOJI.get(category, '📋')} {category}"


def _status_label(completed: bool) -> str:
    return "✅ Done" if completed else "⏳ Pending"


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ── Session state initialization ──────────────────────────────────────────────
# st.session_state works like a dictionary that survives page reruns.
# We check whether "owner" already exists before creating one so we don't
# wipe out any tasks or preferences the user has already added.
if "owner" not in st.session_state:
    try:
        st.session_state.owner = Owner.load_from_json("data.json")
    except FileNotFoundError:
        default_pet = Pet(name="Mochi", species="cat", age=1)
        st.session_state.owner = Owner(
            name="Jordan",
            available_minutes=60,
            pet=default_pet,
        )

st.title("🐾 PawPal+")

st.divider()

# ── Section 1: Owner & Pet Setup ──────────────────────────────────────────────
st.subheader("Owner & Pet Setup")
owner = st.session_state.owner

with st.form("pet_form"):
    col1, col2 = st.columns(2)
    with col1:
        owner_name = st.text_input("Owner name", value=owner.name)
        available_minutes = st.number_input(
            "Time available today (min)", min_value=5, max_value=480, value=owner.available_minutes
        )
    with col2:
        pet_name = st.text_input("Pet name", value=owner.pet.name)
        species = st.selectbox(
            "Species",
            ["dog", "cat", "bird", "other"],
            index=["dog", "cat", "bird", "other"].index(owner.pet.species)
            if owner.pet.species in ["dog", "cat", "bird", "other"] else 0,
            format_func=lambda s: f"{SPECIES_EMOJI.get(s, '🐾')} {s}",
        )
        age = st.number_input("Pet age", min_value=0, max_value=30, value=owner.pet.age)
        special_needs = st.text_input("Special needs (optional)", value=owner.pet.special_needs)

    if st.form_submit_button("Save owner & pet"):
        # Pet() is a dataclass — just construct it with the form values.
        # Owner is updated in-place so existing tasks are preserved.
        new_pet = Pet(name=pet_name, species=species, age=age, special_needs=special_needs)
        st.session_state.owner.name = owner_name
        st.session_state.owner.available_minutes = available_minutes
        st.session_state.owner.pet = new_pet
        st.session_state.owner.save_to_json()
        st.success(f"Saved! {owner_name}'s pet: {new_pet.summary()}")

pet = st.session_state.owner.pet
st.caption(f"{SPECIES_EMOJI.get(pet.species, '🐾')} {pet.summary()}")

st.divider()

# ── Section 2: Add Tasks ──────────────────────────────────────────────────────
PRIORITY_MAP = {"low": 1, "medium": 3, "high": 5}

st.subheader("Tasks")

with st.form("task_form"):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_name = st.text_input("Task name", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority_label = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col4:
        category = st.selectbox(
            "Category",
            ["exercise", "feeding", "medication", "enrichment", "grooming", "other"],
            format_func=_category_label,
        )

    col5, col6 = st.columns(2)
    with col5:
        due_date_input = st.date_input("Due date (optional)", value=None)
    with col6:
        task_time = st.text_input("Scheduled time (HH:MM, optional)", value="")

    if st.form_submit_button("Add task"):
        # owner.add_task() appends to the Owner's internal list and persists
        # for the rest of the session because owner lives in st.session_state.
        new_task = Task(
            name=task_name,
            duration_minutes=int(duration),
            priority=PRIORITY_MAP[priority_label],
            category=category,
            time=task_time.strip(),
            due_date=due_date_input,
        )
        st.session_state.owner.add_task(new_task)
        st.session_state.owner.save_to_json()
        st.success(f"Added: {task_name} ({duration} min)")

# owner.get_tasks() reads the live list — automatically reflects any additions.
tasks = st.session_state.owner.get_tasks()
if tasks:
    st.write("Current tasks:")
    st.dataframe(
        [
            {
                "Status": _status_label(t.completed),
                "Task": t.name,
                "Priority": _priority_label(t.priority),
                "Category": _category_label(t.category),
                "Duration (min)": t.duration_minutes,
                "Due": str(t.due_date) if t.due_date else "—",
                "Time": t.time if t.time else "—",
            }
            for t in tasks
        ],
        hide_index=True,
        use_container_width=True,
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ── Section 3: Generate Schedule ─────────────────────────────────────────────
st.subheader("Build Schedule")

st.caption("Scoring weights — 1.0 = balanced; increase to emphasize that dimension")
wc1, wc2 = st.columns(2)
with wc1:
    priority_weight = st.slider("Priority weight", 0.0, 2.0, 1.0, 0.1)
with wc2:
    urgency_weight = st.slider("Urgency weight", 0.0, 2.0, 1.0, 0.1)

if st.button("Generate schedule"):
    scheduler = Scheduler(st.session_state.owner, priority_weight=priority_weight, urgency_weight=urgency_weight)
    plan = scheduler.generate_plan()

    if not plan:
        st.warning("No tasks could be scheduled. Add some tasks or increase available time.")
    else:
        # ── Conflict warnings ────────────────────────────────────────────────
        # Shown before the plan so the owner sees problems immediately.
        conflicts = scheduler.detect_conflicts()
        if conflicts:
            st.error(
                f"⚠️ {len(conflicts)} time conflict(s) found — "
                "two or more tasks are scheduled at the same time. "
                "Review the conflicts below and adjust task times before starting your day."
            )
            for msg in conflicts:
                st.warning(msg)
        else:
            st.success(f"Schedule ready — {len(plan)} task(s), no conflicts.")

        # ── Summary metrics ──────────────────────────────────────────────────
        total_minutes = sum(t.duration_minutes for t in plan)
        pct = int(total_minutes / st.session_state.owner.available_minutes * 100)
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Tasks scheduled", len(plan))
        mc2.metric("Time used", f"{total_minutes} / {st.session_state.owner.available_minutes} min")
        mc3.metric("Budget used", f"{pct}%")

        # ── Sort display order ───────────────────────────────────────────────
        # Priority-first, then chronological within each priority group.
        display_order = scheduler.sort_by_priority_then_time()

        st.write("**Your plan for today:**")
        today = date.today()
        st.dataframe(
            [
                {
                    "Time": t.time if t.time else "—",
                    "Task": t.name,
                    "Pet": t.pet_name if t.pet_name else "—",
                    "Duration (min)": t.duration_minutes,
                    "Priority": _priority_label(t.priority),
                    "Category": _category_label(t.category),
                    "Due": str(t.due_date) if t.due_date else "—",
                    "Score": f"{scheduler.score_task(t, today):.2f}",
                }
                for t in display_order
            ],
            hide_index=True,
            use_container_width=True,
        )

        # ── Skipped tasks ────────────────────────────────────────────────────
        skipped = scheduler.filter_tasks(completed=False)
        skipped = [t for t in skipped if t not in plan]
        if skipped:
            with st.expander(f"⏭ {len(skipped)} task(s) skipped — not enough time remaining"):
                st.dataframe(
                    [
                        {
                            "Task": t.name,
                            "Priority": _priority_label(t.priority),
                            "Category": _category_label(t.category),
                            "Duration (min)": t.duration_minutes,
                        }
                        for t in skipped
                    ],
                    hide_index=True,
                    use_container_width=True,
                )

        with st.expander("💡 Why this plan?"):
            st.code(scheduler.explain(), language=None)
