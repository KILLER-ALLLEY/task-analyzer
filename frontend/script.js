const API_BASE = "http://127.0.0.1:8000/api/tasks";

const els = {
  form: document.getElementById("task-form"),
  title: document.getElementById("title"),
  due_date: document.getElementById("due_date"),
  estimated_hours: document.getElementById("estimated_hours"),
  importance: document.getElementById("importance"),
  dependencies: document.getElementById("dependencies"),
  task_id: document.getElementById("task_id"),
  addBtn: document.getElementById("add-task-btn"),
  clearBtn: document.getElementById("clear-list-btn"),
  bulkJson: document.getElementById("bulk-json"),
  strategy: document.getElementById("strategy"),
  analyzeBtn: document.getElementById("analyze-btn"),
  suggestBtn: document.getElementById("suggest-btn"),
  taskList: document.getElementById("task-list"),
  status: document.getElementById("status"),
  results: document.getElementById("results"),
  graphContainer: document.getElementById("graph-container"),
};

let localTasks = [];

function parseDependencies(text){
  if(!text) return [];
  return text.split(",").map(s => +s.trim()).filter(n => !Number.isNaN(n));
}

function setStatus(msg, isError=false){
  els.status.textContent = msg || "";
  els.status.style.color = isError ? "var(--danger)" : "var(--muted)";
}

function resetResults(){
  els.results.innerHTML = "";
  els.graphContainer.innerHTML = "";
}

function renderTaskList(){
  els.taskList.innerHTML = "";
  if(localTasks.length === 0){
    const li = document.createElement("li");
    li.className = "small";
    li.textContent = "No tasks added locally yet.";
    els.taskList.appendChild(li);
    return;
  }
  localTasks.forEach((t, idx) => {
    const li = document.createElement("li");
    const left = document.createElement("div");
    left.innerHTML = `<div style="font-weight:700">${t.title || "(no title)"}</div><div class="small">${t.due_date ? t.due_date : "no due date"} • ${t.estimated_hours ?? "?"}h • imp ${t.importance ?? "?"}</div>`;
    const right = document.createElement("div");
    const del = document.createElement("button");
    del.style.background = "#ef4444";
    del.textContent = "Remove";
    del.onclick = () => { localTasks.splice(idx,1); renderTaskList(); };
    right.appendChild(del);
    li.appendChild(left);
    li.appendChild(right);
    els.taskList.appendChild(li);
  });
}

els.addBtn.addEventListener("click", () => {
  const title = els.title.value.trim();
  if(!title){ setStatus("Task title is required", true); return; }
  const task = {
    title,
    due_date: els.due_date.value || null,
    estimated_hours: els.estimated_hours.value ? Number(els.estimated_hours.value) : null,
    importance: els.importance.value ? Number(els.importance.value) : null,
    dependencies: parseDependencies(els.dependencies.value),
    id: els.task_id.value ? Number(els.task_id.value) : undefined
  };
  localTasks.push(task);
  renderTaskList();
  setStatus("Added task to local list");
  els.form.reset();
});

els.clearBtn.addEventListener("click", () => {
  localTasks = [];
  renderTaskList();
  setStatus("Cleared task list");
});

function buildPayload(){
  const raw = els.bulkJson.value.trim();
  if(raw){
    try{
      const parsed = JSON.parse(raw);
      if(!Array.isArray(parsed)){ setStatus("Bulk JSON must be an array of tasks", true); return null; }
      return parsed;
    }catch(e){
      setStatus("Invalid JSON in bulk input", true);
      return null;
    }
  }
  if(localTasks.length === 0){ setStatus("No tasks to analyze. Add tasks or paste JSON.", true); return null; }
  return localTasks.map((t,i) => {
    const copy = {...t};
    if(copy.id === undefined) copy.id = i+1;
    copy.dependencies = Array.isArray(copy.dependencies) ? copy.dependencies : [];
    return copy;
  });
}

function scoreCategory(score){
  if(score >= 20) return "high";
  if(score >= 10) return "medium";
  return "low";
}

function renderResults(tasks){
  resetResults();
  if(!Array.isArray(tasks) || tasks.length === 0){ els.results.textContent = "No results"; return; }
  tasks.forEach(t => {
    const div = document.createElement("div");
    div.className = "result-card";
    const cat = scoreCategory(t.score || 0);
    const ribbon = document.createElement("div");
    ribbon.className = "ribbon";
    ribbon.style.background = cat === "high" ? "#f8d7da" : cat === "medium" ? "#fff6e0" : "#e6fff0";
    div.appendChild(ribbon);
    const main = document.createElement("div");
    main.className = "result-main";
    const title = document.createElement("div");
    title.className = "result-title";
    title.textContent = `${t.title || "(no title)"}  —  ${t.score ?? "0"}`;
    const meta = document.createElement("div");
    meta.className = "result-meta";
    meta.textContent = `Due: ${t.due_date ?? "none"} • Effort: ${t.estimated_hours ?? "?"}h • Importance: ${t.importance ?? "?"}`;
    const explain = document.createElement("div");
    explain.className = "result-explain";
    explain.innerHTML = (t.explanation ? "<strong>Score breakdown</strong><br>" + t.explanation.join("<br>") : "") +
                        (t.reason ? `<br><br><strong>Why suggested</strong><br>${t.reason}` : "");
    main.appendChild(title);
    main.appendChild(meta);
    main.appendChild(explain);
    div.appendChild(main);
    els.results.appendChild(div);
  });
}

function renderDependencyGraph(tasks, cycles = []){
  if(!tasks || tasks.length === 0){ els.graphContainer.innerHTML = ""; return; }
  const cycleNodes = new Set(cycles.flat ? cycles.flat() : [].concat(...cycles));
  let graph = "graph TD;\n";
  tasks.forEach(t => {
    const id = t.id;
    const label = (t.title || `Task ${id}`).replace(/"/g, "'");
    if(cycleNodes.has(id)){
      graph += `${id}["${label} (ID ${id})":::cycle]\n`;
    } else {
      graph += `${id}["${label} (ID ${id})"]\n`;
    }
    (t.dependencies || []).forEach(dep => {
      graph += `${id} --> ${dep}\n`;
    });
  });
  els.graphContainer.innerHTML = `<div class="mermaid">${graph}</div>`;
  if(window.mermaid){ mermaid.init(undefined, document.querySelectorAll(".mermaid")); }
}

async function callAnalyze(){
  setStatus("");
  resetResults();
  const payload = buildPayload();
  if(!payload) return;
  const strategy = els.strategy.value;
  els.analyzeBtn.disabled = true;
  els.suggestBtn.disabled = true;
  setStatus("Analyzing...");
  try{
    const res = await fetch(`${API_BASE}/analyze/?strategy=${encodeURIComponent(strategy)}`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const json = await res.json().catch(()=>null);
    if(!res.ok){
      // if cycles returned, render graph with cycles marked
      if(json?.cycles){
        renderDependencyGraph(payload, json.cycles);
      }
      setStatus(json?.error || json?.detail || `Server error ${res.status}`, true);
      return;
    }
    renderResults(json);
    renderDependencyGraph(json);
    setStatus("Analysis complete");
  }catch(err){
    setStatus("Network error: " + err.message, true);
  }finally{
    els.analyzeBtn.disabled = false;
    els.suggestBtn.disabled = false;
  }
}

async function callSuggest(){
  setStatus("");
  resetResults();
  const payload = buildPayload();
  if(!payload) return;
  els.analyzeBtn.disabled = true;
  els.suggestBtn.disabled = true;
  setStatus("Computing suggestions...");
  try{
    const res = await fetch(`${API_BASE}/suggest/`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const json = await res.json().catch(()=>null);
    if(!res.ok){
      if(json?.cycles){ renderDependencyGraph(payload, json.cycles); }
      setStatus(json?.error || json?.detail || `Server error ${res.status}`, true);
      return;
    }
    renderResults(json);
    renderDependencyGraph(json);
    setStatus("Top suggestions ready");
  }catch(err){
    setStatus("Network error: " + err.message, true);
  }finally{
    els.analyzeBtn.disabled = false;
    els.suggestBtn.disabled = false;
  }
}

els.analyzeBtn.addEventListener("click", callAnalyze);
els.suggestBtn.addEventListener("click", callSuggest);

renderTaskList();
setStatus("Ready");
