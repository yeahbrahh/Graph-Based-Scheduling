from rdflib import FOAF, Graph
from rdflib.namespace import RDF
from rdflib import URIRef

class_graph = Graph()
room_graph = Graph()
student_graph = Graph()

class_graph.parse("./data/classes.ttl")
room_graph.parse("./data/rooms.ttl")
student_graph.parse("./data/students.ttl")

student_courses = {}
classes = {}

# get all classes a student is enrolled in
for student in student_graph.subjects(predicate=URIRef("http://example.org/enrolledIn"), object=None):
    student_courses[student] = list(student_graph.objects(subject=student, predicate=URIRef("http://example.org/enrolledIn")))

for k, v in student_courses.items():
    print(k, v)

# get all students in a class

for s, p, o in class_graph:
    print(p)

predicates = [
    URIRef("http://example.org/hasMinimumRoomCapacity"),
    URIRef("http://example.org/examDuration")
]

for c in class_graph.subjects():
    classes[c] = ()
