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
for room, _, room_cap in room_graph.triples((None, URIRef(EX.roomCapacity), None)):
    _, room_name = split_uri(room)

    slot_uris = room_graph.objects(room, URIRef(EX.hasAvailability))
    available_slots = []

    for s in slot_uris:
        _, slot = split_uri(s)
        available_slots.append(slot)

    min_room_caps_and_availability[room_name] = (
        int(room_cap.toPython()),
        available_slots
    )


for r in min_room_caps_and_availability.items():
    print()
    print(r)

# for s, p, o in room_graph:
#     print(s, p, o)


# define the slots
for subject in room_graph.subjects():
    if str(subject).startswith(str(EX._Time_slot)):
        _, slot = split_uri(subject)
        start_lit = room_graph.value(subject=subject, predicate=URIRef(EX.availableFrom))
        end_lit = room_graph.value(subject=subject, predicate=URIRef(EX.availableUntil))

        start = start_lit.toPython()
        end = end_lit.toPython()
        slot_hours = (end - start).total_seconds() / 3600.0
        time_slot_defs[slot] = (start, end, slot_hours)


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
exam_perms = {}

# get all possible exam times for each time slot
for class_code, (min_cap, exam_duration) in classes.items():
    for room, (room_cap, available_slots) in min_room_caps_and_availability.items():
        if room_cap < min_cap:
            continue
        for slot, (slot_start, slot_end, slot_hours) in time_slot_defs.items():
            if slot not in available_slots:
                continue
            for start, end in all_exam_windows(slot_start, slot_end, exam_duration):
                  print(
                    f"Course: {class_code}, "
                    f"Room: {room}, "
                    f"Slot: {slot}, "
                    f"Duration: {exam_duration} hrs, "
                    f"Window: ({start} → {end})"
                )
    






    
    
    # def schedule_backtrack(assignment, classes_to_schedule):
    #     if not classes_to_schedule:
    #         return assignment;
    #     current_class = classes_to_schedule[0]
    #     remaining_classes = classes_to_schedule[1]

    #     for option in get_all_possible_options(current_class):
    #         if is_consistent(current_class, option, assignment):
    #             assignment[current_class] = option
    #             result = backtrack(assignment, remaining_classes)
                
    #             if result is not None:
    #                 return result
    #             del assignment[current_class]
    #     return None
