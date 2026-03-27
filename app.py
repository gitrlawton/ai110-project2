import streamlit as st
from pawpal_system import Pet, Task, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# --- Session state initialization ---
# st.session_state works like a dictionary that survives page reruns.
# We check whether "owner" already exists before creating one so we don't
# wipe out any tasks or preferences the user has already added.
if "owner" not in st.session_state:
    default_pet = Pet(name="Mochi", species="cat", age=1)
    st.session_state.owner = Owner(
        name="Jordan",
        available_minutes=60,
        pet=default_pet,
    )

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# ── Section 1: Owner & Pet Setup ─────────────────────────────────────────────
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
        st.success(f"Saved! {owner_name}'s pet: {new_pet.summary()}")

st.caption(f"Current pet: {st.session_state.owner.pet.summary()}")

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
            "Category", ["exercise", "feeding", "medication", "enrichment", "grooming", "other"]
        )

    if st.form_submit_button("Add task"):
        # owner.add_task() appends to the Owner's internal list and persists
        # for the rest of the session because owner lives in st.session_state.
        new_task = Task(
            name=task_name,
            duration_minutes=int(duration),
            priority=PRIORITY_MAP[priority_label],
            category=category,
        )
        st.session_state.owner.add_task(new_task)
        st.success(f"Added: {task_name} ({duration} min)")

# owner.get_tasks() reads the live list — automatically reflects any additions.
tasks = st.session_state.owner.get_tasks()
if tasks:
    st.write("Current tasks:")
    st.table([
        {
            "Task": t.name,
            "Duration (min)": t.duration_minutes,
            "Priority": t.priority,
            "Category": t.category,
            "Done": t.completed,
        }
        for t in tasks
    ])
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ── Section 3: Generate Schedule ─────────────────────────────────────────────
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    scheduler = Scheduler(st.session_state.owner)
    plan = scheduler.generate_plan()

    if not plan:
        st.warning("No tasks could be scheduled. Add some tasks or increase available time.")
    else:
        st.success(f"Scheduled {len(plan)} task(s)!")
        st.table([
            {
                "Task": t.name,
                "Duration (min)": t.duration_minutes,
                "Priority": t.priority,
                "Category": t.category,
            }
            for t in plan
        ])
        with st.expander("Why this plan?"):
            st.text(scheduler.explain())
