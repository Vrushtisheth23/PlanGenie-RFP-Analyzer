import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import pandas as pd
import streamlit as st
import altair as alt
from analysis.analyzer import analyze_rfp
from rag.llm_interface import llm_generate
from rag.retriever import RFP_Retriever
from Streamlit.Multi_RFP_ComparisonDashboard import show_multi_rfp_dashboard
from utils.export_utils import export_json, export_pdf, export_excel
from utils.skills_utils import load_internal_skills, skill_gap_analysis


# -----------------------------
# Streamlit Page Setup
# -----------------------------
st.set_page_config(page_title="📄 RFP Analyzer & Comparator", layout="wide")
st.title("📄 RFP Analyzer & Multi-RFP Comparison")

# -----------------------------
# File Upload
# -----------------------------
uploaded_files = st.file_uploader(
    "Upload RFP file(s) (.txt)", type=["txt"], accept_multiple_files=True
)

if uploaded_files:
    all_analyses = []
    retriever = RFP_Retriever()

    # -----------------------------
    # Process each RFP
    # -----------------------------
    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        file_text = uploaded_file.read().decode("utf-8", errors="ignore")

        st.subheader(f"🔎 Analyzing {file_name}...")
        with st.spinner("Analyzing RFP..."):
            analysis = analyze_rfp(file_name, file_text, llm_generate)
            analysis["raw_text"] = file_text  # store for RAG

        all_analyses.append({"RFP_File": file_name, **analysis})

    # -----------------------------
    # Streamlit Tabs
    # -----------------------------
    tab_overview, tab_timeline, tab_roles, tab_rag, tab_compare,tab_skills = st.tabs(
        ["Overview", "Timeline", "Roles & Tasks", "Ask Questions", "Compare RFPs","Skill Gap Analysis"]
    )

    # ===== Tab: Overview =====
    with tab_overview:
        for analysis in all_analyses:
            st.markdown("---")
            st.subheader(f"Project Overview: {analysis.get('RFP_File')}")
            st.markdown(f"**Project Type:** {analysis.get('Project_Type', 'N/A')}")
            st.markdown("**Scope:**")
            st.json(analysis.get("Scope", {}))
            st.markdown("**Deliverables:**")
            st.write(analysis.get("Deliverables", []))
            st.markdown("**Required Skills:**")
            st.write(analysis.get("Required_Skills", []))
            if "Cost_Estimate" in analysis:
                st.markdown("**Cost Estimate:**")
                st.json(analysis["Cost_Estimate"])

    # ===== Tab: Timeline =====
    with tab_timeline:
       # ===== Tab: Timeline =====
     st.subheader("📅 Timeline & Budget Allocation")

    import plotly.express as px

    for analysis in all_analyses:
        st.markdown(f"### {analysis.get('RFP_File')}")

        phases = analysis.get("Timeline", {}).get("Phases", [])
        if phases:
            df = pd.DataFrame(phases)

            # Normalize column names
            if "Start_Date" in df.columns and "End_Date" in df.columns:
                df["Start_Date"] = pd.to_datetime(df["Start_Date"], errors="coerce")
                df["End_Date"] = pd.to_datetime(df["End_Date"], errors="coerce")

                # ✅ KPI Cards
                total_budget = df["Estimated_Budget"].sum() if "Estimated_Budget" in df else 0
                total_duration = df["Duration_Days"].sum() if "Duration_Days" in df else 0

                col1, col2 = st.columns(2)
                col1.metric("💰 Total Estimated Budget", f"₹{total_budget:,.0f}")
                col2.metric("⏳ Total Duration", f"{total_duration} days")

                # ✅ Format budget column for labels
                if "Estimated_Budget" in df.columns:
                    df["Budget_Label"] = df["Estimated_Budget"].apply(
                        lambda x: f"₹{x:,.0f}"
                    )
                else:
                    df["Budget_Label"] = df["Phase"]

                # ✅ Plotly Gantt Chart with formatted currency labels
                fig = px.timeline(
                    df,
                    x_start="Start_Date",
                    x_end="End_Date",
                    y="Phase",
                    color="Phase",
                    text="Budget_Label",
                    title=f"Timeline for {analysis.get('RFP_File')}"
                )
                fig.update_yaxes(autorange="reversed")  # Gantt style
                fig.update_traces(textposition="inside")  # Show labels inside bars
                st.plotly_chart(fig, use_container_width=True)

            st.write("📊 Budget & Timeline Table")
            st.table(df)
        else:
            st.info("No timeline data available.")


    # ===== Tab: Roles & Tasks =====
    with tab_roles:
        st.subheader("Roles & Tasks")
        for analysis in all_analyses:
            st.markdown(f"**{analysis.get('RFP_File')}**")
            roles = analysis.get("Tasks_Roles", [])
            if roles:
                for role in roles:
                    st.markdown(f"**Role:** {role.get('Role', '')}")
                    st.write(role.get("Tasks", []))
            else:
                st.write("No roles/tasks available.")

    # ===== Tab: Ask Questions (RAG Q&A) =====
    with tab_rag:
        st.subheader("❓ Ask Questions about the RFP(s)")
        combined_text = "\n\n".join([f"{a['RFP_File']}:\n{a.get('raw_text', '')}" for a in all_analyses])
        chunks = retriever.chunk_text(combined_text)
        retriever.build_index(chunks)

        query = st.text_input("Enter your question:")
        if query:
            with st.spinner("Searching and generating answer..."):
                context_chunks = retriever.query(query, top_k=3)
                context = "\n\n".join(context_chunks)
                prompt = f"""
                You are an AI assistant analyzing multiple RFPs.
                Answer the question using ONLY the provided context.

                Context:
                {context}

                Question:
                {query}

                Answer:
                """
                answer = llm_generate(prompt, max_tokens=400)

            st.subheader("🧠 AI Answer")
            st.write(answer)

            with st.expander("📎 Supporting Context"):
                st.write(context_chunks)

    # ===== Tab: Multi-RFP Comparison & UI/UX Enhancements =====
    with tab_compare:
        st.subheader("📊 Multi-RFP Comparison Dashboard")

        # ----- Top Metrics Cards -----
        col1, col2, col3, col4 = st.columns(4)
        total_budget = sum(a.get("Cost_Estimate", {}).get("Amount", 0) for a in all_analyses)
        avg_duration = round(
            sum(a.get("Timeline", {}).get("Total_Duration_Days", 0) for a in all_analyses) / len(all_analyses),
            1
        )
        total_roles = sum(len(a.get("Tasks_Roles", [])) for a in all_analyses)
        total_skills = len(set(skill for a in all_analyses for skill in a.get("Required_Skills", [])))

        col1.metric("💰 Total Budget (INR)", f"{total_budget:,}")
        col2.metric("⏱ Average Duration (Days)", avg_duration)
        col3.metric("👥 Total Roles", total_roles)
        col4.metric("🛠 Total Skills", total_skills)

        # ----- Show Multi-RFP Dashboard (Side-by-Side Charts + Skills/Roles Overlap) -----
        show_multi_rfp_dashboard(all_analyses, uploaded_files)

        # ----- Executive Summary (Collapsible) -----
        with st.expander("📌 Executive Summary"):
            st.markdown("**Project Types Overview:**")
            types = {}
            for a in all_analyses:
                types[a.get("Project_Type", "N/A")] = types.get(a.get("Project_Type", "N/A"), 0) + 1
            st.write(types)

            st.markdown("**Key Skills Across All RFPs:**")
            all_skills = {}
            for a in all_analyses:
                for skill in a.get("Required_Skills", []):
                    all_skills[skill] = all_skills.get(skill, 0) + 1
            st.write(dict(sorted(all_skills.items(), key=lambda x: x[1], reverse=True)))

            st.markdown("**Total Roles Across All RFPs:**")
            role_counts = {}
            for a in all_analyses:
                for role in a.get("Tasks_Roles", []):
                    r = role.get("Role")
                    role_counts[r] = role_counts.get(r, 0) + 1
            st.write(role_counts)

    # ===== Export Multi-RFP Analysis =====
    st.subheader("💾 Export Multi-RFP Analysis")
    save_format = st.radio("Choose export format:", ["JSON", "PDF", "Excel"])
    if st.button("Save All Analyses"):
        if save_format == "JSON":
            save_path = export_json(all_analyses)
        elif save_format == "PDF":
            save_path = export_pdf(all_analyses)
        elif save_format == "Excel":
            save_path = export_excel(all_analyses)
        st.success(f"✅ Saved as {save_path}")

    # ===== Tab: Skill Gap Analysis =====
tab_skills = st.tabs(["Skill Gap Analysis"])[0]  # Single tab

with tab_skills:
    st.subheader("🧩 Skill Gap Analysis Across Uploaded RFPs")

    # Load internal skills
    internal_skills_dict = load_internal_skills()  # should return a list of skills

    def flatten_skills(skills_list):
        """Flatten comma-separated skills into individual skill strings."""
        flat = []
        for s in skills_list:
            flat.extend([x.strip() for x in s.split(",")])
        return flat

    for analysis in all_analyses:
        rfp_file = analysis.get("RFP_File")
        rfp_skills = analysis.get("Required_Skills", [])

        st.markdown(f"### {rfp_file}")

        if rfp_skills:
            gap_result = skill_gap_analysis(rfp_skills, internal_skills_dict)

            # Flatten skills
            covered = flatten_skills(gap_result.get("covered", []))
            missing = flatten_skills(gap_result.get("missing", []))

            # Display Covered Skills
            st.markdown("**✅ Skills Covered by Internal Team:**")
            if covered:
                for skill in covered:
                    st.markdown(f"- {skill}")
            else:
                st.write("None")

            # Display Missing Skills
            st.markdown("**❌ Skills Missing in Internal Team:**")
            if missing:
                for skill in missing:
                    st.markdown(f"- {skill}")
            else:
                st.write("None")

            # ----- Visual Bar Chart -----
            all_skills_list = covered + missing
            status_list = ["Covered"] * len(covered) + ["Missing"] * len(missing)

            if all_skills_list:
                df_gap = pd.DataFrame({
                    "Skill": all_skills_list,
                    "Status": status_list
                })

                chart = alt.Chart(df_gap).mark_bar().encode(
                    x=alt.X('Skill', sort='-y'),
                    y='count()',
                    color='Status',
                    tooltip=['Skill', 'Status']
                ).properties(height=300)

                st.altair_chart(chart, use_container_width=True)

        else:
            st.info("No skills listed in this RFP.")