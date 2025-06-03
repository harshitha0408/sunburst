import streamlit as st
import pandas as pd
import plotly.express as px

# Set page configuration
st.set_page_config(page_title="AI Program Structure", layout="wide")

# Title
st.title("AI Program Structure - Interactive Sunburst Chart")

@st.cache_data
def load_and_process_data():
    # Load your CSV files - update these paths to match your server file locations
    ai_df = pd.read_csv("aieLeads.csv")  # Make sure this file is in your Streamlit app directory
    tech_df = pd.read_csv('TechLeads.csv')  # Make sure this file is in your Streamlit app directory
    
    # Tag each level
    ai_df["Level"] = "AI Intern"
    tech_df["Level"] = "Tech Lead"

    # Prepare labels without trailing spaces for consistency
    tech_df["Label"] = tech_df["CollegeName"] + " (Tech Lead)"
    ai_df["Label"] = ai_df["CollegeName"] + " (Intern)"

    # Assign Parent for tech leads (children of AI Coach 1)
    tech_df["Parent"] = "AI Coach 1"

    # Map AI Intern's Parent to Tech Lead's Label exactly
    ai_df["Parent"] = ai_df["CollegeName"].map(dict(zip(tech_df["CollegeName"], tech_df["Label"])))

    # Handle unmatched AI Interns by assigning them to a default "Tech Lead (Unassigned)"
    ai_df["Parent"].fillna("Tech Lead (Unassigned)", inplace=True)

    # Create intermediate nodes with default TotalRegistrations
    coaches = pd.DataFrame({
        "Label": ["AI Coach 1"],
        "Parent": ["Cohort Owner 1"],
        "TotalRegistrations": [200],  # default value
        "Level": ["AI Coach"]
    })

    cohorts = pd.DataFrame({
        "Label": ["Cohort Owner 1"],
        "Parent": ["Program Lead"],
        "TotalRegistrations": [20],  # default value
        "Level": ["Cohort Owner"]
    })

    program = pd.DataFrame({
        "Label": ["Program Lead"],
        "Parent": [""],
        "TotalRegistrations": [1],  # default value
        "Level": ["Program Lead"]
    })

    # Add missing "Tech Lead (Unassigned)" node
    unassigned = pd.DataFrame({
        "Label": ["Tech Lead (Unassigned)"],
        "Parent": ["AI Coach 1"],
        "TotalRegistrations": [0],
        "Level": ["Tech Lead"]
    })

    # Combine all dataframes
    sunburst_df = pd.concat([
        program[["Label", "Parent", "TotalRegistrations", "Level"]],
        cohorts[["Label", "Parent", "TotalRegistrations", "Level"]],
        coaches[["Label", "Parent", "TotalRegistrations", "Level"]],
        tech_df[["Label", "Parent", "TotalRegistrations", "Level"]],
        ai_df[["Label", "Parent", "TotalRegistrations", "Level"]],
        unassigned[["Label", "Parent", "TotalRegistrations", "Level"]],
    ], ignore_index=True)

    # Ensure TotalRegistrations is numeric
    sunburst_df["TotalRegistrations"] = pd.to_numeric(sunburst_df["TotalRegistrations"], errors="coerce").fillna(0)
    
    return sunburst_df

def create_sunburst_chart(sunburst_df):
    # Hovertemplate: just name and number on separate lines
    hover_template = '<b>%{label}</b><br>%{value}<extra></extra>'

    fig = px.sunburst(
        sunburst_df,
        names="Label",
        parents="Parent",
        values="TotalRegistrations",
        color="Level",
        title="AI Program Structure",
        color_discrete_map={
            "Program Lead": "#FF5722",
            "Cohort Owner": "#FF9800",
            "AI Coach": "#FFEB3B",
            "Tech Lead": "#8BC34A",
            "AI Intern": "#4CAF50"
        }
    )

    fig.update_traces(
        insidetextorientation='radial',
        hovertemplate=hover_template
    )
    
    # Make the chart responsive and adjust size for Streamlit
    fig.update_layout(
        height=600,
        font_size=12,
        title_x=0.5
    )
    
    return fig

# Main app
try:
    # Load and process data
    sunburst_df = load_and_process_data()
    
    # Create and display the chart
    fig = create_sunburst_chart(sunburst_df)
    st.plotly_chart(fig, use_container_width=True)
    
    # Optional: Show data summary
    with st.expander("View Data Summary"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Total Registrations by Level")
            summary = sunburst_df.groupby("Level")["TotalRegistrations"].sum().reset_index()
            st.dataframe(summary, use_container_width=True)
        
        with col2:
            st.subheader("Data Preview")
            st.dataframe(sunburst_df.head(10), use_container_width=True)

except FileNotFoundError as e:
    st.error(f"CSV file not found: {e}")
    st.info("Please ensure your CSV files ('ai_leads.csv' and 'tech_leads.csv') are in the same directory as this Streamlit app.")
    
except Exception as e:
    st.error(f"An error occurred: {e}")
    st.info("Please check your CSV file format and ensure it has the required columns: 'CollegeName' and 'TotalRegistrations'")

# Add instructions in sidebar
with st.sidebar:
    st.header("Instructions")
    st.write("""
    This application displays an interactive sunburst chart of the AI Program structure.
    
    **Required CSV Files:**
    - `ai_leads.csv` - AI Intern data
    - `tech_leads.csv` - Tech Lead data
    
    **Required Columns:**
    - `CollegeName` - Name of the college
    - `TotalRegistrations` - Number of registrations
    
    **Chart Interaction:**
    - Click on segments to drill down
    - Hover for details
    - Use the data summary below to explore the data
    """)