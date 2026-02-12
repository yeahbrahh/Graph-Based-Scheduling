from rdflib import Graph
from rdflib import URIRef
from rdflib.namespace import split_uri

ENROLLEDPRE = "http://example.org/enrolledIn"
ROOMPRE = "http://example.org/Room"
ROOMCAP_PRE = "http://example.org/roomCapacity"
SLOTPRE = "http://example.org/_Time_slot"
CAP_PRE = "http://example.org/hasMinimumRoomCapacity"
DUR_PRE = "http://example.org/examDuration"
AVL_PRE = "http://example.org/hasAvailability"
STARTPRE = "http://example.org/availableFrom"
ENDPRE = "http://example.org/availableUntil"

class_graph = Graph()
room_graph = Graph()
student_graph = Graph()

class_graph.parse("./data/classes.ttl", format="turtle")
room_graph.parse("./data/rooms.ttl", format="turtle")
student_graph.parse("./data/students.ttl", format="turtle")
classes = {}
student_courses = {}
room_caps_and_availability = {}
time_slot_defs = {}

# get all the students and the classes they are enrolled in
for student in student_graph.subjects():
    courses = []

    for course in student_graph.objects(subject=student, predicate=URIRef(ENROLLEDPRE)):
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
    min_room_cap = class_graph.value(subject=c, predicate=URIRef(CAP_PRE))
    exam_duration = class_graph.value(subject=c, predicate=URIRef(DUR_PRE))
    classes[class_code] = (int(min_room_cap.toPython()), float(exam_duration.toPython()))

for c in classes.items():
    print()
    print(c)


# get the available rooms plus their capacity and available time slots
for subject in room_graph.subjects():
    if subject.startswith(ROOMPRE):
        _, class_room = split_uri(subject)
        room_cap = room_graph.value(subject=subject, predicate=URIRef(ROOMCAP_PRE))
        temp = list(room_graph.objects(subject=subject, predicate=URIRef(AVL_PRE)))
        available_slots = []
        for p in temp:
            _, slot = split_uri(p)
            slot = slot[1:]
            available_slots.append(slot)
        room_caps_and_availability[class_room] = (int(room_cap.toPython()), available_slots)

for r in room_caps_and_availability.items():
    print()
    print(r)

# for s, p, o in room_graph:
#     print(s, p, o)


## define the slots
for subject in room_graph.subjects():
    if subject.startswith(SLOTPRE):
        _, slot = split_uri(subject)
        slot = slot[1:]
        start = room_graph.value(subject=subject, predicate=URIRef(STARTPRE))
        end = room_graph.value(subject=subject, predicate=URIRef(ENDPRE))

        slot_length = end.toPython() - start.toPython()
        slot_hours = slot_length.total_seconds() / 3600.0
        times = (start.toPython(), end.toPython(), slot_hours)
        time_slot_defs[slot] = times


for item in time_slot_defs.items():
    print()
    print(item)

# for s, p, o in room_graph:
#     print(s, p, o)

potentials = {}
candidates = set()

# def schedule_backtracking(key: str) -> dict:

# narrow down potential rooms by capacity
for c in classes:
    min_cap = classes[c][0]
    for room in room_caps_and_availability:
        max_room_cap = room_caps_and_availability[room][0]
        if max_room_cap < min_cap:
            candidates.add(room)
        potentials[c] = candidates
    # check if each room has a timeslot long enough for exam / exam_duration <= time_slot.length
    for room in potentials[c]:
        pass

    # translate piece of time_slot taken up into real time / e.g. if total_time = 10.0 (12:00pm - 10:00pm) 
    # and exam_duration = 2.0 (12:00pm - 2:00pm), total_time now = 8.0 and 12-2 of slot_x = taken  

    # check for student conflicts (a student has two exam simultaneously)

    # check for double booked rooms

    
    





print()

for p in potentials.items():
    print(p)






