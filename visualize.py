#!/usr/bin/env python3

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, timedelta
from rdflib import Graph, Namespace, URIRef
import matplotlib.dates as mdates

# Set up RDF namespaces
EX = Namespace("http://example.org/")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")

# Load all the data
print("Loading RDF data...")
g = Graph()
g.parse("classes.ttl", format="ttl")
g.parse("rooms.ttl", format="ttl")
g.parse("students.ttl", format="ttl")

print("Loading schedule...")
with open("schedule.json", "r") as f:
    schedule = json.load(f)

# Helper functions to extract info from RDF data
def get_room_label(graph, room_uri):
    """Get human-readable room name"""
    label = graph.value(URIRef(room_uri), Namespace("http://www.w3.org/2000/01/rdf-schema#").label)
    return str(label) if label else room_uri.split('/')[-1]

def get_room_capacity(graph, room_uri):
    """Get max capacity for a room"""
    capacity = graph.value(URIRef(room_uri), EX.roomCapacity)
    return int(capacity) if capacity else 0

def get_room_availability(graph, room_uri):
    """Get all time windows when a room is available"""
    slots = []
    for avail_node in graph.objects(URIRef(room_uri), EX.hasAvailability):
        start_str = str(graph.value(avail_node, EX.availableFrom))
        end_str = str(graph.value(avail_node, EX.availableUntil))
        start_dt = datetime.fromisoformat(start_str)
        end_dt = datetime.fromisoformat(end_str)
        slots.append((start_dt, end_dt))
    return sorted(slots)

def get_class_label(graph, class_uri):
    """Get human-readable class name"""
    label = graph.value(URIRef(class_uri), Namespace("http://www.w3.org/2000/01/rdf-schema#").label)
    if label:
        return str(label)
    return class_uri.split('/')[-1]

# Organize data by room
all_rooms = list(g.subjects(RDF.type, EX.Room))
rooms_data = {}

for room_uri in all_rooms:
    room_id = str(room_uri)
    rooms_data[room_id] = {
        'label': get_room_label(g, room_id),
        'capacity': get_room_capacity(g, room_id),
        'availability': get_room_availability(g, room_id),
        'exams': []
    }

# Add exams to their rooms
for group_id, group_info in schedule.items():
    room_id = group_info['room']['room_iri']
    start_time = datetime.fromisoformat(group_info['room']['start'])
    end_time = datetime.fromisoformat(group_info['room']['end'])
    class_uri = group_info['class_iri']
    num_students = len(group_info['students'])
    
    if room_id in rooms_data:
        rooms_data[room_id]['exams'].append({
            'start': start_time,
            'end': end_time,
            'class': get_class_label(g, class_uri),
            'class_code': class_uri.split('/')[-1],
            'students': num_students,
            'group_id': group_id
        })

# Sort exams by time
for room_id in rooms_data:
    rooms_data[room_id]['exams'].sort(key=lambda x: x['start'])

# Create the timeline visualization
print("Creating visualization...")
fig, axes = plt.subplots(len(rooms_data), 1, figsize=(16, 3 * len(rooms_data)))

if len(rooms_data) == 1:
    axes = [axes]

# Find overall time range
all_times = []
for room_data in rooms_data.values():
    for start, end in room_data['availability']:
        all_times.extend([start, end])
    for exam in room_data['exams']:
        all_times.extend([exam['start'], exam['end']])

min_time = min(all_times)
max_time = max(all_times)

# Plot each room
for idx, (room_id, room_data) in enumerate(sorted(rooms_data.items())):
    ax = axes[idx]
    
    # Plot availability windows (green background)
    for start, end in room_data['availability']:
        ax.barh(0, (end - start).total_seconds() / 3600, 
               left=mdates.date2num(start), 
               height=0.8, 
               color='lightgreen', 
               alpha=0.3,
               edgecolor='green',
               linewidth=1)
    
    # Plot scheduled exams (blue bars)
    for exam in room_data['exams']:
        duration_hours = (exam['end'] - exam['start']).total_seconds() / 3600
        utilization = (exam['students'] / room_data['capacity']) * 100
        
        # Color based on room utilization
        if utilization >= 90:
            color = '#d62728'  # red - very full
        elif utilization >= 70:
            color = '#ff7f0e'  # orange - moderately full
        else:
            color = '#1f77b4'  # blue - comfortable
        
        bar = ax.barh(0, duration_hours,
                     left=mdates.date2num(exam['start']),
                     height=0.6,
                     color=color,
                     alpha=0.8,
                     edgecolor='black',
                     linewidth=1.5)
        
        # Add text label
        mid_time = exam['start'] + (exam['end'] - exam['start']) / 2
        label = f"{exam['class_code']}\n{exam['students']}/{room_data['capacity']}"
        ax.text(mdates.date2num(mid_time), 0, label,
               ha='center', va='center', fontsize=8, fontweight='bold')
    
    # Formatting
    ax.set_ylim(-0.5, 0.5)
    ax.set_xlim(mdates.date2num(min_time), mdates.date2num(max_time))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    ax.set_yticks([])
    ax.set_ylabel(f"{room_data['label']}\n(Cap: {room_data['capacity']})", 
                  fontsize=10, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    # Add room statistics
    total_exam_time = sum((e['end'] - e['start']).total_seconds() / 3600 
                         for e in room_data['exams'])
    total_available_time = sum((end - start).total_seconds() / 3600 
                               for start, end in room_data['availability'])
    utilization_pct = (total_exam_time / total_available_time * 100) if total_available_time > 0 else 0
    
    stats_text = f"Exams: {len(room_data['exams'])} | Time Used: {total_exam_time:.1f}h / {total_available_time:.1f}h ({utilization_pct:.1f}%)"
    ax.text(0.98, 0.95, stats_text, transform=ax.transAxes,
           ha='right', va='top', fontsize=8, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Overall title and legend
fig.suptitle('Final Exam Schedule - Room Availability and Utilization', 
            fontsize=16, fontweight='bold')

# Create legend
legend_elements = [
    mpatches.Patch(facecolor='lightgreen', alpha=0.3, edgecolor='green', label='Room Available'),
    mpatches.Patch(facecolor='#1f77b4', alpha=0.8, edgecolor='black', label='Exam (<70% full)'),
    mpatches.Patch(facecolor='#ff7f0e', alpha=0.8, edgecolor='black', label='Exam (70-90% full)'),
    mpatches.Patch(facecolor='#d62728', alpha=0.8, edgecolor='black', label='Exam (>90% full)')
]
fig.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.99, 0.98))

plt.tight_layout(rect=[0, 0.03, 1, 0.97])

# Save the figure
output_file = "exam_schedule_visualization.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"Visualization saved to: {output_file}")

# Create a summary statistics report
print("\n" + "="*60)
print("EXAM SCHEDULE STATISTICS")
print("="*60)

total_exams = len(schedule)
total_students_scheduled = sum(len(g['students']) for g in schedule.values())

print(f"\nTotal exam sessions scheduled: {total_exams}")
print(f"Total student-exam assignments: {total_students_scheduled}")

print("\nRoom Utilization:")
for room_id, room_data in sorted(rooms_data.items(), key=lambda x: x[1]['label']):
    total_exam_time = sum((e['end'] - e['start']).total_seconds() / 3600 
                         for e in room_data['exams'])
    total_available_time = sum((end - start).total_seconds() / 3600 
                               for start, end in room_data['availability'])
    utilization_pct = (total_exam_time / total_available_time * 100) if total_available_time > 0 else 0
    
    print(f"  {room_data['label']:30} - {len(room_data['exams']):2} exams, "
          f"{total_exam_time:5.1f}h / {total_available_time:5.1f}h ({utilization_pct:5.1f}%)")

print("\n" + "="*60)

# ============================================================================
# CREATE SIMPLE HTML VERSION
# This makes an easy-to-read schedule you can open in your browser
# ============================================================================

print("\n" + "="*60)
print("CREATING SIMPLE HTML SCHEDULE")
print("="*60)

from collections import defaultdict

# Organize schedule by room
room_schedule_html = defaultdict(list)

for group_id, info in schedule.items():
    room_uri = info['room']['room_iri']
    start = datetime.fromisoformat(info['room']['start'])
    end = datetime.fromisoformat(info['room']['end'])
    class_uri = info['class_iri']
    students = len(info['students'])
    
    room_schedule_html[room_uri].append({
        'start': start,
        'end': end,
        'class': get_class_label(g, class_uri),
        'class_code': class_uri.split('/')[-1],
        'students': students,
        'group_id': group_id
    })

# Sort by start time
for room_uri in room_schedule_html:
    room_schedule_html[room_uri].sort(key=lambda x: x['start'])

# Create simple HTML version
html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Final Exam Schedule</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 20px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #333;
            text-align: center;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        .room {
            background: white;
            margin: 20px 0;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .room-header {
            font-size: 20px;
            font-weight: bold;
            color: #2196F3;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }
        .exam {
            margin: 15px 0;
            padding: 15px;
            border-left: 4px solid #ddd;
            background: #fafafa;
        }
        .exam.green { border-left-color: #4CAF50; }
        .exam.yellow { border-left-color: #FF9800; }
        .exam.red { border-left-color: #f44336; }
        .time {
            font-size: 16px;
            font-weight: bold;
            color: #333;
        }
        .class-name {
            font-size: 14px;
            color: #666;
            margin: 5px 0;
        }
        .students {
            font-size: 13px;
            color: #888;
        }
        .legend {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .legend-item {
            display: inline-block;
            margin-right: 20px;
            font-size: 14px;
        }
        .color-box {
            display: inline-block;
            width: 20px;
            height: 20px;
            margin-right: 5px;
            vertical-align: middle;
            border-radius: 3px;
        }
        .summary {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .summary h2 {
            color: #333;
            margin-top: 0;
        }
    </style>
</head>
<body>
    <h1>🎓 Final Exam Schedule</h1>
    
    <div class="legend">
        <strong>Legend:</strong>
        <div class="legend-item">
            <span class="color-box" style="background: #4CAF50;"></span>
            Less than 70% full
        </div>
        <div class="legend-item">
            <span class="color-box" style="background: #FF9800;"></span>
            70-90% full
        </div>
        <div class="legend-item">
            <span class="color-box" style="background: #f44336;"></span>
            Over 90% full
        </div>
    </div>
"""

total_groups = len(schedule)
total_assignments = sum(len(g_info['students']) for g_info in schedule.values())
rooms_used = len(room_schedule_html)

for room_uri in sorted(room_schedule_html.keys(), key=lambda r: get_room_label(g, r)):
    room_name = get_room_label(g, room_uri)
    capacity = get_room_capacity(g, room_uri)
    exams = room_schedule_html[room_uri]
    
    html_content += f"""
    <div class="room">
        <div class="room-header">📍 {room_name} (Capacity: {capacity})</div>
"""
    
    for exam in exams:
        start_str = exam['start'].strftime("%a, %b %d at %I:%M %p")
        end_str = exam['end'].strftime("%I:%M %p")
        duration = (exam['end'] - exam['start']).total_seconds() / 3600
        utilization = (exam['students'] / capacity * 100) if capacity > 0 else 0
        
        if utilization >= 90:
            color_class = "red"
        elif utilization >= 70:
            color_class = "yellow"
        else:
            color_class = "green"
        
        html_content += f"""
        <div class="exam {color_class}">
            <div class="time">{start_str} - {end_str} ({duration:.1f} hours)</div>
            <div class="class-name"><strong>{exam['class_code']}:</strong> {exam['class']}</div>
            <div class="students">👥 {exam['students']}/{capacity} students ({utilization:.0f}% full)</div>
        </div>
"""
    
    html_content += "    </div>\n"

html_content += f"""
    <div class="summary">
        <h2>📊 Summary</h2>
        <p><strong>Total exam sessions:</strong> {total_groups}</p>
        <p><strong>Total student-exam assignments:</strong> {total_assignments}</p>
        <p><strong>Rooms used:</strong> {rooms_used} out of 8</p>
    </div>
</body>
</html>
"""

with open("schedule_simple.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("\n✅ Simple HTML schedule created: schedule_simple.html")
print("   Open this file in your web browser for an easy-to-read view!")
print("\n" + "="*60)
