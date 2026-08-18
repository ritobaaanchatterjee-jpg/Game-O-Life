import streamlit as st
import pandas as pd
import plotly.express as px
import random

st.set_page_config(page_title="Advanced Human Life & Trauma Simulation Engine", layout="wide")

st.title("Advanced Multi-Agent Life & Society Simulation")
st.markdown("Simulating demographics, non-linear relationships, specific medical conditions, 40+ positive life milestones, and wealth trajectories over time.")

# --- INITIALIZE AGENT POPULATION (5 Agents) ---
if "agents" not in st.session_state:
    st.session_state.agents = [
        {
            "id": 1,
            "name": "Elias",
            "age": 24,
            "position": "Junior Analyst",
            "income": 42000,
            "net_worth": 15000,
            "lifespan": 78,
            "health": 95,
            "stress": 40,
            "status": "Active",
            "trauma": "Fear of isolation"
        },
        {
            "id": 2,
            "name": "Clara",
            "age": 29,
            "position": "Senior Developer",
            "income": 95000,
            "net_worth": 65000,
            "lifespan": 82,
            "health": 90,
            "stress": 60,
            "status": "Active",
            "trauma": "Hyper-vigilance"
        },
        {
            "id": 3,
            "name": "Marcus",
            "age": 58,
            "position": "Operations Manager",
            "income": 120000,
            "net_worth": 140000,
            "lifespan": 75,
            "health": 70,
            "stress": 75,
            "status": "Active",
            "trauma": "Survivor guilt"
        },
        {
            "id": 4,
            "name": "Aarav",
            "age": 21,
            "position": "Intern",
            "income": 25000,
            "net_worth": 3000,
            "lifespan": 80,
            "health": 98,
            "stress": 20,
            "status": "Active",
            "trauma": "Imposter syndrome"
        },
        {
            "id": 5,
            "name": "Priya",
            "age": 40,
            "position": "Director",
            "income": 160000,
            "net_worth": 250000,
            "lifespan": 76,
            "health": 75,
            "stress": 65,
            "status": "Active",
            "trauma": "Perfectionism"
        }
    ]

# Initialize non-linear relationship matrix dynamically for all agents
if "relationships" not in st.session_state:
    st.session_state.relationships = {}
    agent_names = [a["name"] for a in st.session_state.agents]
    for p1 in agent_names:
        for p2 in agent_names:
            if p1 != p2:
                st.session_state.relationships[(p1, p2)] = random.randint(-30, 50)

if "event_logs" not in st.session_state:
    st.session_state.event_logs = []

# --- ACTUAL DISEASES POOL ---
ACTUAL_DISEASES = [
    {"name": "Severe Pneumonia", "health_drop": 35, "stress_add": 25},
    {"name": "Type 2 Diabetes Diagnosis", "health_drop": 20, "stress_add": 30},
    {"name": "Hypertension Flare-up", "health_drop": 15, "stress_add": 20},
    {"name": "Chronic Migraine Syndrome", "health_drop": 10, "stress_add": 18},
    {"name": "Acute Appendicitis (Surgical Recovery)", "health_drop": 30, "stress_add": 22},
    {"name": "Gastroenteritis Infection", "health_drop": 12, "stress_add": 10},
    {"name": "Severe Asthma Exacerbation", "health_drop": 25, "stress_add": 28},
    {"name": "Clinical Burnout Syndrome", "health_drop": 18, "stress_add": 40}
]

# --- 40+ POSITIVE EVENTS POOL ---
POSITIVE_EVENTS = [
    "Published an acclaimed research paper",
    "Won a community lottery prize",
    "Cleared a major debt milestone entirely",
    "Received an unexpected financial inheritance",
    "Successfully launched a profitable side hustle",
    "Adopted a rescue pet, boosting mental wellness",
    "Completed a local marathon with a personal best time",
    "Mentored a junior colleague who achieved promotion",
    "Purchased a dream home resulting in property appreciation",
    "Granted lucrative corporate stock options and equity vesting",
    "Authored an industry-viral article or blog post",
    "Won a competitive regional coding championship",
    "Received a prestigious national professional award",
    "Successfully negotiated flexible remote working arrangements",
    "Completely wiped out student loan balances",
    "Formed a deeply fulfilling romantic partnership",
    "Welcomed a new family addition with great joy",
    "Accepted into a highly selective executive leadership fellowship",
    "Discovered a high-return venture capital investment opportunity",
    "Received a substantial performance-based cash bonus",
    "Released an open-source tool that gained massive global traction",
    "Successfully mediated and resolved a long-standing family dispute",
    "Completed a transformative personal sabbatical and vacation",
    "Upgraded personal workspace ergonomics and tech hardware setup",
    "Elected unanimously to a corporate board of advisors",
    "Secured a high-paying freelance advisory consulting gig",
    "Passed a rigorous advanced professional certification exam",
    "Reconnected with a supportive and influential childhood mentor",
    "Won a regional sports club tournament trophy",
    "Invented and registered a groundbreaking utility patent",
    "Received glowing commendations directly from senior executive leadership",
    "Successfully crowd-funded a creative community project",
    "Overcame chronic health hurdles through disciplined lifestyle adjustments",
    "Acquired a residential rental property yielding stable passive income",
    "Built a high-value professional network across international markets",
    "Granted a fully paid corporate creative sabbatical",
    "Published a bestselling non-fiction manual or guide",
    "Secured a major municipal innovation and design grant",
    "Organized and spearheaded a highly successful community charity drive",
    "Received an unexpected tax rebate and government refund check",
    "Successfully completed advanced public speaking masterclasses",
    "Planted an award-winning urban botanical garden on a rooftop terrace"
]

# --- CONTROL PANEL FOR TIME RANDOMIZER & SIMULATION STEP ---
st.sidebar.header("Simulation Control Panel")
simulation_years = st.sidebar.slider("Advance Simulation Timeline (Years)", 1, 10, 3)

if st.sidebar.button("Run Simulation Step (Tick Time)"):
    for _ in range(simulation_years):
        for agent in st.session_state.agents:
            # 1. ABSOLUTE GUARD: Skip deceased agents completely to prevent post-mortem events
            if agent["status"] == "Deceased":
                continue
                
            # Age progression
            agent["age"] += 1
            
            # Age 60+ stress lock
            if agent["age"] >= 60:
                agent["stress"] = 100

            # Stress & health inverse proportionality
            if agent["stress"] > 70:
                agent["health"] -= int((agent["stress"] - 70) / 6) + 1
            if agent["health"] < 40 and agent["age"] < 60:
                agent["stress"] = min(100, agent["stress"] + 6)

            # Early death / lifespan expiration check
            early_death_risk = 0.08 if (agent["health"] < 25 or agent["stress"] == 100) else 0.015
            if agent["age"] >= agent["lifespan"] or agent["health"] <= 0 or random.random() < early_death_risk:
                agent["status"] = "Deceased"
                agent["health"] = 0
                st.session_state.event_logs.insert(0, f"💀 **{agent['name']}** passed away prematurely at age {agent['age']} (Final Health: {agent['health']}, Stress: {agent['stress']}).")
                continue  # Stop execution for this agent immediately

            # Stochastic Event Probabilities (Only active agents reach here)
            roll = random.random()
            
            # 1. Specific Actual Disease Trigger (4% chance)
            if roll < 0.04:
                disease = random.choice(ACTUAL_DISEASES)
                agent["health"] -= disease["health_drop"]
                if agent["age"] < 60:
                    agent["stress"] = min(100, agent["stress"] + disease["stress_add"])
                st.session_state.event_logs.insert(0, f"🦠 **{agent['name']}** diagnosed with **{disease['name']}**! Health decreased by {disease['health_drop']}.")
            
            # 2. Accident Trigger (5% chance)
            elif roll < 0.09:
                agent["health"] -= 20
                agent["net_worth"] -= 8000
                st.session_state.event_logs.insert(0, f"🚑 **{agent['name']}** was involved in an accident. Medical bills drained savings.")
            
            # 3. Promotion Trigger (6% chance)
            elif roll < 0.15 and agent["age"] < 60:
                agent["income"] = int(agent["income"] * 1.25)
                agent["net_worth"] += int(agent["income"] * 0.3)
                st.session_state.event_logs.insert(0, f"📈 **{agent['name']}** received a promotion! Income increased.")
            
            # 4. Positive Milestone Events (40+ options pool, 25% chance range)
            elif roll < 0.40:
                pos_event = random.choice(POSITIVE_EVENTS)
                agent["net_worth"] += random.randint(3000, 15000)
                if agent["age"] < 60:
                    agent["stress"] = max(10, agent["stress"] - random.randint(5, 15))
                agent["health"] = min(100, agent["health"] + random.randint(1, 5))
                st.session_state.event_logs.insert(0, f"✨ **{agent['name']}**: {pos_event}!")

            # 5. Salary Decrease / Pay Cut Trigger (10% chance)
            elif roll < 0.50:
                cut_rate = random.uniform(0.1, 0.3)
                agent["income"] = max(10000, int(agent["income"] * (1 - cut_rate)))
                if agent["age"] < 60:
                    agent["stress"] = min(100, agent["stress"] + 15)
                st.session_state.event_logs.insert(0, f"📉 **{agent['name']}** suffered a salary decrease due to market deflation/pay cuts.")

            # 6. Fired / Laid Off Trigger (6% chance)
            elif roll < 0.56 and agent["age"] < 60:
                agent["income"] = int(agent["income"] * 0.5)
                agent["net_worth"] -= 12000
                agent["stress"] = min(100, agent["stress"] + 40)
                st.session_state.event_logs.insert(0, f"🚨 **{agent['name']}** got laid off, causing a major financial and stress shock.")

            # Standard annual wealth, health, and stress drift
            savings_rate = random.uniform(0.1, 0.3)
            agent["net_worth"] += int(agent["income"] * savings_rate)
            if agent["age"] < 60:
                agent["stress"] = max(10, min(100, agent["stress"] + random.randint(-5, 8)))
            agent["health"] = max(0, min(100, agent["health"] + random.randint(-3, 2)))

    st.sidebar.success(f"Advanced simulation by {simulation_years} years completed!")

if st.sidebar.button("Reset Simulation"):
    del st.session_state.agents
    del st.session_state.relationships
    del st.session_state.event_logs
    st.rerun()

# --- DASHBOARD LAYOUT ---
tab1, tab2, tab3 = st.tabs(["Demographics & Wealth", "Non-Linear Relationships", "Life Event Logs"])

with tab1:
    st.subheader("Current Population State")
    df_agents = pd.DataFrame(st.session_state.agents)
    st.dataframe(df_agents, use_container_width=True)

    st.subheader("Net Worth vs Age Trajectory")
    fig_wealth = px.bar(df_agents, x="name", y="net_worth", color="position", text="net_worth", title="Agent Net Worth Comparison")
    st.plotly_chart(fig_wealth, use_container_width=True)

with tab2:
    st.subheader("Non-Linear Social Relationship Matrix (Trust & Affinity)")
    rel_data = []
    for (p1, p2), score in st.session_state.relationships.items():
        rel_data.append({"Agent A": p1, "Agent B": p2, "Bond Score": score})
    
    df_rel = pd.DataFrame(rel_data)
    st.dataframe(df_rel, use_container_width=True)
    
    fig_rel = px.bar(df_rel, x="Agent A", y="Bond Score", color="Agent B", barmode="group", title="Inter-Agent Relational Bonds (-100 to 100)")
    st.plotly_chart(fig_rel, use_container_width=True)

with tab3:
    st.subheader("Stochastic Life Events Feed")
    if st.session_state.event_logs:
        for log in st.session_state.event_logs[:40]:
            st.markdown(f"- {log}")
    else:
        st.info("Run the simulation step from the sidebar to generate probabilistic life events!")
