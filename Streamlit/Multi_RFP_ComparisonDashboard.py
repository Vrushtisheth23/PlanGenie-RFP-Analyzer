import pandas as pd
import streamlit as st
import altair as alt

def show_multi_rfp_dashboard(results, uploaded_files):
    """
    Display an interactive multi-RFP comparison dashboard.

    Args:
        results (list of dict): List of analyzed RFPs (from analyzer).
        uploaded_files (list): List of uploaded files (Streamlit file_uploader).
    """
    if len(uploaded_files) <= 1:
        st.info("Upload at least 2 RFPs to enable multi-RFP comparison.")
        return

    # ---- Filter RFPs ----
    rfp_names = [r["RFP_File"] for r in results]
    selected_rfps = st.multiselect("Select RFPs to compare:", rfp_names, default=rfp_names)
    if not selected_rfps:
        st.warning("Select at least one RFP.")
        return
    filtered_results = [r for r in results if r["RFP_File"] in selected_rfps]

    # ---- Executive Summary ----
    st.subheader("📋 Executive Summary")
    for r in filtered_results:
        summary = f"""
        **{r['RFP_File']}**
        - Project Type: {r.get('Project_Type', 'N/A')}
        - Total Budget: {r.get('Cost_Estimate', {}).get('Amount', 'N/A')} INR
        - Total Duration: {r.get('Timeline', {}).get('Total_Duration_Days', 'N/A')} Days
        - Number of Skills: {len(r.get('Required_Skills', []))}
        - Number of Roles: {len(r.get('Tasks_Roles', []))}
        """
        st.markdown(summary)
        st.markdown("---")

    st.subheader("📊 Multi-RFP Comparison Dashboard")

    # ---- Budget Comparison ----
    budget_data = [
        {"RFP": r["RFP_File"], "Budget": r.get("Cost_Estimate", {}).get("Amount", 0)}
        for r in filtered_results
    ]
    if budget_data:
        df_budget = pd.DataFrame(budget_data)
        df_budget["Alert"] = df_budget["Budget"].apply(lambda x: "⚠️ High" if x > 1000000 else "✅ Normal")
        chart = alt.Chart(df_budget).mark_bar().encode(
            x=alt.X("RFP", sort=None),
            y=alt.Y("Budget"),
            color=alt.Color("Alert:N", scale=alt.Scale(domain=["⚠️ High", "✅ Normal"],
                                                       range=["red", "green"])),
            tooltip=["RFP", "Budget", "Alert"]
        ).properties(width=700, height=400).interactive()
        st.markdown("**💰 Budget Comparison**")
        st.altair_chart(chart, use_container_width=True)

    # ---- Timeline / Phase Comparison ----
    timeline_rows = []
    for r in filtered_results:
        for phase in r.get("Timeline", {}).get("Phases", []):
            timeline_rows.append({
                "RFP": r["RFP_File"],
                "Phase": phase.get("Phase", ""),
                "Duration": phase.get("Duration_Days", 0),
                "Estimated_Budget": phase.get("Estimated_Budget", 0)
            })
    if timeline_rows:
        df_timeline = pd.DataFrame(timeline_rows)
        df_timeline["Alert"] = df_timeline["Duration"].apply(lambda x: "⚠️ Long" if x > 30 else "✅ Normal")
        chart = alt.Chart(df_timeline).mark_bar().encode(
            x=alt.X('Phase:N', sort=None),
            y='Duration:Q',
            color=alt.Color("Alert:N", scale=alt.Scale(domain=["⚠️ Long", "✅ Normal"], range=["orange", "skyblue"])),
            tooltip=['RFP', 'Phase', 'Duration', 'Estimated_Budget', 'Alert']
        ).properties(width=700, height=400).interactive()
        st.markdown("**⏱ Phase Duration Comparison**")
        st.altair_chart(chart, use_container_width=True)

    # ---- Skills Overlap ----
    skills_dict = {}
    for r in filtered_results:
        for skill in r.get("Required_Skills", []):
            skills_dict[skill] = skills_dict.get(skill, 0) + 1
    if skills_dict:
        df_skills = pd.DataFrame(list(skills_dict.items()), columns=["Skill", "Count"]).sort_values(by="Count", ascending=False)
        chart = alt.Chart(df_skills).mark_bar().encode(
            x='Count',
            y=alt.Y('Skill', sort='-x'),
            tooltip=['Skill', 'Count'],
            color='Count:N'
        ).properties(width=700, height=400)
        st.markdown("**🛠 Skills Across Selected RFPs**")
        st.altair_chart(chart, use_container_width=True)

    # ---- Roles Overlap ----
    roles_dict = {}
    for r in filtered_results:
        for role in r.get("Tasks_Roles", []):
            roles_dict[role.get("Role")] = roles_dict.get(role.get("Role"), 0) + 1
    if roles_dict:
        df_roles = pd.DataFrame(list(roles_dict.items()), columns=["Role", "Count"]).sort_values(by="Count", ascending=False)
        st.markdown("**👥 Roles Across Selected RFPs**")
        st.table(df_roles)

    # ---- Optional Alerts Summary ----
    st.subheader("⚠️ Alerts / Highlights")
    alerts = []
    for r in filtered_results:
        for phase in r.get("Timeline", {}).get("Phases", []):
            if phase.get("Duration_Days", 0) > 30 or phase.get("Estimated_Budget", 0) > 1000000:
                alerts.append(f"{r['RFP_File']} → {phase.get('Phase')} (Duration: {phase.get('Duration_Days')}, Budget: {phase.get('Estimated_Budget')})")
    if alerts:
        for a in alerts:
            st.warning(a)
    else:
        st.success("No critical alerts detected.")
