## Semantic Graph Based Scheduling

`python scheduler.py` or `python3 scheduler.py` depending on your version of Python

outputs `schedule.json` upon running.

`pip install streamlit` to install dependencies

`streamlit run app.py` to run the GUI

This program uses a recursive backtracking algorithm to schedule the exams. It works by narrowing down candidates by conflict until a fully valid assignment can be made.

Our potential conflicts are: 
- There can be no one student who has two exams scheduled simultaneously
- Two Exams cannot take place in the same room at the same time

### The scheduling algorithm:

``` python
def schedule_backtrack(self, assignment, classes_to_schedule):
        if not classes_to_schedule:
            return assignment
        current_class = classes_to_schedule[0]
        remaining_classes = classes_to_schedule[1:]
        for option in self.get_options(current_class):
            if self.is_consistent(current_class, option, assignment):
                assignment[current_class] = option
                result = self.schedule_backtrack(assignment, remaining_classes)
                if result is not None:
                    return result
                del assignment[current_class]
        return None
```
____________________________________
### screenshot of web app:
<img width="1914" height="1005" alt="student_schedule" src="https://github.com/user-attachments/assets/088755c0-dded-40f2-a4c3-1bcb391ef5d5" />

** Disclaimer: **

The frontend of this wep app was written using AI, the backend (parsing, scheduling, etc.) was written by us. We may choose to increment upon this project in the future but we wanted to have something nice for our upcoming presentation.




