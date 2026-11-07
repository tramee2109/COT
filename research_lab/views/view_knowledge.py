"""
COT DATA RESEARCH LAB — Module 7: Applications & Knowledge Base
"""

import streamlit as st
from research_lab.knowledge_base import KNOWLEDGE_TOPICS

def render_knowledge_base():
    st.title("📚 Applications & Institutional Knowledge Base")
    st.caption("Comprehensive Handbook of Quantitative Commodity Positioning Research Methodologies")

    topic_titles = [t["title"] for t in KNOWLEDGE_TOPICS]
    sel_title = st.selectbox("Select Research Methodology Topic:", topic_titles)

    topic = next((t for t in KNOWLEDGE_TOPICS if t["title"] == sel_title), KNOWLEDGE_TOPICS[0])

    st.markdown(f"### {topic['title']}")
    st.info(f"**Concept:** {topic['concept']}")

    col_rat, col_fld = st.columns(2)
    with col_rat:
        st.markdown(f"""
        **💡 Economic Rationale:**
        {topic['rationale']}
        """)
    with col_fld:
        st.markdown(f"""
        **📋 Relevant Fields & Metrics:**
        `{topic['fields']}`
        """)

    st.markdown(f"""
    **🔬 Rigorous Research Methodology:**
    {topic['methodology']}
    """)

    col_str, col_lim = st.columns(2)
    with col_str:
        st.markdown(f"""
        **✅ Analytical Strengths:**
        {topic['strengths']}
        """)
    with col_lim:
        st.markdown(f"""
        **⚠️ Known Limitations:**
        {topic['limitations']}
        """)

    st.error(f"**🚫 Common Interpretation Mistakes / Pitfalls:**\n\n{topic['pitfalls']}")

    st.markdown("---")
    st.subheader("Handbook Table of Contents")
    for i, t in enumerate(KNOWLEDGE_TOPICS):
        st.markdown(f"{i+1}. **{t['title'].split('. ')[-1]}** — *{t['concept'][:110]}...*")

