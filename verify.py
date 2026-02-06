import json
import jsonschema
import os
import sys
from rdflib import Graph, Namespace, URIRef
from datetime import datetime

# Type hints for better code clarity
from typing import TypedDict


class RoomInfo(TypedDict):
    end: str
    room_iri: str
    start: str


class GroupInfo(TypedDict):
    students: list[str]
    room: RoomInfo
    class_iri: str


OutputType = dict[str, GroupInfo]


# Set up RDF namespaces
TTL_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

EX = Namespace("http://example.org/")
SCHEMA = Namespace("http://schema.org/")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")

# Load all the RDF data files
g = Graph()
for filename in os.listdir(TTL_DIRECTORY):
    if filename.endswith(".ttl"):
        file_path = os.path.join(TTL_DIRECTORY, filename)
        g.parse(file_path, format="ttl")
print("Successfully loaded data!\n")

# Verification functions - these check if the schedule is valid


def verify_room_capacity(output: OutputType, graph: Graph):
    """Make sure no room has more students than it can hold"""
    all_ok = True

    for group_id, group_info in output.items():
        room_iri = group_info["room"]["room_iri"]
        assigned_students = group_info["students"]

        room_capacity = int(
            next(graph.objects(URIRef(room_iri), EX.roomCapacity)))

        if len(assigned_students) > room_capacity:
            print(f"ERROR: {group_id} has {len(assigned_students)} students "
                  f"but room capacity is {room_capacity} ({room_iri})")
            all_ok = False

    assert all_ok


def verify_student_exam_conflicts(output: OutputType):
    """Make sure no student has two exams at the same time"""
    all_ok = True
    student_assignments = {}

    # Collect all student assignments
    for group_id, group_info in output.items():
        start_dt, end_dt = parse_slot_time_slot(group_info["room"])
        class_iri = group_info["class_iri"]
        for student in group_info["students"]:
            student_assignments.setdefault(student, []).append({
                "class": class_iri,
                "start": start_dt,
                "end": end_dt,
                "group_id": group_id
            })

    # Check each student's schedule for overlaps
    for student, assignments in student_assignments.items():
        assignments.sort(key=lambda x: x["start"])
        for i in range(len(assignments) - 1):
            current = assignments[i]
            next_ = assignments[i + 1]
            if current["end"] > next_["start"]:
                print(f"CONFLICT: {student} has overlapping exams "
                      f"{current['class']} (group {current['group_id']}) and "
                      f"{next_['class']} (group {next_['group_id']})")
                all_ok = False

    assert all_ok


def verify_all_students_have_all_finals(output: OutputType, graph: Graph):
    """
    Make sure every student has an exam scheduled for each class
    they're enrolled in
    """
    all_ok = True

    # Build a map of which classes each student has scheduled
    scheduled_classes: dict[str, set] = {}

    for group in output.values():
        class_iri = group["class_iri"]
        for student in group["students"]:
            scheduled_classes.setdefault(student, set()).add(class_iri)

    # Compare with what they're actually enrolled in
    for student in scheduled_classes:
        enrolled_classes = {
            str(c) for c in graph.objects(URIRef(student), EX.enrolledIn)
        }

        assigned_classes = scheduled_classes.get(student, set())

        missing_classes = enrolled_classes - assigned_classes

        if len(missing_classes):
            print(f"ERROR: {student} missing finals for:")
            for cls in missing_classes:
                print(f"  - {cls}")
            all_ok = False

    assert all_ok


def verify_exam_room_fit(output: OutputType, graph: Graph):
    """
    Make sure each exam actually fits within the time the room is available
    """
    all_ok = True

    for group_id, group_info in output.items():
        room_iri = URIRef(group_info["room"]["room_iri"])

        start_str = group_info["room"]["start"]
        end_str = group_info["room"]["end"]
        exam_start = datetime.fromisoformat(start_str)
        exam_end = datetime.fromisoformat(end_str)

        availability_windows = get_room_slots(graph, room_iri)

        # Check if exam fits in any window
        fits = False
        for avail_start, avail_end in availability_windows:
            if exam_start >= avail_start and exam_end <= avail_end:
                fits = True
                break

        if not fits:
            print(f"ERROR: Exam {group_info['class_iri']} in group {group_id} "
                  f"scheduled {exam_start} - {exam_end} does NOT fit in room {room_iri} availability")
            all_ok = False

    assert all_ok


def verify_no_room_overlaps(output: OutputType):
    """Make sure no room is double-booked"""
    all_ok = True
    exam_assignments: dict[str, list[tuple[str, str, str]]] = {}

    # Collect all exams per room
    for group_id, group_info in output.items():
        room_iri = group_info["room"]["room_iri"]
        start_dt, end_dt = parse_slot_time_slot(group_info["room"])

        exam_assignments.setdefault(room_iri, []).append(
            (start_dt, end_dt, group_id)
        )

    # Check each room for overlaps
    for room_iri, exams in exam_assignments.items():
        exams.sort(key=lambda x: x[0])

        for i in range(len(exams) - 1):
            curr_start, curr_end, curr_group = exams[i]
            next_start, next_end, next_group = exams[i + 1]

            if curr_end > next_start:
                print(
                    f"ROOM CONFLICT: Room {room_iri} has overlapping exams "
                    f"{curr_group} ({curr_start} - {curr_end}) and "
                    f"{next_group} ({next_start} - {next_end})"
                )
                all_ok = False

    assert all_ok


def verify_no_duplicate_exam_assignments(output: OutputType):
    """Make sure no student is assigned to the same exam multiple times"""
    all_ok = True

    student_exam_map: dict[str, dict[str, list[str]]] = {}

    for group_id, group_info in output.items():
        class_iri = group_info["class_iri"]

        for student in group_info["students"]:
            student_exam_map.setdefault(student, {}).setdefault(
                class_iri, []).append(group_id)

    # Check for duplicates
    for student, classes in student_exam_map.items():
        for class_iri, groups in classes.items():
            if len(groups) > 1:
                print(
                    f"DUPLICATE EXAM: {student} assigned to multiple groups for class {class_iri}: {groups}")
                all_ok = False

    assert all_ok


def verify_all_student_exams_are_accounted_for(output: OutputType, graph: Graph):
    """
    Final sanity check - make sure the total number of student-exam
    assignments matches what we expect
    """
    students_in_exams = 0
    expected_number_of_students_in_exams = 0
    
    for group_info in output.values():
        students_in_exams += len(group_info["students"])
    
    students = get_students(graph)
    for student in students:
        expected_number_of_students_in_exams += len(
            get_student_classes(graph, student))

    all_ok = students_in_exams == expected_number_of_students_in_exams

    assert all_ok


# Helper functions

def parse_time_slot(start_str: str, end_str: str):
    """Convert time strings to Python datetime objects"""
    return datetime.fromisoformat(start_str), datetime.fromisoformat(end_str)


def parse_slot_time_slot(data: dict[str, str]):
    """Convert a time slot dictionary to datetime tuple"""
    start_str = data["start"]
    end_str = data["end"]
    start_dt = datetime.fromisoformat(start_str)
    end_dt = datetime.fromisoformat(end_str)
    return start_dt, end_dt


def get_students(graph: Graph):
    """Get all student URIs from the graph"""
    return list(graph.subjects(predicate=RDF.type, object=EX.Person))


def get_student_classes(graph: Graph, student_uri: URIRef):
    """Get all classes a student is enrolled in"""
    return list(graph.objects(student_uri, EX.enrolledIn))


def get_room_slots(graph: Graph, room_uri: URIRef):
    """Get all time windows when a room is available"""
    availability_slots = list(graph.objects(room_uri, EX.hasAvailability))

    starts = []
    ends = []

    for availability_node in availability_slots:
        starts.append(
            next(graph.objects(availability_node, EX.availableFrom), None))
        ends.append(
            next(graph.objects(availability_node, EX.availableUntil), None))
    
    return [parse_time_slot(str(s), str(e)) for s, e in zip(starts, ends)]


def get_rooms(graph: Graph):
    """Get all room URIs from the graph"""
    return list(graph.subjects(predicate=RDF.type, object=EX.Room))


def get_exam_duration_hours(graph: Graph, class_iri: str):
    """Get exam duration in hours as a float"""
    duration_literal = next(graph.objects(URIRef(class_iri), EX.examDuration))

    try:
        return float(duration_literal)
    except ValueError:
        raise ValueError(
            f"Unsupported examDuration format: {duration_literal}")


# Main script
if "__main__" == __name__:
    # Check if user provided a filename
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <filename.json>")
        sys.exit(1)

    # Load the schedule
    filename = sys.argv[1]
    with open(filename, "r") as f:
        schedule = json.load(f)

    # Define expected JSON format
    schema = {
        "type": "object",
        "additionalProperties": {
            "type": "object",
            "properties": {
                "students": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1
                },
                "room": {
                    "type": "object",
                    "properties": {
                        "room_iri": {"type": "string"},
                        "start": {"type": "string"},
                        "end": {"type": "string"}
                    },
                    "required": ["room_iri", "start", "end"]
                },
                "class_iri": {"type": "string"}
            },
            "required": ["students", "room", "class_iri"]
        }
    }

    # Run all the verification checks
    try:
        jsonschema.validate(instance=schedule, schema=schema)
        verify_room_capacity(schedule, g)
        verify_student_exam_conflicts(schedule)
        verify_all_students_have_all_finals(schedule, g)
        verify_exam_room_fit(schedule, g)
        verify_no_room_overlaps(schedule)
        verify_no_duplicate_exam_assignments(schedule)
        verify_all_student_exams_are_accounted_for(schedule, g)
        print("This is a valid schedule!")
    except jsonschema.ValidationError as e:
        print("Validation error:", e)
