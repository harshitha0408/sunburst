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

    # Store State information for hover - handle missing State column gracefully
    if "State" in tech_df.columns:
        tech_df["StateInfo"] = tech_df["State"]
    else:
        tech_df["StateInfo"] = "N/A"
    
    if "State" in ai_df.columns:
        ai_df["StateInfo"] = ai_df["State"]
    else:
        ai_df["StateInfo"] = "N/A"

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
        "Level": ["AI Coach"],
        "StateInfo": ["N/A"]  # No state for intermediate nodes
    })

    cohorts = pd.DataFrame({
        "Label": ["Cohort Owner 1"],
        "Parent": ["Program Lead"],
        "TotalRegistrations": [20],  # default value
        "Level": ["Cohort Owner"],
        "StateInfo": ["N/A"]  # No state for intermediate nodes
    })

    program = pd.DataFrame({
        "Label": ["Program Lead"],
        "Parent": [""],
        "TotalRegistrations": [1],  # default value
        "Level": ["Program Lead"],
        "StateInfo": ["N/A"]  # No state for intermediate nodes
    })

    # Add missing "Tech Lead (Unassigned)" node
    unassigned = pd.DataFrame({
        "Label": ["Tech Lead (Unassigned)"],
        "Parent": ["AI Coach 1"],
        "TotalRegistrations": [0],
        "Level": ["Tech Lead"],
        "StateInfo": ["N/A"]  # No state for unassigned
    })

    # Combine all dataframes
    sunburst_df = pd.concat([
        program[["Label", "Parent", "TotalRegistrations", "Level", "StateInfo"]],
        cohorts[["Label", "Parent", "TotalRegistrations", "Level", "StateInfo"]],
        coaches[["Label", "Parent", "TotalRegistrations", "Level", "StateInfo"]],
        tech_df[["Label", "Parent", "TotalRegistrations", "Level", "StateInfo"]],
        ai_df[["Label", "Parent", "TotalRegistrations", "Level", "StateInfo"]],
        unassigned[["Label", "Parent", "TotalRegistrations", "Level", "StateInfo"]],
    ], ignore_index=True)

    # Ensure TotalRegistrations is numeric
    sunburst_df["TotalRegistrations"] = pd.to_numeric(sunburst_df["TotalRegistrations"], errors="coerce").fillna(0)
    
    return sunburst_df

def create_sunburst_chart(sunburst_df):
    # Enhanced hovertemplate with State information
    hover_template = '<b>%{label}</b><br>State: %{customdata[0]}<br>Registrations: %{value}<extra></extra>'

    # Ensure all segments have minimum value to be visible
    sunburst_df_display = sunburst_df.copy()
    sunburst_df_display.loc[sunburst_df_display["TotalRegistrations"] == 0, "TotalRegistrations"] = 0.1

    fig = px.sunburst(
        sunburst_df_display,
        names="Label",
        parents="Parent",
        values="TotalRegistrations",
        color="Level",
        title="AI Program Structure",
        color_discrete_map={
            "Program Lead": "#D32F2F",      # Dark Red
            "Cohort Owner": "#F57C00",      # Dark Orange  
            "AI Coach": "#FBC02D",          # Dark Yellow
            "Tech Lead": "#388E3C",         # Dark Green
            "AI Intern": "#1976D2"          # Dark Blue
        }
    )

    fig.update_traces(
        insidetextorientation='radial',
        hovertemplate=hover_template,
        customdata=sunburst_df[["StateInfo"]].values
    )
    
    # Make the chart responsive and adjust size for Streamlit
    fig.update_layout(
        height=600,
        font_size=12,
        title_x=0.5,
        # Improve visibility for dark themes
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
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
        
        # Add state-wise summary if State data is available
        if "StateInfo" in sunburst_df.columns and not sunburst_df["StateInfo"].eq("N/A").all():
            st.subheader("Registrations by State")
            state_summary = sunburst_df[sunburst_df["StateInfo"] != "N/A"].groupby("StateInfo")["TotalRegistrations"].sum().reset_index()
            state_summary.columns = ["State", "Total Registrations"]
            st.dataframe(state_summary, use_container_width=True)

except FileNotFoundError as e:
    st.error(f"CSV file not found: {e}")
    st.info("Please ensure your CSV files ('aieLeads.csv' and 'TechLeads.csv') are in the same directory as this Streamlit app.")
    
except Exception as e:
    st.error(f"An error occurred: {e}")
    st.info("Please check your CSV file format and ensure it has the required columns: 'CollegeName', 'TotalRegistrations', and 'State'")

# Add instructions in sidebar
with st.sidebar:
    st.header("Instructions")
    st.write("""
    This application displays an interactive sunburst chart of the AI Program structure.
    
    **Required CSV Files:**
    - aieLeads.csv - AI Intern data
    - TechLeads.csv - Tech Lead data
    
    **Required Columns:**
    - CollegeName - Name of the college
    - TotalRegistrations - Number of registrations
    - State - State where the college is located
    
    **Chart Interaction:**
    - Click on segments to drill down
    - Hover for details (shows college name, state, and registrations)
    - Use the data summary below to explore the data
    """)