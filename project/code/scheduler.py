import verify

from datetime import timedelta
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import split_uri

EX = Namespace("http://example.org/")
SCHEMA = Namespace("http://schema.org/")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")

class_graph = Graph()
room_graph = Graph()
student_graph = Graph()

class_graph.parse("./data/classes.ttl", format="turtle")
room_graph.parse("./data/rooms.ttl", format="turtle")
student_graph.parse("./data/students.ttl", format="turtle")

classes = {}
student_courses = {}
min_room_caps_and_availability = {}
time_slot_defs = {}

# get all the students and the classes they are enrolled in
for student in student_graph.subjects():
    courses = []

    for course in student_graph.objects(subject=student, predicate=URIRef(EX.enrolledIn)):
        _, course_code = split_uri(course)
        courses.append(course_code)
    if courses:
        _, student_name = split_uri(student)
        student_name = student_name[1:]
        student_courses[student_name] = courses

for student in student_courses.items():
    print(student)

# gets all classes and their min room capacities and exam durations (respectively)
for c in class_graph.subjects():
    _, class_code = split_uri(c)
    min_room_cap = class_graph.value(subject=c, predicate=URIRef(EX.hasMinimumRoomCapacity))
    exam_duration = class_graph.value(subject=c, predicate=URIRef(EX.examDuration))
    classes[class_code] = (int(min_room_cap.toPython()),
                           float(exam_duration.toPython()))

for c in classes.items():
    print()
    print(c)


# get the available rooms plus their capacity and available time slots
for subject in room_graph.subjects():
    if subject.startswith(EX.roomCapacity):
        _, class_room = split_uri(subject)
        room_cap = room_graph.value(
            subject=subject, predicate=URIRef(EX.roomCapacity))
        temp = list(room_graph.objects(
            subject=subject, predicate=URIRef(EX.hasAvailability)))
        available_slots = []
        for p in temp:
            _, slot = split_uri(p)
            slot = slot[1:]
            available_slots.append(slot)
        min_room_caps_and_availability[class_room] = (
            int(room_cap.toPython()), available_slots)

for r in min_room_caps_and_availability.items():
    print()
    print(r)

# for s, p, o in room_graph:
#     print(s, p, o)


# define the slots
for subject in room_graph.subjects():
    if subject.startswith(EX._Time_slot):
        _, slot = split_uri(subject)
        slot = slot[1:]
        start = room_graph.value(subject=subject, predicate=URIRef(EX.availableFrom))
        end = room_graph.value(subject=subject, predicate=URIRef(EX.availableUntil))

        slot_length = end.toPython() - start.toPython()
        slot_hours = slot_length.total_seconds() / 3600.0
        times = (start.toPython(), end.toPython(), slot_hours)
        time_slot_defs[slot] = times


for item in time_slot_defs.items():
    print()
    print(item)

# sliding window
def all_exam_windows(slot_start, slot_end, exam_duration, step_hours=1):
    windows = []
    current = slot_start

    while current + timedelta(hours=exam_duration) <= slot_end:
        end = current + timedelta(hours=exam_duration)
        windows.append((current, end))
        current += timedelta(hours=step_hours)
    
    return windows
        

potential_rooms = {}

# narrow down potential rooms by capacity
# def schedule_backtracking(key: str) -> dict:
for c in classes:
    min_cap, exam_duration = classes[c]
    candidates = set()
    for room, (room_cap, _) in min_room_caps_and_availability.items():
        if room_cap >= min_cap:
            candidates.add(room)
    potential_rooms[c] = candidates

    for room in potential_rooms[c]:
        for slot, (slot_start, slot_end, slot_hours) in time_slot_defs.items():
           possible_times = all_exam_windows(
               slot_start,
               slot_end,
               exam_duration,
               step_hours=1
           )

           for start, end in possible_times:
                print(f"Course: {c}, Exam Duration: {exam_duration}/hrs, Potential Room: {room}, Time Slot: {slot}, Total Slot Length: {slot_hours}/hrs, Possible Exam Time: ({start} to {end})")
    
    
    # make sure possible exam time is not already taken
    
    reserved = {}


    # check for student conflicts (a student has two exam simultaneously)

    

    # course -> exam time
    # exam time -> all students in course