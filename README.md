# Final Exam Scheduler

A Python program that automatically schedules university final exams while avoiding conflicts and respecting room capacities.

## What This Does

This program takes student enrollment data, class information, and room availability, then figures out when and where to hold each final exam so that:
- No student has two exams at the same time
- Rooms don't get double-booked
- We don't cram too many students into small rooms
- Everyone gets to take all their finals

## Files

**Main Scripts:**
- `run_all.py` - Runs everything in one command (use this!)
- `scheduler.py` - Creates the exam schedule
- `verify.py` - Double-checks that the schedule is valid
- `visualize.py` - Makes charts showing the schedule

**Data Files:**
- `students.ttl` - List of students and what classes they're taking
- `classes.ttl` - List of classes and how long their exams are
- `rooms.ttl` - List of rooms and when they're available

**Output Files:**
- `schedule.json` - The final exam schedule (gets created when you run it)
- `exam_schedule_visualization.png` - Timeline chart (gets created)
- `schedule_simple.html` - Easy-to-read HTML version (gets created)

## How to Run

### Install Required Packages
```bash
pip install -r requirements.txt
```

### Run Everything (Easiest Way)
```bash
python run_all.py
```

That's it! This will:
1. Generate the schedule
2. Verify it's correct
3. Create visualizations

### Or Run Step-by-Step
```bash
python scheduler.py                  # Creates schedule.json
python verify.py schedule.json       # Checks if it's valid
python visualize.py                  # Makes charts
```

## How It Works

The algorithm is pretty straightforward:

1. **Load the data** - Read all the students, classes, and rooms from the `.ttl` files
2. **Sort by size** - Start with the biggest classes first (they're harder to fit)
3. **Find time slots** - For each class, look for available rooms and times
4. **Check conflicts** - Make sure students aren't double-booked
5. **Assign exams** - Put students in rooms at specific times
6. **Split if needed** - If a class is too big for one room, split it into multiple sessions

## Results

When you run it, you'll get:
**24 exam sessions** scheduled across 3 rooms
**1,863 total student-exam assignments**
**100% success rate** - all 496 students scheduled for all their exams
**No conflicts** - every student can actually make it to all their exams


### schedule_simple.html
Open this in a web browser for a nice, color-coded view of the schedule. Way easier to read than the JSON!

### exam_schedule_visualization.png
A timeline chart showing when each room is being used.

## Assumptions I Made

- Each class has a fixed exam duration (can't be changed)
- Students don't care what time their exams are (no preferences)
- Any room can host any exam (no special requirements)
- It's okay to split a class across multiple rooms/times if needed
- Exams can start every 30 minutes (not just on the hour)

## Requirements

- Python 3.8 or higher
- rdflib (for reading the data files)
- jsonschema (for validating the output)
- matplotlib (for making charts)

