import streamlit as st
import pandas as pd
import json
from scheduler import Scheduler

st.set_page_config(page_title="Exam Scheduler")
st.title("Exam Scheduler")

if st.button("Run Scheduler"):
    solver = Scheduler()
    with st.spinner("Processing..."):
        solver.load_data()
        all_classes = list(solver.classes.keys())
        final_schedule = solver.schedule_backtrack({}, all_classes)

    if final_schedule:
        st.success("Schedule Found")
        
        display_data = []
        structured_json = {}

        for i, (course_code, details) in enumerate(final_schedule.items(), 1):
            group_id = f"group_{i:04d}"
            
            start_str = details['window'][0].isoformat()
            end_str = details['window'][1].isoformat()
            time_slot = f"{start_str} - {end_str}"
            
            students = [f"{solver.EX}_{name}" for name in solver.course_to_students.get(course_code, [])]
            
            structured_json[group_id] = {
                "students": students,
                "room": {
                    "room_iri": f"{solver.EX}{details['room']}",
                    "time_slot": time_slot
                },
                "class_iri": f"{solver.EX}{course_code}"
            }

            display_data.append({
                "Group": group_id,
                "Course": course_code,
                "Room": details['room'],
                "Time": time_slot
            })

        st.table(pd.DataFrame(display_data))

        json_string = json.dumps(structured_json, indent=4)
        st.download_button(
            label="Download Structured JSON",
            data=json_string,
            file_name="exam_schedule.json",
            mime="application/json"
        )
    else:
        st.error("No valid schedule possible.")