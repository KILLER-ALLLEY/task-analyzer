from datetime import datetime, timedelta
from collections import defaultdict

try:
    import holidays as _holidays_pkg
except Exception:
    _holidays_pkg = None


class TaskScorer:
    def __init__(self, strategy="smart_balance", country_code="IN"):
        self.strategy = strategy
        self.country_code = country_code
        self.weights = self.get_weights(strategy)
        self.holidays_available = _holidays_pkg is not None
        self._holiday_cache = {}
        self.errors = []

    # Strategy weights
    def get_weights(self, strategy):
        presets = {
            "fastest_wins": {"urgency": 0.2, "importance": 0.2, "effort": 0.5, "dependency": 0.1},
            "high_impact": {"urgency": 0.2, "importance": 0.6, "effort": 0.1, "dependency": 0.1},
            "deadline_driven": {"urgency": 0.6, "importance": 0.2, "effort": 0.1, "dependency": 0.1},
        }
        return presets.get(strategy, {"urgency": 0.4, "importance": 0.35, "effort": 0.15, "dependency": 0.1})

    # -------------------------
    # Task sanitization
    # -------------------------
    def sanitize_tasks(self, tasks):
        if not isinstance(tasks, list):
            self.errors.append("No valid tasks provided")
            return []

        sanitized = []
        seen = set()
        next_id = 1
        today = datetime.now().date()

        for idx, raw in enumerate(tasks):
            if not isinstance(raw, dict):
                self.errors.append(f"Task at index {idx} is not a dictionary, skipping")
                continue

            task = {}

            # ID
            try:
                task_id = int(raw.get("id", idx + 1))
            except:
                task_id = idx + 1
                self.errors.append(f"Task index {idx}: Invalid ID replaced with {task_id}")

            if task_id in seen:  # Fix duplicate ID
                while next_id in seen:
                    next_id += 1
                self.errors.append(f"Duplicate ID {task_id} reassigned to {next_id}")
                task_id = next_id

            seen.add(task_id)
            task["id"] = task_id

            # Title
            title = raw.get("title")
            if isinstance(title, str) and title.strip():
                task["title"] = title.strip()
            else:
                task["title"] = f"Task {task_id}"
                self.errors.append(f"Task {task_id}: Missing or invalid title replaced")

            # Due date
            due_raw = raw.get("due_date")
            task["due_date"] = None

            if isinstance(due_raw, str):
                try:
                    parsed = datetime.strptime(due_raw, "%Y-%m-%d").date()
                    if parsed < today:
                        self.errors.append(f"Task {task_id}: Due date {due_raw} is in the past")
                    task["due_date"] = due_raw
                except:
                    self.errors.append(f"Task {task_id}: Invalid due date '{due_raw}'")

            elif due_raw is not None:
                self.errors.append(f"Task {task_id}: Invalid due date type")

            # Hours
            try:
                hrs = float(raw.get("estimated_hours", 1.0))
                if hrs < 0:
                    hrs = 0
                    self.errors.append(f"Task {task_id}: Negative hours fixed")
                task["estimated_hours"] = hrs
            except:
                task["estimated_hours"] = 1.0
                self.errors.append(f"Task {task_id}: Invalid hours replaced")

            # Importance
            try:
                imp = float(raw.get("importance", 1.0))
                clamped = max(1.0, min(10.0, imp))
                if imp != clamped:
                    self.errors.append(f"Task {task_id}: Importance out of range, clamped")
                task["importance"] = clamped
            except:
                task["importance"] = 1.0
                self.errors.append(f"Task {task_id}: Invalid importance replaced")

            # Dependencies
            deps = raw.get("dependencies", [])
            if not isinstance(deps, list):
                self.errors.append(f"Task {task_id}: Dependencies not list, reset")
                deps = []

            cleaned_deps = []
            for d in deps:
                try:
                    cleaned_deps.append(int(d))
                except:
                    self.errors.append(f"Task {task_id}: Invalid dependency '{d}' skipped")

            task["dependencies"] = cleaned_deps
            sanitized.append(task)

        # Remove deps pointing to missing tasks
        valid = {t["id"] for t in sanitized}
        for t in sanitized:
            bad = [d for d in t["dependencies"] if d not in valid]
            if bad:
                t["dependencies"] = [d for d in t["dependencies"] if d in valid]
                self.errors.append(f"Task {t['id']}: Removed invalid dependencies {bad}")

        return sanitized

    # -------------------------
    # Cycle detection
    # -------------------------
    def detect_cycles_with_paths(self, tasks):
        graph = defaultdict(list)
        ids = {t["id"] for t in tasks}

        for t in tasks:
            for d in t["dependencies"]:
                if d in ids:
                    graph[t["id"]].append(d)

        visited = set()
        stack = []
        cycles = []

        def dfs(n):
            if n in stack:
                cycle = stack[stack.index(n):] + [n]
                if cycle not in cycles:
                    cycles.append(cycle)
                return
            if n in visited:
                return

            visited.add(n)
            stack.append(n)
            for nxt in graph[n]:
                dfs(nxt)
            stack.pop()

        for t in tasks:
            if t["id"] not in visited:
                dfs(t["id"])

        return cycles

    # -------------------------
    # Holidays
    # -------------------------
    def _ensure_holidays_for_year(self, year):
        if year in self._holiday_cache:
            return self._holiday_cache[year]

        dates = set()
        if self.holidays_available and _holidays_pkg is not None:
            try:
                for d in _holidays_pkg.country_holidays(self.country_code, years=year):
                    dates.add(d if not isinstance(d, datetime) else d.date())
            except:
                self.errors.append(f"Could not load holidays for {year}")

        self._holiday_cache[year] = dates
        return dates

    def _is_holiday(self, d):
        if not self.holidays_available or d is None:
            return False
        return d in self._ensure_holidays_for_year(d.year)

    # -------------------------
    # Working days
    # -------------------------
    def working_days_between(self, a, b):
        if a > b:
            return -self.working_days_between(b, a)

        count = 0
        cur = a
        while cur <= b:
            if cur.weekday() < 5 and not self._is_holiday(cur):
                count += 1
            cur += timedelta(days=1)
        return count

    # -------------------------
    # Urgency score
    # -------------------------
    def calculate_urgency(self, due_raw):
        if not due_raw:
            return 0

        try:
            due = datetime.strptime(due_raw, "%Y-%m-%d").date()
        except:
            return 0

        today = datetime.now().date()
        left = self.working_days_between(today, due) - 1

        if left < 0:
            return 40

        return max(0, 30 - left)

    # -------------------------
    # Effort score
    # -------------------------
    def calculate_effort_score(self, hrs):
        return 10 if hrs <= 0 else 10 / (hrs + 1)

    # -------------------------
    # Main scoring
    # -------------------------
    def score_task(self, task, dep_counts):
        u = self.calculate_urgency(task["due_date"])
        imp = task["importance"]
        eff = self.calculate_effort_score(task["estimated_hours"])
        dep = dep_counts.get(task["id"], 0) * 5
        w = self.weights

        total = w["urgency"] * u + w["importance"] * imp + w["effort"] * eff + w["dependency"] * dep

        # future penalty
        today = datetime.now().date()
        penalty_msg = "No future penalty"

        try:
            due = datetime.strptime(task["due_date"], "%Y-%m-%d").date() if task["due_date"] else None
        except:
            due = None

        if due:
            diff = (due - today).days
            if diff > 0:
                penalty = 1 / (1 + diff / 60)
                total *= penalty
                penalty_msg = "Future date penalty applied"

        explanation = [
            f"Urgency contributed {w['urgency'] * u:.2f}",
            f"Importance contributed {w['importance'] * imp:.2f}",
            f"Effort contributed {w['effort'] * eff:.2f}",
            f"Dependency contributed {w['dependency'] * dep:.2f}",
            penalty_msg
        ]

        return round(total, 2), explanation

    # -------------------------
    # Score all tasks
    # -------------------------
    def score_all(self, tasks):
        self.errors = []
        sanitized = self.sanitize_tasks(tasks)

        if not sanitized:
            return []

        cycles = self.detect_cycles_with_paths(sanitized)
        for c in cycles:
            self.errors.append("Circular dependency detected: " + " -> ".join(map(str, c)))

        dep_counts = defaultdict(int)
        for t in sanitized:
            for d in t["dependencies"]:
                dep_counts[d] += 1

        scored = []
        for t in sanitized:
            score, explanation = self.score_task(t, dep_counts)
            t["score"] = score
            t["explanation"] = explanation
            scored.append(t)

        return sorted(scored, key=lambda x: x["score"], reverse=True)

    def get_errors(self):
        return self.errors