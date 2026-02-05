from rdflib import Graph
from rdflib import URIRef
from rdflib.namespace import split_uri

class_graph = Graph()
room_graph = Graph()
student_graph = Graph()

class_graph.parse("./data/classes.ttl", format="turtle")
room_graph.parse("./data/rooms.ttl")
student_graph.parse("./data/students.ttl")

student_courses = {}
classes = {}

# get all classes a student is enrolled in
for student in student_graph.subjects():
    courses = []
    
    for course in student_graph.objects(subject=student, predicate=URIRef("http://example.org/enrolledIn")):
         _, course_code = split_uri(course)
         courses.append(course_code)
    if courses:
        _, student_name = split_uri(student)
        student_courses[student_name] = courses                         

for student in student_courses.items():
    print(student)

for k, v in student_courses.items():
    print(k, v)

tup = ()

# gets min room capacities and exam durations (respectively)
for c in class_graph.subjects():
    room_cap = next(class_graph.objects(subject=c, predicate=URIRef("http://example.org/hasMinimumRoomCapacity")), None)
    exam_duration = next(class_graph.objects(subject=c, predicate=URIRef("http://example.org/examDuration")), None)

    if room_cap and exam_duration:
        _, class_code = split_uri(c)
        classes[class_code] = (room_cap.toPython(), float(exam_duration.toPython()))


for c in classes.items():
    print()
    print(c)

    print(type(classes["CS310"][0]))
