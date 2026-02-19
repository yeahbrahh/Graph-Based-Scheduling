import streamlit as st
import pandas as pd
import plotly.express as px
import json  # Added for JSON export
from scheduler import Scheduler 

st.set_page_config(page_title="Exam Scheduler", layout="wide")

# Updated CSS
st.markdown("""
    <style>
    .main { background-color: #000000; color: #ffffff; }
    div[data-testid="stSidebar"] { background-color: #111111; border-right: 2px solid #333333; }
    
    .js-plotly-plot .yaxislayer-above .ytick text {
        font-size: 18px !important;
        fill: #ffffff !important;
        font-weight: bold !important;
    }
    
    label, .stRadio, .stSelectbox { font-size: 1.1rem !important; }
    </style>
    """, unsafe_allow_html=True)

if "solver" not in st.session_state:
    st.session_state.solver = None
if "final_schedule" not in st.session_state:
    st.session_state.final_schedule = None

def get_master_df(schedule, solver):
    rows = []
    for course_code, details in schedule.items():
        start_dt = details['window'][0]
        end_dt = details['window'][1]
        
        rows.append({
            "Course": course_code,
            "Start": start_dt, "End": end_dt,
            "Day": start_dt.strftime("%A, %b %d"),
            "SortDate": start_dt.date(),
            "Room": str(details['room']),
            "Label": f"{course_code} ({details['room']})",
            "Students": list(solver.course_to_students.get(course_code, []))
        })
    return pd.DataFrame(rows).sort_values(by=["Start", "Room"])

# --- Helper Function for JSON Export ---
def convert_schedule_to_json(schedule):
    """Converts datetime objects to strings for JSON serialization."""
    export_data = {}
    for course, details in schedule.items():
        export_data[course] = {
            "room": details['room'],
            "start": details['window'][0].isoformat(),
            "end": details['window'][1].isoformat()
        }
    return json.dumps(export_data, indent=4)

st.title("Exam Schedule")

if st.button("Generate Schedule"):
    solver = Scheduler()
    solver.load_data()
    all_classes = list(solver.classes.keys())
    st.session_state.final_schedule = solver.schedule_backtrack({}, all_classes)
    st.session_state.solver = solver

if st.session_state.final_schedule:
    df_master = get_master_df(st.session_state.final_schedule, st.session_state.solver)
    
    # --- Sidebar Controls ---
    st.sidebar.header("Options")
    
    # JSON Download Button
    json_string = convert_schedule_to_json(st.session_state.final_schedule)
    st.sidebar.download_button(
        label="📥 Download Schedule (JSON)",
        data=json_string,
        file_name="exam_schedule.json",
        mime="application/json"
    )
    
    st.sidebar.markdown("---")
    
    view_mode = st.sidebar.radio("View Perspective:", ["Room", "Course", "Student"])

    if view_mode == "Room":
        sel_room = st.sidebar.selectbox("Select Room", sorted(df_master["Room"].unique()))
        room_df = df_master[df_master["Room"] == sel_room]
        sel_day = st.sidebar.selectbox("Select Day", sorted(room_df["Day"].unique()))
        plot_df = room_df[room_df["Day"] == sel_day].copy()
        y_val, facet = "Room", None
    elif view_mode == "Course":
        sel_course = st.sidebar.selectbox("Select Course", sorted(df_master["Course"].unique()))
        plot_df = df_master[df_master["Course"] == sel_course].copy()
        y_val, facet = "Course", "Day"
    else:
        sel_student = st.sidebar.selectbox("Search Student Profile", sorted(list(st.session_state.solver.student_courses.keys())))
        plot_df = df_master[df_master["Students"].apply(lambda x: sel_student in x)].copy()
        y_val, facet = "Course", "Day"

    # --- Plotting Logic ---
    if not plot_df.empty:
        fig = px.timeline(
            plot_df, 
            x_start="Start", x_end="End", y=y_val, 
            color="Course", text="Label",
            facet_col=facet,
            color_discrete_sequence=px.colors.qualitative.Alphabet 
        )

        fig.update_xaxes(matches=None)
        fig.update_traces(
            textposition='inside',
            insidetextanchor='middle',
            marker_line_color='#ffffff',
            marker_line_width=2,
            textfont=dict(size=18, color="white", family="Arial Black")
        )

        fig.update_layout(
            height=500,
            plot_bgcolor="#F7F0F0", 
            paper_bgcolor="#1E4D2B",
            margin=dict(l=150, r=20, t=80, b=100),
            showlegend=False,
            font=dict(color="white")
        )

        fig.update_xaxes(
            tickformat="%I:%M %p", 
            dtick=1800000, 
            tickangle=45,
            gridcolor='#333333',
            tickfont=dict(color="white", size=14)
        )

        fig.update_yaxes(
            type='category', 
            gridcolor='#333333', 
            autorange="reversed",
            tickfont=dict(color="white", size=18)
        )

        if facet:
            fig.for_each_annotation(lambda a: a.update(
                text=f"<b>{a.text.split('=')[-1]}</b>", 
                font=dict(size=20, color="white")
            ))

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data found for this selection.")