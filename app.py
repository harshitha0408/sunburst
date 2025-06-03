import streamlit as st
import pandas as pd
import plotly.express as px

# Set page configuration
st.set_page_config(
    page_title="AI Program Structure",
    page_icon="🌟",
    layout="wide"
)

# Title and description
st.title("🌟 AI Program Structure - Interactive Sunburst Chart")
st.markdown("Upload your CSV files to visualize the hierarchical structure of your AI program.")

# File upload section
st.sidebar.header("Upload CSV Files")
ai_file = st.sidebar.file_uploader("Upload AI Intern CSV", type=['csv'])
tech_file = st.sidebar.file_uploader("Upload Tech Lead CSV", type=['csv'])

# Function to create sunburst chart
def create_sunburst_chart(ai_df, tech_df):
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

# Function to display the chart
def display_chart(sunburst_df):
    # Hovertemplate: just name and number on separate lines
    hover_template = '<b>%{label}</b><br>%{value}<extra></extra>'

    fig = px.sunburst(
        sunburst_df,
        names="Label",
        parents="Parent",
        values="TotalRegistrations",
        color="Level",
        title="AI Program Structure - Interactive Sunburst Chart",
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
    
    # Update layout for better display in Streamlit
    fig.update_layout(
        height=700,
        margin=dict(t=50, l=50, r=50, b=50)
    )

    return fig

# Main app logic
if ai_file is not None and tech_file is not None:
    try:
        # Load the CSV files
        ai_df = pd.read_csv(ai_file)
        tech_df = pd.read_csv(tech_file)
        
        # Display basic info about the uploaded files
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("AI Intern Data")
            st.write(f"Rows: {len(ai_df)}")
            st.write("Columns:", list(ai_df.columns))
            with st.expander("Preview AI Intern Data"):
                st.dataframe(ai_df.head())
        
        with col2:
            st.subheader("Tech Lead Data")
            st.write(f"Rows: {len(tech_df)}")
            st.write("Columns:", list(tech_df.columns))
            with st.expander("Preview Tech Lead Data"):
                st.dataframe(tech_df.head())
        
        # Check if required columns exist
        required_columns = ['CollegeName', 'TotalRegistrations']
        ai_missing = [col for col in required_columns if col not in ai_df.columns]
        tech_missing = [col for col in required_columns if col not in tech_df.columns]
        
        if ai_missing or tech_missing:
            st.error("Missing required columns:")
            if ai_missing:
                st.error(f"AI Intern CSV missing: {ai_missing}")
            if tech_missing:
                st.error(f"Tech Lead CSV missing: {tech_missing}")
            st.info("Required columns: CollegeName, TotalRegistrations")
        else:
            # Create and display the sunburst chart
            sunburst_df = create_sunburst_chart(ai_df.copy(), tech_df.copy())
            fig = display_chart(sunburst_df)
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
            
            # Display summary statistics
            st.subheader("📊 Summary Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total AI Interns", len(ai_df))
            
            with col2:
                st.metric("Total Tech Leads", len(tech_df))
            
            with col3:
                total_ai_registrations = ai_df['TotalRegistrations'].sum()
                st.metric("AI Intern Registrations", total_ai_registrations)
            
            with col4:
                total_tech_registrations = tech_df['TotalRegistrations'].sum()
                st.metric("Tech Lead Registrations", total_tech_registrations)
            
            # Show the processed data
            with st.expander("View Processed Sunburst Data"):
                st.dataframe(sunburst_df)
                
                # Download processed data
                csv = sunburst_df.to_csv(index=False)
                st.download_button(
                    label="Download Processed Data as CSV",
                    data=csv,
                    file_name='sunburst_data.csv',
                    mime='text/csv'
                )
    
    except Exception as e:
        st.error(f"Error processing files: {str(e)}")
        st.info("Please make sure your CSV files have the correct format and required columns.")

else:
    # Show instructions when no files are uploaded
    st.info("👆 Please upload both CSV files using the sidebar to get started.")
    
    st.subheader("📋 File Requirements")
    st.markdown("""
    Both CSV files should contain at least the following columns:
    - **CollegeName**: Name of the college/institution
    - **TotalRegistrations**: Number of registrations (numeric)
    
    ### Expected File Structure:
    
    **AI Intern CSV:**
    ```
    CollegeName,TotalRegistrations
    College A,25
    College B,30
    ...
    ```
    
    **Tech Lead CSV:**
    ```
    CollegeName,TotalRegistrations
    College A,5
    College B,8
    ...
    ```
    """)
    
    # Sample data for demonstration
    if st.button("🎯 Show Demo with Sample Data"):
        # Create sample data
        sample_ai = pd.DataFrame({
            'CollegeName': ['College A', 'College B', 'College C', 'College D'],
            'TotalRegistrations': [25, 30, 20, 15]
        })
        
        sample_tech = pd.DataFrame({
            'CollegeName': ['College A', 'College B', 'College C'],
            'TotalRegistrations': [5, 8, 6]
        })
        
        # Create and display demo chart
        sunburst_df = create_sunburst_chart(sample_ai.copy(), sample_tech.copy())
        fig = display_chart(sunburst_df)
        
        st.subheader("🎯 Demo Chart")
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit and Plotly")