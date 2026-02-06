from rdflib import Graph
from rdflib import URIRef
from rdflib.namespace import split_uri

from tkinter import *

ROOMPREFIX = "http://example.org/Room"
SLOTPREFIX = "http://example.org/_Time_slot"
CAP_PREFIX = "http://example.org/roomCapacity"
DUR_PREFIX = "http://example.org/examDuration"
AVL_PREFIX = "http://example.org/hasAvailability"
STARTPREFIX = "http://example.org/availableFrom"
ENDPREFIX = "http://example.org/availableUntil"

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
    
    for course in student_graph.objects(subject=student, predicate=URIRef("http://example.org/enrolledIn")):
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
    min_room_cap = next(class_graph.objects(subject=c, predicate=URIRef(CAP_PREFIX)), None)
    exam_duration = next(class_graph.objects(subject=c, predicate=URIRef(DUR_PREFIX)), None)

    if min_room_cap and exam_duration:
        _, class_code = split_uri(c)
        classes[class_code] = (min_room_cap.toPython(), float(exam_duration.toPython()))


for c in classes.items():
    print()
    print(c)

# get the available rooms plus their capacity and available time slots
for subject in room_graph.subjects():
    if subject.startswith(ROOMPREFIX):
        _, class_room = split_uri(subject)
        room_cap = next(room_graph.objects(subject=subject, predicate=URIRef(CAP_PREFIX)), None)
        temp = list(room_graph.objects(subject=subject, predicate=URIRef(AVL_PREFIX)))
        available_slots = []
        for p in temp:
            _, slot = split_uri(p)
            slot = slot[1:]
            available_slots.append(slot)
        room_caps_and_availability[class_room] = (int(room_cap.toPython()), available_slots)

for r in room_caps_and_availability.items():
    print()
    print(r)


## define the slots
for subject in room_graph.subjects():
    if subject.startswith(SLOTPREFIX):
        _, slot = split_uri(subject)
        slot = slot[1:]
        start = next(room_graph.objects(subject=subject, predicate=URIRef(STARTPREFIX)), None)
        end = next(room_graph.objects(subject=subject, predicate=URIRef(ENDPREFIX)), None)
        
        times = (start.toPython(), end.toPython())
        time_slot_defs[slot] = times

# print(times)

for item in time_slot_defs.items():
    print()
    print(item)

# for s, p, o in room_graph:
#     print(s, p, o)
