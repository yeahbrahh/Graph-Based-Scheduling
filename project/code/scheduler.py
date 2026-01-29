from rdflib import Graph

class_graph = Graph()
room_graph = Graph()
student_graph = Graph()

class_graph.parse("./data/classes.ttl")

room_graph.parse("./data/rooms.ttl")

student_graph.parse("./data/students.ttl")

print(len(class_graph))

import pprint

for stmt in class_graph:
    pprint.pprint(stmt)

for _ in range (5):
    print()

for stmt in room_graph:
    pprint.pprint(stmt)

for _ in range(5):
    print()

for stmt in student_graph:
    pprint.pprint(stmt)

print()
