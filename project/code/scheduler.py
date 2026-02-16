import json
from datetime import timedelta
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import split_uri

class Scheduler:
    def __init__(self):
        self.EX = Namespace("http://example.org/")
        self.SCHEMA = Namespace("http://schema.org/")
        self.RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        
        self.classes = {}
        self.student_courses = {}
        self.min_room_caps_and_availability = {}
        self.time_slot_defs = {}
        self.course_to_students = {}

    def load_data(self):
        class_graph = Graph()
        room_graph = Graph()
        student_graph = Graph()

        class_graph.parse("./data/classes.ttl", format="turtle")
        room_graph.parse("./data/rooms.ttl", format="turtle")
        student_graph.parse("./data/students.ttl", format="turtle")

        for student in student_graph.subjects():
            courses = []
            for course in student_graph.objects(subject=student, predicate=URIRef(self.EX.enrolledIn)):
                _, course_code = split_uri(course)
                courses.append(course_code)
            if courses:
                _, student_name = split_uri(student)
                student_name = student_name[1:]
                self.student_courses[student_name] = courses

        for c in class_graph.subjects():
            _, class_code = split_uri(c)
            min_room_cap = class_graph.value(subject=c, predicate=URIRef(self.EX.hasMinimumRoomCapacity))
            exam_duration = class_graph.value(subject=c, predicate=URIRef(self.EX.examDuration))
            self.classes[class_code] = (int(min_room_cap.toPython()), float(exam_duration.toPython()))

        for room, _, room_cap in room_graph.triples((None, URIRef(self.EX.roomCapacity), None)):
            _, room_name = split_uri(room)
            slot_uris = room_graph.objects(room, URIRef(self.EX.hasAvailability))
            available_slots = [split_uri(s)[1] for s in slot_uris]
            self.min_room_caps_and_availability[room_name] = (int(room_cap.toPython()), available_slots)

        for subject in room_graph.subjects():
            if str(subject).startswith(str(self.EX._Time_slot)):
                _, slot = split_uri(subject)
                start_lit = room_graph.value(subject=subject, predicate=URIRef(self.EX.availableFrom))
                end_lit = room_graph.value(subject=subject, predicate=URIRef(self.EX.availableUntil))
                start = start_lit.toPython()
                end = end_lit.toPython()
                slot_hours = (end - start).total_seconds() / 3600.0
                self.time_slot_defs[slot] = (start, end, slot_hours)

        for student, enrolled_courses in self.student_courses.items():
            for c in enrolled_courses:
                if c not in self.course_to_students:
                    self.course_to_students[c] = set()
                self.course_to_students[c].add(student)

    def all_exam_windows(self, slot_start, slot_end, exam_duration, step_hours=1):
        windows = []
        current = slot_start
        while current + timedelta(hours=exam_duration) <= slot_end:
            windows.append((current, current + timedelta(hours=exam_duration)))
            current += timedelta(hours=step_hours)
        return windows

    def is_consistent(self, course, option, assignment):
        start_new, end_new = option['window']
        room_new = option['room']
        students_new = self.course_to_students.get(course, set())

        for other_course, other_val in assignment.items():
            start_other, end_other = other_val['window']
            if start_new < end_other and start_other < end_new:
                if room_new == other_val['room']:
                    return False
                if students_new.intersection(self.course_to_students.get(other_course, set())):
                    return False
        return True

    def get_options(self, course_code):
        options = []
        min_cap, duration = self.classes[course_code]
        for room, (room_cap, available_slots) in self.min_room_caps_and_availability.items():
            if room_cap < min_cap: continue
            for slot in available_slots:
                s_start, s_end, _ = self.time_slot_defs[slot]
                for window in self.all_exam_windows(s_start, s_end, duration):
                    options.append({'room': room, 'window': window})
        return options

    def schedule_backtrack(self, assignment, classes_to_schedule):
        if not classes_to_schedule:
            return assignment
        current_class = classes_to_schedule[0]
        remaining_classes = classes_to_schedule[1:]

        for option in self.get_options(current_class):
            if self.is_consistent(current_class, option, assignment):
                assignment[current_class] = option
                result = self.schedule_backtrack(assignment, remaining_classes)
                if result is not None:
                    return result
                del assignment[current_class]
        return None


def run_and_export_json(scheduler):
    scheduler.load_data()
    all_classes = list(scheduler.classes.keys())
    
    final_schedule = scheduler.schedule_backtrack({}, all_classes)
    
    if final_schedule:
        structured_json = {}
        
        for i, (course_code, details) in enumerate(final_schedule.items(), 1):
            group_key = f"group_{i:04d}"
            
            start_time, end_time = details['window']
            time_slot_str = f"{start_time.isoformat()} - {end_time.isoformat()}"
            
            student_list = [
                str(scheduler.EX[f"_{name}"]) 
                for name in scheduler.course_to_students.get(course_code, [])
            ]
            
            structured_json[group_key] = {
                "students": student_list,
                "room": {
                    "room_iri": str(scheduler.EX[details['room']]),
                    "time_slot": time_slot_str
                },
                "class_iri": str(scheduler.EX[course_code])
            }
        
        return json.dumps(structured_json, indent=4)
    else:
        return json.dumps({"error": "No valid schedule found"}, indent=4)

if __name__ == "__main__":
    s = Scheduler()
    
    json_output = run_and_export_json(s)
    
    print(json_output)
    
    with open("schedule.json", "w") as f:
        f.write(json_output)