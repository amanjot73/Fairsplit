import streamlit as st
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# -------------------------
# PAGE CONFIG
# -------------------------

st.set_page_config(
    page_title="FairSplit",
    page_icon="💸",
    layout="centered"
)

# -------------------------
# CUSTOM CSS
# -------------------------

st.markdown("""
<style>
.stApp {
    background-color: #0E1117;
    color: white;
}

h1, h2, h3 {
    color: #FFFFFF;
}

[data-testid="stMetricValue"] {
    color: #6C63FF;
}

div.stButton > button {
    background-color: #6C63FF;
    color: white;
    border-radius: 10px;
    height: 3em;
    width: 100%;
    font-size: 16px;
    font-weight: bold;
}

div.stButton > button:hover {
    background-color: #574fd6;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# SETTLEMENT LOGIC
# -------------------------

def calculate_settlements(amounts):
    n = len(amounts)

    total = sum(amounts)

    per_head = total / n if n > 0 else 0

    net = [amt - per_head for amt in amounts]

    creditors = [(i, x) for i, x in enumerate(net) if x > 0]
    debtors = [(i, -x) for i, x in enumerate(net) if x < 0]

    i, j = 0, 0

    transfers = []

    while i < len(debtors) and j < len(creditors):

        debtor_idx, debt = debtors[i]
        creditor_idx, credit = creditors[j]

        pay = min(debt, credit)

        transfers.append((debtor_idx, creditor_idx, pay))

        debtors[i] = (debtor_idx, debt - pay)
        creditors[j] = (creditor_idx, credit - pay)

        if debtors[i][1] < 0.01:
            i += 1

        if creditors[j][1] < 0.01:
            j += 1

    return transfers, per_head, total

# -------------------------
# GRAPH DRAWING
# -------------------------

def draw_graph(transfers, people):

    G = nx.DiGraph()

    for payer, payee, amount in transfers:

        if amount > 0:
            G.add_edge(
                people[payer],
                people[payee],
                weight=amount
            )

    pos = nx.spring_layout(G, seed=42)

    fig, ax = plt.subplots(figsize=(8, 6))

    fig.patch.set_facecolor('#0E1117')
    ax.set_facecolor('#0E1117')

    nx.draw(
        G,
        pos,
        with_labels=True,
        node_color='#6C63FF',
        node_size=3500,
        font_size=10,
        font_color='white',
        edgecolors='white',
        width=2,
        arrows=True,
        ax=ax
    )

    edge_labels = {
        (u, v): f"₹{d['weight']:.2f}"
        for u, v, d in G.edges(data=True)
    }

    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels=edge_labels,
        font_color='white',
        ax=ax
    )

    st.pyplot(fig)

# -------------------------
# TITLE
# -------------------------

st.title("💸 FairSplit")
st.markdown("### Split expenses fairly and visualize settlements")

st.divider()

# -------------------------
# USER INPUT
# -------------------------

n = st.number_input(
    "Enter Number of People",
    min_value=2,
    step=1
)

people = []
amounts = []

for i in range(n):

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input(
            f"Person {i+1} Name",
            key=f"name_{i}"
        )

    with col2:
        amount = st.number_input(
            f"Amount Paid by Person {i+1}",
            min_value=0.0,
            step=1.0,
            key=f"amount_{i}"
        )

    if name.strip() == "":
        name = f"Person {i+1}"

    people.append(name)
    amounts.append(amount)

# -------------------------
# VALIDATE UNIQUE NAMES
# -------------------------

if len(set(people)) != len(people):
    st.error("⚠️ Names must be unique")
    st.stop()

# -------------------------
# CALCULATE BUTTON
# -------------------------

if st.button("🚀 Calculate Settlement"):

    transfers, per_head, total = calculate_settlements(amounts)

    st.balloons()

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "💰 Total Spending",
            f"₹{total:.2f}"
        )

    with col2:
        st.metric(
            "👤 Per Head",
            f"₹{per_head:.2f}"
        )

    st.divider()

    summary_df = pd.DataFrame({
        "Person": people,
        "Amount Paid": amounts
    })

    st.subheader("🧾 Expense Summary")

    st.dataframe(
        summary_df,
        use_container_width=True
    )

    max_payer = people[np.argmax(amounts)]

    st.warning(
        f"🏆 Highest Contributor: {max_payer}"
    )

    st.subheader("🥧 Expense Distribution")

    fig2, ax2 = plt.subplots()

    fig2.patch.set_facecolor('#0E1117')
    ax2.set_facecolor('#0E1117')

    ax2.pie(
        amounts,
        labels=people,
        autopct='%1.1f%%'
    )

    st.pyplot(fig2)

    if transfers:

        st.subheader("💸 Settlement Details")

        df = pd.DataFrame([
            {
                "Who Pays": people[payer],
                "To Whom": people[payee],
                "Amount": f"₹{amount:.2f}"
            }

            for payer, payee, amount in transfers
            if amount > 0
        ])

        st.dataframe(
            df,
            use_container_width=True
        )

        csv = df.to_csv(index=False)

        st.download_button(
            label="📥 Download Settlement CSV",
            data=csv,
            file_name="settlements.csv",
            mime="text/csv"
        )

        st.subheader("📊 Settlement Graph")

        draw_graph(transfers, people)

        st.info("""
### ⚡ Algorithm Used
Greedy Algorithm

### ⏱️ Time Complexity
O(n log n)

### 🧠 Idea
Debtors and creditors are matched efficiently to minimize transactions.
""")

    else:
        st.success("🎉 Everyone paid equally. No settlements needed!")