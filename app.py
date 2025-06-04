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

def filter_data_by_state(sunburst_df, selected_state):
    """Filter the sunburst data for a specific state"""
    if selected_state == "All States":
        return sunburst_df
    
    # Filter only the records that belong to the selected state (Tech Leads and AI Interns)
    state_filtered = sunburst_df[
        (sunburst_df["StateInfo"] == selected_state) | 
        (sunburst_df["StateInfo"] == "N/A")  # Keep intermediate nodes
    ].copy()
    
    # If no data for the selected state, return empty dataframe with structure
    if len(state_filtered[state_filtered["StateInfo"] == selected_state]) == 0:
        return pd.DataFrame(columns=sunburst_df.columns)
    
    # Get the colleges in the selected state
    state_colleges = sunburst_df[sunburst_df["StateInfo"] == selected_state]["Label"].tolist()
    
    # Filter to include only relevant Tech Leads and AI Interns
    # Keep intermediate nodes and only the colleges from selected state
    filtered_df = sunburst_df[
        (sunburst_df["Level"].isin(["Program Lead", "Cohort Owner", "AI Coach"])) |  # Keep all intermediate nodes
        (sunburst_df["StateInfo"] == selected_state) |  # Keep state-specific nodes
        ((sunburst_df["Level"] == "Tech Lead") & (sunburst_df["StateInfo"] == "N/A") & (sunburst_df["Label"] == "Tech Lead (Unassigned)"))  # Keep unassigned if needed
    ].copy()
    
    # Remove unassigned tech lead if no AI interns are unassigned in this state
    unassigned_interns = sunburst_df[
        (sunburst_df["Level"] == "AI Intern") & 
        (sunburst_df["Parent"] == "Tech Lead (Unassigned)") & 
        (sunburst_df["StateInfo"] == selected_state)
    ]
    
    if len(unassigned_interns) == 0:
        filtered_df = filtered_df[filtered_df["Label"] != "Tech Lead (Unassigned)"]
    
    return filtered_df

def create_sunburst_chart(sunburst_df, selected_state="All States"):
    """Create sunburst chart with optional state filtering"""
    if sunburst_df.empty:
        # Create empty chart with message
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_annotation(
            text=f"No data available for {selected_state}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(
            height=600,
            title=f"AI Program Structure - {selected_state}",
            title_x=0.5
        )
        return fig
    
    # Enhanced hovertemplate with State information
    hover_template = '<b>%{label}</b><br>State: %{customdata[0]}<br>Registrations: %{value}<extra></extra>'

    # Ensure all segments have minimum value to be visible
    sunburst_df_display = sunburst_df.copy()
    sunburst_df_display.loc[sunburst_df_display["TotalRegistrations"] == 0, "TotalRegistrations"] = 0.1

    chart_title = f"AI Program Structure - {selected_state}" if selected_state != "All States" else "AI Program Structure - All States"
    
    fig = px.sunburst(
        sunburst_df_display,
        names="Label",
        parents="Parent",
        values="TotalRegistrations",
        color="Level",
        title=chart_title,
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
    
    # Get unique states for dropdown (excluding N/A and intermediate nodes)
    available_states = sorted(sunburst_df[
        (sunburst_df["StateInfo"] != "N/A") & 
        (sunburst_df["StateInfo"].notna())
    ]["StateInfo"].unique())
    
    # Add state filter dropdown
    st.subheader("Filter by State")
    state_options = ["All States"] + available_states
    selected_state = st.selectbox(
        "Select a state to view its program structure:",
        options=state_options,
        index=0,  # Default to "All States"
        help="Choose a specific state to see only the colleges and participants from that state"
    )
    
    # Filter data based on selected state
    if selected_state == "All States":
        filtered_df = sunburst_df
    else:
        filtered_df = filter_data_by_state(sunburst_df, selected_state)
    
    # Display summary statistics for selected state
    if selected_state != "All States":
        state_data = sunburst_df[sunburst_df["StateInfo"] == selected_state]
        if not state_data.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                total_colleges = len(state_data[state_data["Level"].isin(["Tech Lead", "AI Intern"])]["Label"].str.replace(" \(.*\)", "", regex=True).unique())
                st.metric("Colleges in State", total_colleges)
            with col2:
                total_registrations = state_data["TotalRegistrations"].sum()
                st.metric("Total Registrations", int(total_registrations))
            with col3:
                tech_leads = len(state_data[state_data["Level"] == "Tech Lead"])
                ai_interns = len(state_data[state_data["Level"] == "AI Intern"])
                st.metric("Tech Leads / AI Interns", f"{tech_leads} / {ai_interns}")
    
    # Create and display the chart
    fig = create_sunburst_chart(filtered_df, selected_state)
    st.plotly_chart(fig, use_container_width=True)
    
    # Optional: Show data summary
    with st.expander("View Data Summary"):
        if not filtered_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"Total Registrations by Level - {selected_state}")
                summary = filtered_df.groupby("Level")["TotalRegistrations"].sum().reset_index()
                st.dataframe(summary, use_container_width=True)
            
            with col2:
                st.subheader("Data Preview")
                display_df = filtered_df[filtered_df["Level"].isin(["Tech Lead", "AI Intern"])].head(10)
                st.dataframe(display_df, use_container_width=True)
            
            # Show state-specific data
            if selected_state != "All States":
                st.subheader(f"Colleges in {selected_state}")
                state_colleges = filtered_df[
                    (filtered_df["StateInfo"] == selected_state) & 
                    (filtered_df["Level"].isin(["Tech Lead", "AI Intern"]))
                ][["Label", "Level", "TotalRegistrations"]]
                st.dataframe(state_colleges, use_container_width=True)
        else:
            st.info(f"No data available for {selected_state}")

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
    
    **New Feature: State Filter**
    - Use the dropdown above the chart to filter by state
    - Select "All States" to view the complete program structure
    - Select a specific state to view only colleges from that state
    
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
    - Filter by state to focus on specific regions
    """)
    
    # Display available states
    if 'available_states' in locals():
        st.subheader("Available States")
        for state in available_states:
            st.write(f"• {state}")