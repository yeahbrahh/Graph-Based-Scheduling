#!/usr/bin/env python3

from rdflib import Graph, Namespace, URIRef
from datetime import datetime, timedelta
from collections import defaultdict
import json

# Set up the namespaces for RDF queries
EX = Namespace("http://example.org/")
SCHEMA = Namespace("http://schema.org/")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")

# Load all the RDF data files
print("Loading data files...")
g = Graph()
g.parse("classes.ttl", format="ttl")
g.parse("rooms.ttl", format="ttl")
g.parse("students.ttl", format="ttl")
print(f"Loaded {len(g)} triples\n")


# Helper functions to get data from RDF

def get_all_students(graph):
    """Get list of all student URIs"""
    return list(graph.subjects(RDF.type, EX.Person))


def get_all_classes(graph):
    """Get list of all class URIs"""
    return list(graph.subjects(RDF.type, EX.Class))


def get_all_rooms(graph):
    """Get list of all room URIs"""
    return list(graph.subjects(RDF.type, EX.Room))


def get_student_classes(graph, student_uri):
    """Get all classes a student is enrolled in"""
    return list(graph.objects(student_uri, EX.enrolledIn))


def get_class_students(graph, class_uri):
    """Get all students enrolled in a specific class"""
    students = []
    for student in get_all_students(graph):
        if class_uri in get_student_classes(graph, student):
            students.append(student)
    return students


def get_exam_duration(graph, class_uri):
    """Get exam duration in hours for a class"""
    duration = graph.value(class_uri, EX.examDuration)
    return float(duration)


def get_room_capacity(graph, room_uri):
    """Get max capacity for a room"""
    capacity = graph.value(room_uri, EX.roomCapacity)
    return int(capacity)


def get_room_availability(graph, room_uri):
    """Get list of time windows when a room is available"""
    slots = []
    for avail_node in graph.objects(room_uri, EX.hasAvailability):
        start_str = str(graph.value(avail_node, EX.availableFrom))
        end_str = str(graph.value(avail_node, EX.availableUntil))
        
        start_dt = datetime.fromisoformat(start_str)
        end_dt = datetime.fromisoformat(end_str)
        slots.append((start_dt, end_dt))
    
    return slots


# Functions for scheduling logic

def generate_time_slots(availability_window, duration_hours):
    """
    Create all possible start times for an exam within a room's availability.
    Uses 30-minute increments.
    """
    start, end = availability_window
    duration = timedelta(hours=duration_hours)
    slots = []
    
    current = start
    while current + duration <= end:
        slots.append((current, current + duration))
        current += timedelta(minutes=30)
    
    return slots


def has_time_conflict(slot1, slot2):
    """Check if two time slots overlap"""
    start1, end1 = slot1
    start2, end2 = slot2
    
    return not (end1 <= start2 or end2 <= start1)


def is_student_available(student_uri, time_slot, student_schedule):
    """Check if a student is free during a specific time"""
    if student_uri not in student_schedule:
        return True
    
    for scheduled_slot in student_schedule[student_uri]:
        if has_time_conflict(time_slot, scheduled_slot):
            return False
    
    return True


def is_room_available(room_uri, time_slot, room_schedule):
    """Check if a room is free during a specific time"""
    if room_uri not in room_schedule:
        return True
    
    for scheduled_slot in room_schedule[room_uri]:
        if has_time_conflict(time_slot, scheduled_slot):
            return False
    
    return True


# Main scheduling function

def schedule_exams(graph):
    """
    Main algorithm that schedules all exams.
    Strategy: Schedule biggest classes first, then fit in smaller ones.
    """
    schedule = {}
    group_counter = 1
    
    # Track when each student and room is busy
    student_schedule = defaultdict(list)
    room_schedule = defaultdict(list)
    
    # Get all classes and sort by size (biggest first)
    all_classes = get_all_classes(graph)
    class_data = []
    
    for class_uri in all_classes:
        students = get_class_students(graph, class_uri)
        duration = get_exam_duration(graph, class_uri)
        class_data.append({
            'uri': class_uri,
            'students': students,
            'count': len(students),
            'duration': duration
        })
    
    class_data.sort(key=lambda x: x['count'], reverse=True)
    
    print(f"Scheduling {len(class_data)} classes...")
    print(f"Total students: {len(get_all_students(graph))}\n")
    
    # Schedule each class
    for class_info in class_data:
        class_uri = class_info['uri']
        all_students = class_info['students']
        duration_hours = class_info['duration']
        
        print(f"Scheduling {str(class_uri)} ({len(all_students)} students, {duration_hours}h exam)")
        
        # Keep track of students we haven't scheduled yet
        unscheduled_students = all_students[:]
        
        # Keep trying until everyone is scheduled
        while unscheduled_students:
            scheduled_this_round = False
            
            all_rooms = get_all_rooms(graph)
            
            # Try each room
            for room_uri in all_rooms:
                if not unscheduled_students:
                    break
                
                room_capacity = get_room_capacity(graph, room_uri)
                availability_windows = get_room_availability(graph, room_uri)
                
                # Try each time window for this room
                for window in availability_windows:
                    if not unscheduled_students:
                        break
                    
                    # Get all possible start times
                    possible_slots = generate_time_slots(window, duration_hours)
                    
                    # Try each time slot
                    for time_slot in possible_slots:
                        if not unscheduled_students:
                            break
                        
                        # Check if room is free
                        if not is_room_available(room_uri, time_slot, room_schedule):
                            continue
                        
                        # Find students who are free during this time
                        available_students = []
                        for student in unscheduled_students:
                            if is_student_available(student, time_slot, student_schedule):
                                available_students.append(student)
                                
                                # Stop if room is full
                                if len(available_students) >= room_capacity:
                                    break
                        
                        # If we found students, schedule them!
                        if available_students:
                            group_id = f"group_{group_counter:04d}"
                            group_counter += 1
                            
                            start_time, end_time = time_slot
                            
                            # Add to the schedule
                            schedule[group_id] = {
                                'students': [str(s) for s in available_students],
                                'room': {
                                    'room_iri': str(room_uri),
                                    'start': start_time.isoformat(),
                                    'end': end_time.isoformat()
                                },
                                'class_iri': str(class_uri)
                            }
                            
                            # Update our tracking
                            for student in available_students:
                                student_schedule[student].append(time_slot)
                                unscheduled_students.remove(student)
                            
                            room_schedule[room_uri].append(time_slot)
                            
                            print(f"  -> Scheduled {len(available_students)} students in {str(room_uri)} "
                                  f"at {start_time.strftime('%Y-%m-%d %H:%M')}")
                            
                            scheduled_this_round = True
                            break
            
            # If we couldn't schedule anyone, something's wrong
            if not scheduled_this_round and unscheduled_students:
                print(f"  WARNING: Could not schedule {len(unscheduled_students)} students for {str(class_uri)}")
                print(f"     This might mean we need more rooms or time slots.")
                break
        
        if not unscheduled_students:
            print(f"  [OK] Successfully scheduled all students for {str(class_uri)}")
        print()
    
    return schedule

# Run the scheduler
if __name__ == "__main__":
    print("=" * 60)
    print("FINAL EXAM SCHEDULER")
    print("=" * 60 + "\n")
    
    schedule = schedule_exams(g)
    
    # Save to JSON file
    output_file = "schedule.json"
    with open(output_file, "w") as f:
        json.dump(schedule, f, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"Schedule saved to: {output_file}")
    print(f"Total exam groups: {len(schedule)}")
    print(f"{'=' * 60}\n")
    print("Run verification with:")
    print(f"  python verify.py {output_file}")
