// Frontend-only configuration. Set window.FAIRAID_API_BASE before loading this script
// when the Django API runs on another machine or port.
const API_BASE = (window.FAIRAID_API_BASE || "http://localhost:8000").replace(
  /\/$/,
  "",
);
const library = [
  {
    name: "Development Fund Bursary Scheme",
    type: ["Bursary"],
    funder: "Ministry (Development Fund)",
    description: "Undergraduate funding for recognised qualifications.",
    criteria:
      "Namibian citizenship, academic results and supporting documentation. Refer to the official call.",
  },
  {
    name: "Arts Council of Namibia Bursary",
    type: ["Bursary"],
    funder: "Arts Council of Namibia",
    description: "Arts, culture and creative fields.",
    criteria: "Namibian citizenship, academic results and motivation letter.",
  },
  {
    name: "Bank of Namibia Bursary Programme",
    type: ["Bursary"],
    funder: "Bank of Namibia",
    description:
      "Selected economics, data science, AI and information systems fields.",
    criteria:
      "Strong academic performance and field restrictions. Verify the current intake.",
  },
  {
    name: "NamibRe Bursary",
    type: ["Bursary"],
    funder: "NamibRe",
    description:
      "Actuarial science, engineering, finance, AI-focused IT and other fields.",
    criteria: "Namibian citizenship and qualifying tertiary study.",
  },
  {
    name: "NamPower Bursary",
    type: ["Bursary"],
    funder: "NamPower",
    description: "Engineering and technical fields.",
    criteria:
      "Namibian citizenship, academic qualifications and provisional tertiary acceptance. Verify the current intake.",
  },
  {
    name: "NAMDIA Foundation Bursary",
    type: ["Bursary"],
    funder: "NAMDIA",
    description: "Multiple fields, with preferences for some study areas.",
    criteria:
      "Previous published requirements included full-time study and age restrictions. Verify the current call.",
  },
  {
    name: "NSFAF Loans and Grants",
    type: ["Loan", "Grant"],
    funder: "NSFAF",
    description:
      "Government student funding with different loan and grant routes.",
    criteria:
      "Eligibility and funding type depend on the programme. A loan must be repaid.",
  },
  {
    name: "DAAD In-Country / In-Region PhD Scholarship at NUST",
    type: ["Scholarship"],
    funder: "DAAD",
    description:
      "PhD Computer Science scholarship at NUST; the documented call was from 2025.",
    criteria:
      "Postgraduate admission and academic requirements. Check for a new call.",
  },
  {
    name: "Standard Bank Student Loan",
    type: ["Loan"],
    funder: "Standard Bank Namibia",
    description: "Student financing subject to credit assessment.",
    criteria:
      "Bank lending and surety requirements apply. FairAid cannot assess bank credit approval.",
  },
];
let demoMode = false,
  demoHistory = [];
let accessToken = null,
  refreshToken = null,
  currentRunId = null,
  currentResults = [],
  activeScheme = null,
  apiSchemes = [],
  signedIn = false,
  refreshInProgress = null;
const $ = (id) => document.getElementById(id),
  nav = $("navigation");
$("menu-toggle").addEventListener("click", () => {
  let open = nav.classList.toggle("open");
  $("menu-toggle").setAttribute("aria-expanded", String(open));
});
function route() {
  let page = location.hash.slice(1) || "home";
  if (!$(page)?.classList.contains("page")) page = "home";
  document.querySelectorAll(".page").forEach((e) => (e.hidden = e.id !== page));
  nav.classList.remove("open");
  $("menu-toggle").setAttribute("aria-expanded", "false");
  document
    .querySelectorAll(".navigation a[data-route]")
    .forEach((a) =>
      a.setAttribute(
        "aria-current",
        a.dataset.route === page ? "page" : "false",
      ),
    );
  window.scrollTo(0, 0);
  if (page === "screen") renderScreenGate();
  if (page === "history") loadHistory();
  if (page === "explore") {
    renderSchemes();
    if (!apiSchemes.length && !demoMode) loadApiSchemes();
  }
}
window.addEventListener("hashchange", route);
function updateAuth() {
  document
    .querySelectorAll(".signed-only")
    .forEach((el) => (el.hidden = !signedIn));
  document
    .querySelectorAll(".sign-in-link,.signup-link")
    .forEach((el) => (el.hidden = signedIn));
  renderScreenGate();
}
function renderScreenGate() {
  $("screen-gate").hidden = signedIn;
  $("screen-form").hidden = !signedIn;
}
async function request(
  path,
  {
    method = "GET",
    body = null,
    auth = false,
    form = false,
    retry = true,
  } = {},
) {
  const headers = {};
  if (body !== null)
    headers["Content-Type"] = form
      ? "application/x-www-form-urlencoded"
      : "application/json";
  if (auth) {
    if (!accessToken) throw Error("Please sign in first.");
    headers.Authorization = "Bearer " + accessToken;
  }
  let res;
  try {
    res = await fetch(API_BASE + path, {
      method,
      headers,
      body:
        body === null
          ? undefined
          : form
            ? new URLSearchParams(body)
            : JSON.stringify(body),
    });
  } catch {
    throw Error(
      "Cannot connect to FairAid. Check that the Django API is running and reachable from this device. If it is running, ask the backend developer to allow this website origin (CORS).",
    );
  }
  if (res.status === 401 && auth && retry && refreshToken) {
    try {
      await refreshSession();
      return request(path, { method, body, auth, form, retry: false });
    } catch {
      signOut();
      throw Error("Your session has expired. Please sign in again.");
    }
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = data?.detail;
    throw Error(
      typeof detail === "string"
        ? detail
        : data && typeof data === "object"
          ? Object.entries(data)
              .map(
                ([k, v]) =>
                  k +
                  ": " +
                  (Array.isArray(v) ? v.join(", ") : JSON.stringify(v)),
              )
              .join("; ")
          : "Request failed (" + res.status + ")",
    );
  }
  return data;
}
async function refreshSession() {
  if (!refreshInProgress)
    refreshInProgress = request("/api/auth/refresh", {
      method: "POST",
      body: { refresh_token: refreshToken },
    })
      .then((d) => {
        accessToken = d.access_token;
        refreshToken = d.refresh_token;
      })
      .finally(() => (refreshInProgress = null));
  return refreshInProgress;
}
function signOut() {
  demoMode = false;
  demoHistory = [];
  accessToken = null;
  refreshToken = null;
  signedIn = false;
  currentRunId = null;
  currentResults = [];
  updateAuth();
  location.hash = "home";
}
$("signout").addEventListener("click", async () => {
  try {
    if (accessToken)
      await request("/api/auth/logout", {
        method: "POST",
        auth: true,
        body: { refresh_token: refreshToken },
      });
  } catch {}
  signOut();
});
for (const kind of ["signin", "signup"]) {
  $(kind + "-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const f = e.currentTarget,
      msg = f.querySelector(".form-message"),
      btn = f.querySelector("button"),
      v = Object.fromEntries(new FormData(f));
    btn.disabled = true;
    msg.textContent = "Connecting…";
    try {
      if (kind === "signup") {
        await request("/api/auth/signup", { method: "POST", body: v });
        msg.textContent = "";
        msg.className = "form-message";
        $("signin-form").reset();
        location.hash = "signin";
      } else {
        const d = await request("/api/auth/login", {
          method: "POST",
          form: true,
          body: { username: v.email, password: v.password },
        });
        accessToken = d.access_token;
        refreshToken = d.refresh_token;
        signedIn = true;
        updateAuth();
        await loadApiSchemes();
        location.hash = "screen";
        msg.textContent = "";
      }
    } catch (err) {
      msg.className = "form-message error";
      msg.textContent = err.message;
    } finally {
      btn.disabled = false;
    }
  });
}
async function loadApiSchemes() {
  if (demoMode) {
    apiSchemes = demoSchemes;
    populateFields();
    renderSchemes();
    return;
  }
  try {
    const data = await request("/api/schemes");
    apiSchemes = Array.isArray(data) ? data : [];
    populateFields();
    renderSchemes();
  } catch (err) {
    apiSchemes = [];
    populateFields();
    renderSchemes();
    console.warn(err.message);
  }
}
function isScreenable(s) {
  return (
    !demoMode &&
    apiSchemes.some(
      (a) => a.name.trim().toLowerCase() === s.name.trim().toLowerCase(),
    )
  );
}
// Keep the existing informational funding library and append registered API schemes.
// The backend is authoritative for schemes evaluated by the decision tree.
function displayedSchemes() {
  const entries = [...library];
  const known = new Set(entries.map((s) => s.name.trim().toLowerCase()));
  for (const scheme of apiSchemes) {
    const name = String(scheme.name || "").trim();
    if (!name || known.has(name.toLowerCase())) continue;
    known.add(name.toLowerCase());
    const types = /scholarship/i.test(name)
      ? ["Scholarship"]
      : /grant|fund/i.test(name)
        ? ["Grant"]
        : ["Bursary"];
    const requirements = [];
    if (scheme.min_nqf_level != null)
      requirements.push("Minimum NQF level: " + scheme.min_nqf_level);
    if (scheme.max_household_income != null)
      requirements.push(
        "Maximum annual household income: N$" +
          Number(scheme.max_household_income).toLocaleString("en-NA"),
      );
    if (scheme.eligible_fields_of_study?.length)
      requirements.push(
        "Fields: " + scheme.eligible_fields_of_study.join(", "),
      );
    if (scheme.eligible_regions?.length)
      requirements.push("Regions: " + scheme.eligible_regions.join(", "));
    if (scheme.requires_disability)
      requirements.push("Recognised disability required");
    entries.push({
      name,
      type: types,
      funder: "Registered funding scheme",
      description:
        scheme.description ||
        "Funding scheme registered for FairAid pre-screening.",
      criteria:
        requirements.join(". ") ||
        "Refer to the registered scheme requirements.",
      registered: true,
    });
  }
  return entries;
}
const grid = $("scheme-grid");
let filter = "All";
function renderSchemes() {
  grid.replaceChildren();
  const filtered = displayedSchemes().filter(
    (s) => filter === "All" || s.type.includes(filter),
  );
  filtered.forEach((s) => {
    const card = document.createElement("article");
    card.className = "scheme-card";
    const tag = document.createElement("span");
    tag.className = "scheme-type";
    tag.textContent = s.type.join(" / ");
    const h = document.createElement("h2");
    h.textContent = s.name;
    const funder = document.createElement("p");
    funder.textContent = s.funder;
    const desc = document.createElement("p");
    desc.textContent = s.description;
    const btn = document.createElement("button");
    btn.className = "card-link";
    btn.textContent = "View details →";
    btn.addEventListener("click", () => {
      activeScheme = s;
      showDetail();
      location.hash = "detail";
    });
    card.append(tag, h, funder, desc, btn);
    grid.append(card);
  });
}
document.querySelectorAll(".filter").forEach((b) =>
  b.addEventListener("click", () => {
    filter = b.dataset.filter;
    document.querySelectorAll(".filter").forEach((x) => {
      x.classList.toggle("active", x === b);
      x.setAttribute("aria-pressed", String(x === b));
    });
    renderSchemes();
  }),
);
function showDetail() {
  const d = $("scheme-detail");
  d.replaceChildren();
  if (!activeScheme) return;
  const h = document.createElement("h1");
  h.textContent = activeScheme.name;
  const funder = document.createElement("p");
  funder.textContent = "Provider: " + activeScheme.funder;
  const desc = document.createElement("p");
  desc.textContent = activeScheme.description;
  const h2 = document.createElement("h2");
  h2.textContent = "Funding requirements";
  const criteria = document.createElement("p");
  criteria.textContent = activeScheme.criteria;
  const notice = document.createElement("p");
  notice.className = "notice";
  notice.textContent =
    "This page is for exploring funding information, not an individual eligibility assessment. Requirements and application dates may change. Confirm current details with the official provider. FairAid does not apply or award funding.";
  d.append(h, funder, desc, h2, criteria, notice);
}
const regions = [
  "Erongo",
  "Hardap",
  "ǁKharas",
  "Kavango East",
  "Kavango West",
  "Khomas",
  "Kunene",
  "Ohangwena",
  "Omaheke",
  "Omusati",
  "Oshana",
  "Oshikoto",
  "Otjozondjupa",
  "Zambezi",
];
function populateFields() {
  const nqf = $("nqf");
  if (nqf.options.length === 1)
    for (let i = 1; i <= 10; i++) nqf.add(new Option("NQF " + i, i));
  const region = $("region");
  if (region.options.length === 1)
    regions.forEach((x) => region.add(new Option(x, x)));
  const field = $("field");
  field.replaceChildren(new Option("Choose a field", ""));
  const values = [
    ...new Set(apiSchemes.flatMap((s) => s.eligible_fields_of_study || [])),
  ].sort();
  if (!values.length) {
    field.add(new Option("Fields will load when the API is available", ""));
    field.disabled = true;
  } else {
    field.disabled = false;
    values.forEach((x) => field.add(new Option(x, x)));
  }
}
$("screen-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = e.currentTarget,
    msg = f.querySelector(".form-message"),
    btn = f.querySelector("button");
  btn.disabled = true;
  msg.textContent = "Checking scheme criteria…";
  try {
    if (demoMode) {
      const profile = {
        nqf_level: Number($("nqf").value),
        field_of_study: $("field").value,
        household_income: Number($("income").value),
        region: $("region").value,
        has_disability: $("disability").value === "true",
      };
      currentResults = demoResults(profile);
      currentRunId = demoHistory.length + 1;
      demoHistory.unshift({
        id: currentRunId,
        created_at: new Date().toISOString(),
        circumstances: profile,
        results: currentResults,
      });
      showResults();
      location.hash = "results";
      msg.textContent = "";
      return;
    }
    currentResults = await request("/api/prescreen", {
      method: "POST",
      auth: true,
      body: {
        nqf_level: Number($("nqf").value),
        field_of_study: $("field").value,
        household_income: Number($("income").value),
        region: $("region").value,
        has_disability: $("disability").value === "true",
      },
    });
    let history = [];
    try {
      history = await request("/api/prescreen/history", { auth: true });
    } catch (historyError) {
      console.warn(
        "Screening succeeded but history could not be loaded:",
        historyError.message,
      );
    } // The POST endpoint returns results only, not a run ID. Find the matching
    // persisted record by its profile and returned results, not list position.
    const submitted = {
      nqf_level: Number($("nqf").value),
      field_of_study: $("field").value,
      household_income: Number($("income").value),
      region: $("region").value,
      has_disability: $("disability").value === "true",
    };
    const sameProfile = (h) =>
      h.circumstances &&
      Number(h.circumstances.nqf_level) === submitted.nqf_level &&
      String(h.circumstances.field_of_study).toLowerCase() ===
        submitted.field_of_study.toLowerCase() &&
      Number(h.circumstances.household_income) === submitted.household_income &&
      String(h.circumstances.region).toLowerCase() ===
        submitted.region.toLowerCase() &&
      Boolean(h.circumstances.has_disability) === submitted.has_disability;
    const sameResults = (h) =>
      Array.isArray(h.results) &&
      h.results.length === currentResults.length &&
      h.results.every(
        (r, i) =>
          r.scheme_name === currentResults[i].scheme_name &&
          r.match_status === currentResults[i].match_status &&
          Number(r.match_score) === Number(currentResults[i].match_score),
      );
    const candidates = (Array.isArray(history) ? history : [])
      .filter((h) => sameProfile(h) && sameResults(h))
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    currentRunId = candidates[0]?.id ?? null;
    showResults();
    if (!currentRunId) {
      $("explanation").textContent =
        "Results are available, but the saved screening could not be identified. You can find it under My Screenings to request an explanation.";
    }
    location.hash = "results";
    msg.textContent = "";
  } catch (err) {
    msg.textContent = err.message;
    msg.className = "form-message error";
  } finally {
    btn.disabled = false;
  }
});
function showResults() {
  const out = $("result-grid");
  out.replaceChildren();
  const summary = $("results-summary");
  summary.replaceChildren();
  const results = Array.isArray(currentResults) ? [...currentResults] : [];
  const rank = (s) =>
    ({ "likely eligible": 0, "possibly eligible": 1, "not eligible": 2 })[
      String(s || "")
        .trim()
        .toLowerCase()
    ] ?? 3;
  results.sort(
    (a, b) =>
      rank(a.match_status) - rank(b.match_status) ||
      Number(b.match_score || 0) - Number(a.match_score || 0),
  );
  if (!results.length) {
    summary.textContent =
      "No registered scheme results were returned. Please try again or contact the project team.";
    return;
  }
  const counts = { likely: 0, possibly: 0, not: 0 };
  results.forEach((r) => {
    const v = rank(r.match_status);
    if (v === 0) counts.likely++;
    else if (v === 1) counts.possibly++;
    else if (v === 2) counts.not++;
  });
  const overview = document.createElement("p");
  overview.textContent = `${results.length} schemes assessed · ${counts.likely} likely eligible · ${counts.possibly} possibly eligible · ${counts.not} not eligible`;
  summary.append(overview);
  for (const r of results) {
    const card = document.createElement("article");
    card.className = "result-card";
    const title = document.createElement("h2");
    title.textContent = r.scheme_name || "Funding scheme";
    const status = document.createElement("strong");
    status.className = "result-status";
    status.textContent = r.match_status || "Status unavailable";
    const score = document.createElement("p");
    score.className = "muted";
    score.textContent =
      "Applicable criteria met: " +
      (r.match_score ?? "Not provided") +
      "%. This is not a probability of funding.";
    const explanation = document.createElement("p");
    explanation.textContent = r.plain_language_explanation || "";
    card.append(title, status, score, explanation);
    for (const [label, arr] of [
      ["What matched", r.factors_that_helped],
      ["What did not match", r.factors_that_hurt],
    ]) {
      if (Array.isArray(arr) && arr.length) {
        const heading = document.createElement("h3");
        heading.textContent = label;
        const ul = document.createElement("ul");
        arr.forEach((x) => {
          const li = document.createElement("li");
          li.textContent = x;
          ul.append(li);
        });
        card.append(heading, ul);
      }
    }
    if (
      Array.isArray(r.what_would_change_this) &&
      r.what_would_change_this.length
    ) {
      const heading = document.createElement("h3");
      heading.textContent = "Possible next steps";
      card.append(heading);
      r.what_would_change_this.forEach((x) => {
        const p = document.createElement("p");
        p.textContent =
          typeof x === "string" ? x : x.suggestion || x.pathway || "";
        card.append(p);
      });
    }
    out.append(card);
  }
  const disclaimer = document.createElement("p");
  disclaimer.className = "notice";
  disclaimer.textContent =
    results[0]?.governance_safeguard ||
    "Advisory only. Final decisions remain with funders.";
  out.append(disclaimer);
  $("explanation").replaceChildren();
  $("conversation").replaceChildren();
}
async function loadHistory() {
  const out = $("history-list");
  out.replaceChildren();
  if (!signedIn) {
    out.textContent = "Sign in to see your screenings.";
    return;
  }
  out.textContent = "Loading screenings…";
  try {
    const history = demoMode
      ? demoHistory
      : await request("/api/prescreen/history", { auth: true });
    out.replaceChildren();
    if (!history.length) {
      out.textContent =
        "No screenings yet. Start your first eligibility check.";
      return;
    }
    for (const item of history) {
      const card = document.createElement("article");
      card.className = "result-card";
      const h = document.createElement("h2");
      h.textContent = "Screening " + (history.length - history.indexOf(item));
      const p = document.createElement("p");
      p.textContent = new Date(item.created_at).toLocaleString();
      const btn = document.createElement("button");
      btn.className = "card-link";
      btn.textContent = "View results →";
      btn.addEventListener("click", () => {
        currentRunId = item.id;
        currentResults = item.results || [];
        showResults();
        location.hash = "results";
      });
      card.append(h, p, btn);
      out.append(card);
    }
  } catch (err) {
    out.textContent = err.message;
  }
}
$("explain-btn").addEventListener("click", async () => {
  const out = $("explanation");
  if (!currentRunId) {
    out.textContent = "A saved screening is needed to request explanations.";
    return;
  }
  out.textContent = "Preparing explanation. This may take up to a minute…";
  try {
    if (demoMode) {
      out.textContent =
        "Sample explanation: These are illustrative results generated in your browser to test the interface. They do not represent actual funding eligibility.";
      return;
    }
    const d = await request(
      "/api/prescreen/history/" + currentRunId + "/explain",
      { method: "POST", auth: true },
    );
    out.replaceChildren();
    const summary = document.createElement("p");
    summary.textContent = d.overall_summary;
    out.append(summary);
    (d.schemes || []).forEach((s) => {
      const h = document.createElement("h3");
      h.textContent = s.scheme_name;
      const p = document.createElement("p");
      p.textContent = s.explanation;
      out.append(h, p);
    });
  } catch (err) {
    out.textContent = err.message;
  }
});
$("ask-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.currentTarget,
    msg = form.querySelector(".form-message"),
    btn = form.querySelector("button"),
    question = $("question").value.trim();
  if (!currentRunId) {
    msg.textContent = "A saved screening is needed to ask questions.";
    return;
  }
  btn.disabled = true;
  msg.textContent = "Preparing answer…";
  try {
    if (demoMode) {
      const box = document.createElement("div");
      box.className = "conversation-turn";
      const q = document.createElement("strong");
      q.textContent = question;
      const a = document.createElement("p");
      a.textContent =
        "Sample response only: Review the listed criteria and contact the official funder. To receive a real explanation, sign in with the connected backend.";
      box.append(q, a);
      $("conversation").append(box);
      $("question").value = "";
      msg.textContent = "";
      return;
    }
    const d = await request("/api/prescreen/history/" + currentRunId + "/ask", {
      method: "POST",
      auth: true,
      body: { question },
    });
    const box = document.createElement("div");
    box.className = "conversation-turn";
    const q = document.createElement("strong");
    q.textContent = question;
    const answer = document.createElement("p");
    answer.textContent = d.answer;
    box.append(q, answer);
    if (d.what_if?.schemes) {
      const ul = document.createElement("ul");
      d.what_if.schemes.forEach((s) => {
        const li = document.createElement("li");
        li.textContent =
          s.scheme_name + ": " + s.before_status + " → " + s.after_status;
        ul.append(li);
      });
      box.append(ul);
    }
    if (d.source === "fallback") {
      const note = document.createElement("small");
      note.textContent =
        "Explanation provided by the rules engine (AI unavailable).";
      box.append(note);
    }
    $("conversation").append(box);
    $("question").value = "";
    msg.textContent = "";
  } catch (err) {
    msg.textContent = err.message;
  } finally {
    btn.disabled = false;
  }
});
const demoSchemes = [
  {
    name: "Sample technology bursary",
    eligible_fields_of_study: [
      "Computer Science",
      "Information Technology",
      "Engineering",
    ],
    min_nqf_level: 5,
    max_household_income: 300000,
  },
  {
    name: "Sample arts bursary",
    eligible_fields_of_study: ["Arts", "Design"],
    min_nqf_level: 5,
    max_household_income: 250000,
  },
  {
    name: "Sample general grant",
    eligible_fields_of_study: [],
    min_nqf_level: 4,
    max_household_income: 200000,
  },
];
function demoResults(profile) {
  return demoSchemes.map((s) => {
    const checks = [
      { label: "NQF level", pass: profile.nqf_level >= s.min_nqf_level },
      {
        label: "Household income",
        pass: profile.household_income <= s.max_household_income,
      },
    ];
    if (s.eligible_fields_of_study.length)
      checks.push({
        label: "Field of study",
        pass: s.eligible_fields_of_study.includes(profile.field_of_study),
      });
    const passed = checks.filter((x) => x.pass).length;
    const failed = checks.length - passed;
    return {
      scheme_name: s.name,
      match_status:
        failed === 0
          ? "Likely eligible"
          : failed === 1
            ? "Possibly eligible"
            : "Not eligible",
      match_score: Math.round((passed / checks.length) * 100),
      plain_language_explanation:
        "Illustrative result for interface testing only. This is not an assessment against a real funder.",
      factors_that_helped: checks
        .filter((x) => x.pass)
        .map((x) => x.label + " matches the sample rule."),
      factors_that_hurt: checks
        .filter((x) => !x.pass)
        .map((x) => x.label + " does not match the sample rule."),
      what_would_change_this: [],
      governance_safeguard:
        "DEMO ONLY: Fictional schemes and synthetic student details. No eligibility decision, application or funding offer.",
    };
  });
}
function startSampleStudent() {
  demoMode = true;
  signedIn = true;
  accessToken = null;
  refreshToken = null;
  updateAuth();
  loadApiSchemes();
  $("nqf").value = "6";
  $("field").value = "Computer Science";
  $("income").value = "120000";
  $("region").value = "Khomas";
  $("disability").value = "false";
  location.hash = "screen";
}
$("demo-access").addEventListener("click", startSampleStudent);
$("signup-demo-access").addEventListener("click", startSampleStudent);
renderSchemes();
populateFields();
loadApiSchemes();
updateAuth();
route();

// Guide contents navigate within the guide without changing the main hash route.
document.querySelectorAll("[data-guide-target]").forEach((link) =>
  link.addEventListener("click", (event) => {
    event.preventDefault();
    if (location.hash !== "#guide") {
      location.hash = "guide";
    }
    const target = document.getElementById(link.dataset.guideTarget);
    if (target)
      target.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "instant"
          : "smooth",
        block: "start",
      });
  }),
);
