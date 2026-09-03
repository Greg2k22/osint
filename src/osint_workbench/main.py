import json
from pathlib import Path
import uuid
from pydantic import BaseModel
from neo4j import GraphDatabase
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from osint_workbench.api.runs import router as runs_router

app = FastAPI(title='OSINT Workbench', version='0.1.0')
app.include_router(runs_router)

@app.get('/health')
def health():
    return {'status': 'ok'}


@app.get("/ui", response_class=HTMLResponse)
def ui_dashboard():
    return """
<!doctype html>
<html lang="pl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>OSINT Workbench</title>
  <style>
    * { box-sizing: border-box; }

    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 0;
      background: #111827;
      color: #e5e7eb;
    }

    header {
      padding: 22px 32px;
      border-bottom: 1px solid #374151;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    main {
      padding: 32px;
      max-width: 1400px;
      margin: 0 auto;
    }

    h1 { margin: 0; }

    .status {
      color: #86efac;
      font-weight: 700;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }

    .card {
      background: #1f2937;
      border: 1px solid #374151;
      border-radius: 12px;
      padding: 18px;
    }

    .card h2 {
      margin-top: 0;
      font-size: 18px;
    }

    .toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin: 22px 0 12px;
    }

    button {
      background: #2563eb;
      border: 0;
      color: white;
      padding: 9px 14px;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 600;
    }

    button:hover {
      background: #1d4ed8;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      background: #1f2937;
      border: 1px solid #374151;
      border-radius: 12px;
      overflow: hidden;
    }

    th, td {
      padding: 12px 14px;
      text-align: left;
      border-bottom: 1px solid #374151;
      vertical-align: top;
    }

    th {
      color: #93c5fd;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: .04em;
    }

    td {
      font-size: 14px;
    }

    tr:last-child td {
      border-bottom: 0;
    }

    .badge {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 999px;
      background: #374151;
      font-size: 12px;
      font-weight: 700;
    }

    .muted {
      color: #9ca3af;
    }

    .path {
      max-width: 520px;
      overflow-wrap: anywhere;
      color: #9ca3af;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 12px;
    }

    #case-error {
      display: none;
      color: #fca5a5;
      margin: 12px 0;
    }
  
    .scan-form {
      display: grid;
      grid-template-columns: 180px 1fr 160px 220px;
      gap: 12px;
      align-items: end;
    }

    .field {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    label {
      font-size: 13px;
      color: #9ca3af;
    }

    input, select {
      width: 100%;
      background: #111827;
      color: #e5e7eb;
      border: 1px solid #4b5563;
      border-radius: 8px;
      padding: 10px 12px;
    }

    .check {
      display: flex;
      align-items: center;
      gap: 8px;
      min-height: 40px;
    }

    .check input {
      width: auto;
    }

    .scan-result {
      margin-top: 12px;
      min-height: 22px;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 13px;
    }

    @media (max-width: 900px) {
      .scan-form {
        grid-template-columns: 1fr;
      }
    }

  </style>
</head>
<body>
  <header>
    <div>
      <h1>OSINT Workbench</h1>
      <div class="muted">DOMAIN / PERSON / EMAIL / GRAPH</div>
    </div>
    <div class="status">Backend działa</div>
  </header>

  <main>
    <div class="grid">
      <section class="card">
        <h2>DOMAIN</h2>
        <p>BBOT, Subfinder, theHarvester, httpx.</p>
      </section>

      <section class="card">
        <h2>PERSON</h2>
        <p>Maigret, Sherlock.</p>
      </section>

      <section class="card">
        <h2>EMAIL</h2>
        <p>Holehe.</p>
      </section>

      <section class="card">
        <h2>GRAPH</h2>
        <p>Neo4j, MEDIUM/HIGH.</p>
      </section>
    </div>

    <section class="card" style="margin-bottom:28px">
      <h2>Nowa analiza</h2>

      <form id="scan-form" class="scan-form" onsubmit="submitScan(event)">
        <div class="field">
          <label for="scan-type">Typ</label>
          <select id="scan-type" onchange="updateScanMode()">
            <option value="DOMAIN">DOMAIN</option>
            <option value="PERSON">PERSON</option>
            <option value="EMAIL">EMAIL</option>
          </select>
        </div>

        <div class="field">
          <label for="scan-target">Cel</label>
          <input
            id="scan-target"
            type="text"
            autocomplete="off"
            placeholder="example.org"
            required>
        </div>

        <div class="field">
          <label for="scan-mode">Tryb</label>
          <select id="scan-mode" onchange="updateAuthorization()">
            <option value="PASSIVE">PASSIVE</option>
            <option value="ACTIVE">ACTIVE</option>
          </select>
        </div>

        <div>
          <label class="check">
            <input id="scan-authorized" type="checkbox" disabled>
            Mam autoryzację do ACTIVE
          </label>
          <button id="scan-submit" type="submit">Uruchom analizę</button>
        </div>
      </form>

      <div id="scan-result" class="scan-result muted"></div>
    </section>


    <div class="toolbar">
      <div>
        <h2 style="margin:0">Sprawy</h2>
        <div class="muted" id="case-summary">Ładowanie...</div>
      </div>
      <button onclick="refreshAll()">Odśwież</button>
    </div>

    <div id="case-error"></div>

    <div id="case-detail" class="card" style="display:none; margin-bottom:24px">
      <div class="toolbar" style="margin-top:0">
        <div>
          <h2 style="margin:0">Szczegóły sprawy</h2>
          <div class="muted" id="case-detail-title"></div>
        </div>
        <button onclick="closeCase()">Zamknij</button>
      </div>

      <div id="case-detail-content"></div>
    </div>


    <div class="toolbar" style="margin-top:32px">
      <div>
        <h2 style="margin:0">Zadania</h2>
        <div class="muted" id="job-summary">Ładowanie...</div>
      </div>
    </div>

    <div id="job-error"></div>

    <table id="job-table">
      <thead>
        <tr>
          <th>Status</th>
          <th>Typ</th>
          <th>Cel</th>
          <th>Job ID</th>
          <th>Tryb</th>
        </tr>
      </thead>
      <tbody id="job-body">
        <tr>
          <td colspan="5" class="muted">Ładowanie danych...</td>
        </tr>
      </tbody>
    </table>


    <table id="case-table">
      <thead>
        <tr>
          <th>Typ</th>
          <th>Case ID</th>
          <th>Obiekty</th>
          <th>Ścieżka</th>
        </tr>
      </thead>
      <tbody id="case-body">
        <tr>
          <td colspan="4" class="muted">Ładowanie danych...</td>
        </tr>
      </tbody>
    </table>
  </main>

  <script>
    function esc(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    async function loadCases() {
      const body = document.getElementById("case-body");
      const summary = document.getElementById("case-summary");
      const error = document.getElementById("case-error");

      error.style.display = "none";
      body.innerHTML =
        '<tr><td colspan="4" class="muted">Ładowanie danych...</td></tr>';

      try {
        const response = await fetch("/api/cases", {
          headers: { "Accept": "application/json" }
        });

        if (!response.ok) {
          throw new Error("HTTP " + response.status);
        }

        const data = await response.json();
        const cases = Array.isArray(data.cases) ? data.cases : [];

        summary.textContent = "Liczba spraw: " + cases.length;

        if (cases.length === 0) {
          body.innerHTML =
            '<tr><td colspan="4" class="muted">Brak spraw.</td></tr>';
          return;
        }

        body.innerHTML = cases.map(item => `
          <tr>
            <td><span class="badge">${esc(item.type || "UNKNOWN")}</span></td>
            <td>
              <a href="#"
                 onclick="showCase('${esc(item.id)}'); return false;"
                 style="color:#93c5fd">
                ${esc(item.id)}
              </a>
            </td>
            <td>${esc(item.observed)}</td>
            <td class="path">${esc(item.path)}</td>
          </tr>
        `).join("");

      } catch (err) {
        summary.textContent = "Błąd ładowania";
        error.textContent = "Nie udało się pobrać /api/cases: " + err.message;
        error.style.display = "block";
        body.innerHTML =
          '<tr><td colspan="4" class="muted">Brak danych.</td></tr>';
      }
    }


    function nodeValue(node) {
      return node.name || node.value || node.url ||
             node.address || JSON.stringify(node);
    }

    function closeCase() {
      document.getElementById("case-detail").style.display = "none";
    }

    async function showCase(caseId) {
      const box = document.getElementById("case-detail");
      const title = document.getElementById("case-detail-title");
      const content = document.getElementById("case-detail-content");

      box.style.display = "block";
      title.textContent = caseId;
      content.innerHTML =
        '<div class="muted">Ładowanie...</div>';

      try {
        const response = await fetch(
          "/api/cases/" + encodeURIComponent(caseId)
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || ("HTTP " + response.status));
        }

        const observed = Array.isArray(data.observed)
          ? data.observed : [];

        const relations = Array.isArray(data.relations)
          ? data.relations : [];

        let html = `
          <p>
            <strong>Typ:</strong> ${esc(data.case.type)}
            &nbsp;&nbsp;
            <strong>Obiekty:</strong> ${observed.length}
            &nbsp;&nbsp;
            <strong>Relacje:</strong> ${relations.length}
          </p>
        `;

        if (observed.length) {
          html += `
            <table>
              <thead>
                <tr>
                  <th>Typ</th>
                  <th>Wartość</th>
                </tr>
              </thead>
              <tbody>
          `;

          html += observed.map(item => `
            <tr>
              <td>
                <span class="badge">
                  ${esc((item.labels || []).join(","))}
                </span>
              </td>
              <td class="path">
                ${esc(nodeValue(item.node || {}))}
              </td>
            </tr>
          `).join("");

          html += `
              </tbody>
            </table>
          `;
        }

        if (relations.length) {
          html += `
            <h3 style="margin-top:24px">Relacje</h3>
            <table>
              <thead>
                <tr>
                  <th>Od</th>
                  <th>Relacja</th>
                  <th>Do</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody>
          `;

          html += relations.map(item => `
            <tr>
              <td class="path">
                ${esc(nodeValue(item.from || {}))}
              </td>
              <td>${esc(item.type)}</td>
              <td class="path">
                ${esc(nodeValue(item.to || {}))}
              </td>
              <td>
                ${esc((item.relation || {}).confidence || "")}
              </td>
            </tr>
          `).join("");

          html += `
              </tbody>
            </table>
          `;
        }

        content.innerHTML = html;

      } catch (err) {
        content.innerHTML =
          '<div style="color:#fca5a5">Błąd: ' +
          esc(err.message) +
          '</div>';
      }
    }

    async function loadJobs() {
      const body = document.getElementById("job-body");
      const summary = document.getElementById("job-summary");
      const error = document.getElementById("job-error");

      error.style.display = "none";
      body.innerHTML =
        '<tr><td colspan="5" class="muted">Ładowanie danych...</td></tr>';

      try {
        const response = await fetch("/api/jobs", {
          headers: { "Accept": "application/json" }
        });

        if (!response.ok) {
          throw new Error("HTTP " + response.status);
        }

        const data = await response.json();
        const jobs = Array.isArray(data.jobs) ? data.jobs : [];

        summary.textContent = "Liczba zadań: " + jobs.length;

        if (jobs.length === 0) {
          body.innerHTML =
            '<tr><td colspan="5" class="muted">Brak zadań.</td></tr>';
          return;
        }

        body.innerHTML = jobs.map(item => `
          <tr>
            <td><span class="badge">${esc(item.status || item.queue || "UNKNOWN")}</span></td>
            <td>${esc(item.type)}</td>
            <td>${esc(item.target)}</td>
            <td class="path">${esc(item.id)}</td>
            <td>${item.active ? "ACTIVE" : "PASSIVE"}</td>
          </tr>
        `).join("");

      } catch (err) {
        summary.textContent = "Błąd ładowania";
        error.textContent = "Nie udało się pobrać /api/jobs: " + err.message;
        error.style.display = "block";
        body.innerHTML =
          '<tr><td colspan="5" class="muted">Brak danych.</td></tr>';
      }
    }

    function updateScanMode() {
      const type = document.getElementById("scan-type").value;
      const mode = document.getElementById("scan-mode");

      if (type !== "DOMAIN") {
        mode.value = "PASSIVE";
        mode.disabled = true;
      } else {
        mode.disabled = false;
      }

      updateAuthorization();
    }

    function updateAuthorization() {
      const type = document.getElementById("scan-type").value;
      const mode = document.getElementById("scan-mode").value;
      const checkbox = document.getElementById("scan-authorized");

      const active = type === "DOMAIN" && mode === "ACTIVE";

      checkbox.disabled = !active;

      if (!active) {
        checkbox.checked = false;
      }
    }

    async function submitScan(event) {
      event.preventDefault();

      const type = document.getElementById("scan-type").value;
      const target = document.getElementById("scan-target").value.trim();
      const mode = document.getElementById("scan-mode").value;
      const authorized = document.getElementById("scan-authorized").checked;
      const result = document.getElementById("scan-result");
      const button = document.getElementById("scan-submit");

      const active = type === "DOMAIN" && mode === "ACTIVE";

      if (!target) {
        result.textContent = "Podaj cel analizy.";
        return;
      }

      if (active && !authorized) {
        result.textContent = "ACTIVE wymaga potwierdzenia autoryzacji.";
        return;
      }

      button.disabled = true;
      result.textContent = "Dodawanie zadania...";

      try {
        const response = await fetch("/api/scan", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
          },
          body: JSON.stringify({
            type: type,
            target: target,
            active: active,
            authorized: authorized
          })
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || ("HTTP " + response.status));
        }

        result.textContent =
          "PENDING | " + data.type + " | " + data.target +
          " | Job: " + data.id;

        document.getElementById("scan-target").value = "";

        updateScanMode();
    refreshAll();
    setInterval(refreshAll, 5000);

      } catch (err) {
        result.textContent = "Błąd: " + err.message;
      } finally {
        button.disabled = false;
      }
    }


    function refreshAll() {
      loadCases();
      loadJobs();
    }

    refreshAll();
  </script>
</body>
</html>
"""


@app.get("/api/cases")
def api_cases():
    auth = os.environ.get("NEO4J_AUTH", "")
    uri = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")

    if "/" not in auth:
        raise HTTPException(
            status_code=503,
            detail="Neo4j credentials are not configured"
        )

    user, password = auth.split("/", 1)

    try:
        driver = GraphDatabase.driver(
            uri,
            auth=(user, password)
        )

        with driver:
            with driver.session(database="neo4j") as session:
                rows = session.run("""
                    MATCH (c:Case)
                    OPTIONAL MATCH (x)-[:OBSERVED_IN]->(c)
                    RETURN
                        c.id AS id,
                        c.type AS type,
                        c.path AS path,
                        count(DISTINCT x) AS observed
                    ORDER BY c.id DESC
                    LIMIT 100
                """)

                return {
                    "cases": [
                        {
                            "id": row["id"],
                            "type": row["type"],
                            "path": row["path"],
                            "observed": row["observed"],
                        }
                        for row in rows
                    ]
                }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Neo4j unavailable: {type(exc).__name__}"
        ) from exc


class ScanRequest(BaseModel):
    type: str
    target: str
    active: bool = False
    authorized: bool = False



@app.get("/api/cases/{case_id}")
def api_case_detail(case_id: str):
    auth = os.environ.get("NEO4J_AUTH", "")
    uri = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")

    if "/" not in auth:
        raise HTTPException(
            status_code=503,
            detail="Neo4j credentials are not configured"
        )

    user, password = auth.split("/", 1)

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))

        with driver:
            with driver.session(database="neo4j") as session:
                case_row = session.run(
                    """
                    MATCH (c:Case {id: $case_id})
                    RETURN c.id AS id, c.type AS type, c.path AS path
                    """,
                    case_id=case_id
                ).single()

                if not case_row:
                    raise HTTPException(
                        status_code=404,
                        detail="Case not found"
                    )

                observed_rows = session.run(
                    """
                    MATCH (n)-[:OBSERVED_IN]->(c:Case {id: $case_id})
                    RETURN
                        labels(n) AS labels,
                        properties(n) AS node
                    ORDER BY labels(n)
                    """,
                    case_id=case_id
                )

                observed = [
                    {
                        "labels": row["labels"],
                        "node": row["node"],
                    }
                    for row in observed_rows
                ]

                relation_rows = session.run(
                    """
                    MATCH (a)-[r]->(b)
                    WHERE r.case_id = $case_id
                    RETURN
                        labels(a) AS from_labels,
                        properties(a) AS from_node,
                        type(r) AS relation_type,
                        properties(r) AS relation,
                        labels(b) AS to_labels,
                        properties(b) AS to_node
                    ORDER BY relation_type
                    """,
                    case_id=case_id
                )

                relations = [
                    {
                        "from_labels": row["from_labels"],
                        "from": row["from_node"],
                        "type": row["relation_type"],
                        "relation": row["relation"],
                        "to_labels": row["to_labels"],
                        "to": row["to_node"],
                    }
                    for row in relation_rows
                ]

                return {
                    "case": {
                        "id": case_row["id"],
                        "type": case_row["type"],
                        "path": case_row["path"],
                    },
                    "observed": observed,
                    "relations": relations,
                }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Neo4j unavailable: {type(exc).__name__}"
        ) from exc


@app.post("/api/scan", status_code=202)
def api_scan(request: ScanRequest):
    scan_type = request.type.upper().strip()
    target = request.target.strip()

    if scan_type not in {"DOMAIN", "PERSON", "EMAIL"}:
        raise HTTPException(status_code=400, detail="Unsupported scan type")

    if not target:
        raise HTTPException(status_code=400, detail="Target is required")

    if request.active and not request.authorized:
        raise HTTPException(
            status_code=403,
            detail="ACTIVE mode requires explicit authorization"
        )

    if request.active and scan_type != "DOMAIN":
        raise HTTPException(
            status_code=400,
            detail="ACTIVE mode is currently supported only for DOMAIN"
        )

    job_id = uuid.uuid4().hex
    jobs = Path("/data/jobs/pending")
    jobs.mkdir(parents=True, exist_ok=True)

    payload = {
        "id": job_id,
        "type": scan_type,
        "target": target,
        "active": request.active,
        "authorized": request.authorized,
        "status": "PENDING",
    }

    tmp = jobs / f".{job_id}.tmp"
    dst = jobs / f"{job_id}.json"

    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2)
    )
    tmp.replace(dst)

    return payload


@app.get("/api/jobs")
def api_jobs():
    root = Path("/data/jobs")
    result = []

    for status in ("pending", "running", "done", "failed"):
        folder = root / status
        if not folder.exists():
            continue

        for item in sorted(folder.glob("*.json"), reverse=True):
            try:
                payload = json.loads(item.read_text())
            except Exception:
                continue

            payload["queue"] = status.upper()
            payload["file"] = item.name
            result.append(payload)

    return {
        "jobs": result
    }
