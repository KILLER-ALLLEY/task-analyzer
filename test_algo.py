from backend.tasks.scoring import TaskScorer

def run_test(name, func):
    print("\n=== " + name + " ===")
    try:
        func()
    except Exception as e:
        print("Error raised:", e)


def test_missing_fields():
    scorer = TaskScorer()

    tasks = [
        {
            "id": 1,
            "title": "Incomplete task",
            "due_date": None,
            "estimated_hours": None,
            "importance": None,
            "dependencies": []
        }
    ]

    result = scorer.score_all(tasks)
    print("Output:", result)


def test_invalid_date():
    scorer = TaskScorer()

    tasks = [
        {
            "id": 1,
            "title": "Invalid date task",
            "due_date": "invalid-date",
            "estimated_hours": 3,
            "importance": 5,
            "dependencies": []
        }
    ]

    result = scorer.score_all(tasks)
    print("Output:", result)


def test_past_due_urgency():
    scorer = TaskScorer()

    tasks = [
        {
            "id": 1,
            "title": "Past due task",
            "due_date": "2020-01-01",
            "estimated_hours": 3,
            "importance": 5,
            "dependencies": []
        }
    ]

    result = scorer.score_all(tasks)
    print("Output:", result)


def test_circular_dependencies():
    scorer = TaskScorer()

    tasks = [
        {"id": 1, "title": "A", "due_date": "2025-01-01", "estimated_hours": 2, "importance": 5, "dependencies": [2]},
        {"id": 2, "title": "B", "due_date": "2025-01-01", "estimated_hours": 2, "importance": 5, "dependencies": [1]},
    ]

    scorer.score_all(tasks)  # Should raise ValueError


def test_low_effort_boost():
    scorer = TaskScorer()

    tasks = [
        {"id": 1, "title": "Quick fix", "due_date": "2025-12-01", "estimated_hours": 1, "importance": 5, "dependencies": []},
        {"id": 2, "title": "Heavy task", "due_date": "2025-12-01", "estimated_hours": 12, "importance": 5, "dependencies": []}
    ]

    result = scorer.score_all(tasks)
    print("Output:", [(t["title"], t["score"]) for t in result])


def test_dependency_priority():
    scorer = TaskScorer()

    tasks = [
        {"id": 1, "title": "Core API", "due_date": "2025-11-30", "estimated_hours": 4, "importance": 7, "dependencies": []},
        {"id": 2, "title": "Integrate FE", "due_date": "2025-12-10", "estimated_hours": 3, "importance": 6, "dependencies": [1]},
        {"id": 3, "title": "Final testing", "due_date": "2025-12-15", "estimated_hours": 2, "importance": 5, "dependencies": [1]},
    ]

    result = scorer.score_all(tasks)
    print("Output:", [(t["title"], t["score"]) for t in result])


if __name__ == "__main__":
    run_test("Missing fields", test_missing_fields)
    run_test("Invalid date format", test_invalid_date)
    run_test("Past due urgency boost", test_past_due_urgency)
    run_test("Circular dependency detection", test_circular_dependencies)
    run_test("Low effort task boost", test_low_effort_boost)
    run_test("Tasks that block others get priority", test_dependency_priority)

    print("\nAll tests completed.\n")
