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
    ai_df = pd.read_csv("C:\\Users\\HP\\Desktop\\INTERN@SWECHA\\aieLeads.csv")  # Make sure this file is in your Streamlit app directory
    tech_df = pd.read_csv("C:\\Users\\HP\\Desktop\\INTERN@SWECHA\\TechLeads.csv")  # Make sure this file is in your Streamlit app directory
    
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
    
    return sunburst_df, ai_df, tech_df

def get_top_colleges_by_registrations(ai_df, tech_df, selected_state=None, min_registrations=100):
    """Get colleges with registrations >= min_registrations, optionally filtered by state"""
    # Combine data from both dataframes and sum registrations by college
    all_colleges = []
    
    # Add tech leads
    for _, row in tech_df.iterrows():
        college_data = {
            'CollegeName': row['CollegeName'],
            'TotalRegistrations': row['TotalRegistrations'],
            'StateInfo': row.get('StateInfo', 'N/A')
        }
        all_colleges.append(college_data)
    
    # Add AI interns
    for _, row in ai_df.iterrows():
        college_data = {
            'CollegeName': row['CollegeName'],
            'TotalRegistrations': row['TotalRegistrations'],
            'StateInfo': row.get('StateInfo', 'N/A')
        }
        all_colleges.append(college_data)
    
    colleges_df = pd.DataFrame(all_colleges)
    
    # Filter by state if specified
    if selected_state and selected_state != "All States":
        colleges_df = colleges_df[colleges_df['StateInfo'] == selected_state]
    
    # Group by college name and sum registrations
    college_totals = colleges_df.groupby(['CollegeName', 'StateInfo'])['TotalRegistrations'].sum().reset_index()
    
    # Filter colleges with registrations >= minimum threshold
    filtered_colleges = college_totals[college_totals['TotalRegistrations'] >= min_registrations]
    
    # Sort by total registrations (descending)
    top_colleges = filtered_colleges.sort_values('TotalRegistrations', ascending=False)
    
    return top_colleges

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

def create_sunburst_chart(sunburst_df, selected_state="All States", selected_college=None):
    """Create sunburst chart with optional state filtering and college highlighting"""
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
    
    # Enhanced hovertemplate with State information and college highlighting
    hover_template = '<b>%{label}</b><br>State: %{customdata[0]}<br>Registrations: %{value}<extra></extra>'

    # Ensure all segments have minimum value to be visible
    sunburst_df_display = sunburst_df.copy()
    sunburst_df_display.loc[sunburst_df_display["TotalRegistrations"] == 0, "TotalRegistrations"] = 0.1

    # Create color mapping with highlighting for selected college
    if selected_college:
        # Create a custom color column for highlighting
        sunburst_df_display['ColorCategory'] = sunburst_df_display['Level'].copy()
        
        # Highlight selected college entries
        selected_mask = sunburst_df_display["Label"].str.contains(selected_college, na=False, regex=False)
        sunburst_df_display.loc[selected_mask, 'ColorCategory'] = 'Selected College'
        
        color_map = {
            "Program Lead": "#D32F2F",      # Dark Red
            "Cohort Owner": "#F57C00",      # Dark Orange  
            "AI Coach": "#FBC02D",          # Dark Yellow
            "Tech Lead": "#388E3C",         # Dark Green
            "AI Intern": "#1976D2",         # Dark Blue
            "Selected College": "#FF6B35"   # Bright Orange for highlighting
        }
        color_column = 'ColorCategory'
        chart_title = f"AI Program Structure - {selected_state} (Highlighting: {selected_college})" if selected_state != "All States" else f"AI Program Structure - All States (Highlighting: {selected_college})"
    else:
        color_map = {
            "Program Lead": "#D32F2F",      # Dark Red
            "Cohort Owner": "#F57C00",      # Dark Orange  
            "AI Coach": "#FBC02D",          # Dark Yellow
            "Tech Lead": "#388E3C",         # Dark Green
            "AI Intern": "#1976D2"          # Dark Blue
        }
        color_column = 'Level'
        chart_title = f"AI Program Structure - {selected_state}" if selected_state != "All States" else "AI Program Structure - All States"
    
    fig = px.sunburst(
        sunburst_df_display,
        names="Label",
        parents="Parent",
        values="TotalRegistrations",
        color=color_column,
        title=chart_title,
        color_discrete_map=color_map
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
        # Improve visibility - remove dark theme overrides
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(color='black')
    )
    
    return fig

# Main app
try:
    # Load and process data
    sunburst_df, ai_df, tech_df = load_and_process_data()
    
    # Get unique states for dropdown (excluding N/A and intermediate nodes)
    available_states = sorted(sunburst_df[
        (sunburst_df["StateInfo"] != "N/A") & 
        (sunburst_df["StateInfo"].notna())
    ]["StateInfo"].unique())
    
    # Create three columns for filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Filter by State")
        state_options = ["All States"] + available_states
        selected_state = st.selectbox(
            "Select a state to view its program structure:",
            options=state_options,
            index=0,  # Default to "All States"
            help="Choose a specific state to see only the colleges and participants from that state"
        )
    
    with col2:
        st.subheader("Filter by Registration Count")
        registration_threshold = st.selectbox(
            "Select minimum registrations:",
            options=[50, 100],
            index=1,  # Default to 100
            help="Choose minimum registration count to filter colleges"
        )
    
    with col3:
        st.subheader("Top Colleges by Registrations")
        # Get top colleges based on selected state and registration threshold
        top_colleges = get_top_colleges_by_registrations(ai_df, tech_df, selected_state, min_registrations=registration_threshold)
        
        if not top_colleges.empty:
            # Create display options for dropdown
            college_options = ["All Colleges"] + [
                f"{row['CollegeName']} ({row['StateInfo']}) - {int(row['TotalRegistrations'])} registrations"
                for _, row in top_colleges.iterrows()
            ]
            
            selected_college_option = st.selectbox(
                f"Select from colleges with {registration_threshold}+ registrations ({len(top_colleges)} found):",
                options=college_options,
                index=0,
                help=f"Shows only colleges with {registration_threshold} or more total registrations"
            )
            
            # Extract college name if a specific college is selected
            selected_college = None
            if selected_college_option != "All Colleges":
                selected_college = selected_college_option.split(" (")[0]
        else:
            selected_college = None
            st.info(f"No colleges found for {selected_state}")
    
    # Filter data based on selected state
    if selected_state == "All States":
        filtered_df = sunburst_df
    else:
        filtered_df = filter_data_by_state(sunburst_df, selected_state)
    
    # Store selected college for highlighting but don't filter the dataframe
    # We'll handle college selection in the chart creation function
    
    # Display summary statistics
    if selected_state != "All States" or selected_college:
        state_data = sunburst_df[sunburst_df["StateInfo"] == selected_state] if selected_state != "All States" else sunburst_df
        
        if selected_college:
            college_data = state_data[state_data["Label"].str.contains(selected_college, na=False, regex=False)]
            display_title = f"Statistics for {selected_college}"
        else:
            college_data = state_data
            display_title = f"Statistics for {selected_state}"
        
        if not college_data.empty:
            st.subheader(display_title)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if selected_college:
                    total_registrations = college_data["TotalRegistrations"].sum()
                    st.metric("Total Registrations", int(total_registrations))
                else:
                    total_colleges = len(state_data[state_data["Level"].isin(["Tech Lead", "AI Intern"])]["Label"].str.replace(" \(.*\)", "", regex=True).unique())
                    st.metric("Colleges in State", total_colleges)
            
            with col2:
                if selected_college:
                    tech_leads = len(college_data[college_data["Level"] == "Tech Lead"])
                    ai_interns = len(college_data[college_data["Level"] == "AI Intern"])
                    st.metric("Tech Leads / AI Interns", f"{tech_leads} / {ai_interns}")
                else:
                    total_registrations = state_data["TotalRegistrations"].sum()
                    st.metric("Total Registrations", int(total_registrations))
            
            with col3:
                if not selected_college:
                    tech_leads = len(state_data[state_data["Level"] == "Tech Lead"])
                    ai_interns = len(state_data[state_data["Level"] == "AI Intern"])
                    st.metric("Tech Leads / AI Interns", f"{tech_leads} / {ai_interns}")
    
    # Create and display the chart
    fig = create_sunburst_chart(filtered_df, selected_state, selected_college)
    st.plotly_chart(fig, use_container_width=True)
    
    # Display top colleges table with improved styling
    if not top_colleges.empty:
        with st.expander(f"View {len(top_colleges)} Colleges with {registration_threshold}+ Registrations ({selected_state})"):
            # Format the dataframe for better display
            display_top_colleges = top_colleges.copy()
            display_top_colleges['Rank'] = range(1, len(display_top_colleges) + 1)
            display_top_colleges = display_top_colleges[['Rank', 'CollegeName', 'StateInfo', 'TotalRegistrations']]
            display_top_colleges.columns = ['Rank', 'College Name', 'State', 'Total Registrations']
            
            # Improved color coding with better contrast
            def highlight_registrations(row):
                if row['Total Registrations'] >= 100:
                    return ['background-color: #c8e6c9; color: #1b5e20'] * len(row)  # Green background with dark green text
                elif row['Total Registrations'] >= 50:
                    return ['background-color: #fff9c4; color: #f57f17'] * len(row)  # Light yellow background with dark yellow text
                else:
                    return ['background-color: #ffcdd2; color: #c62828'] * len(row)  # Light red background with dark red text
            
            # Apply styling and display table
            styled_df = display_top_colleges.style.apply(highlight_registrations, axis=1)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Add legend with better formatting
            st.markdown("""
            **Color Legend:**
            - 🟢 **Green**: 100+ registrations
            - 🟡 **Yellow**: 50-99 registrations
            - 🔴 **Red**: Less than 50 registrations
            """)
            
            # Add download button for the filtered data
            csv_data = display_top_colleges.to_csv(index=False)
            st.download_button(
                label="Download Table as CSV",
                data=csv_data,
                file_name=f"top_colleges_{selected_state}_{registration_threshold}plus.csv",
                mime="text/csv"
            )
    
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
            st.info(f"No data available for the selected filters")

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
    
    **New Features:**
    - **State Filter**: Filter by state to view regional data
    - **Registration Threshold**: Choose between 50+ or 100+ registrations
    - **College Selection**: Select specific colleges meeting the threshold
    - **Combined Filtering**: Use all three filters together for focused analysis
    - **Improved Visibility**: Better color contrast for all elements
    
    **How to Use:**
    1. Select a state from the first dropdown (or keep "All States")
    2. Choose registration threshold: 50+ or 100+ registrations
    3. Select a specific college from the qualifying colleges
    4. View the sunburst chart with highlighting and detailed statistics
    5. Explore the color-coded colleges table
    6. Download filtered data as CSV
    
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
    - Use the data summary sections to explore the data
    - Filter by state and registration threshold for targeted analysis
    - Color-coded table helps distinguish between different registration levels
    """)
    
    # Display available states
    if 'available_states' in locals():
        st.subheader("Available States")
        for state in available_states:
            st.write(f"• {state}")