import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Bell,
  ChartNoAxesCombined,
  CircleDollarSign,
  Download,
  FileText,
  LayoutDashboard,
  LogOut,
  Moon,
  PiggyBank,
  Plus,
  Receipt,
  RefreshCw,
  Search,
  Settings,
  Shield,
  Sun,
  Tags,
  Trash2,
  Upload,
  User,
  WalletCards,
} from "lucide-react";
import "./styles.css";

const DEFAULT_API_URL = window.location.port === "80" || window.location.port === "" ? "/api" : "http://localhost:8000";
const API_URL = (import.meta.env.VITE_API_URL || DEFAULT_API_URL).replace(/\/$/, "");

const navItems = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "expenses", label: "Expenses", icon: WalletCards },
  { id: "categories", label: "Categories", icon: Tags },
  { id: "budgets", label: "Budgets", icon: PiggyBank },
  { id: "recurring", label: "Recurring", icon: RefreshCw },
  { id: "receipts", label: "Receipts", icon: Receipt },
  { id: "reports", label: "Reports", icon: FileText },
  { id: "notifications", label: "Alerts", icon: Bell },
  { id: "profile", label: "Profile", icon: User },
  { id: "admin", label: "Admin", icon: Shield },
];

function todayInput() {
  return new Date().toISOString().slice(0, 16);
}

function money(value, currency = "USD") {
  return new Intl.NumberFormat("en", { style: "currency", currency }).format(Number(value || 0));
}

function useApi(token, onAuthError) {
  return useMemo(() => {
    async function request(path, options = {}) {
      const headers = { ...(options.headers || {}) };
      if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
      if (token) headers.Authorization = `Bearer ${token}`;

      const response = await fetch(`${API_URL}${path}`, { ...options, headers });
      if (response.status === 401 || response.status === 403) onAuthError?.();
      if (!response.ok) {
        let detail = "Request failed";
        try {
          const data = await response.json();
          detail = data.detail || detail;
        } catch {
          detail = await response.text();
        }
        throw new Error(detail);
      }
      const type = response.headers.get("content-type") || "";
      if (type.includes("application/json")) return response.json();
      return response.blob();
    }

    return {
      get: (path) => request(path),
      post: (path, body) => request(path, { method: "POST", body: body instanceof FormData ? body : JSON.stringify(body || {}) }),
      put: (path, body) => request(path, { method: "PUT", body: body ? JSON.stringify(body) : undefined }),
      del: (path) => request(path, { method: "DELETE" }),
      download: request,
    };
  }, [token, onAuthError]);
}

function Field({ label, children }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  );
}

function Empty({ label }) {
  return <div className="empty">{label}</div>;
}

function AuthScreen({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ email: "", password: "", first_name: "", last_name: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "register") {
        await fetch(`${API_URL}/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(form),
        }).then(async (response) => {
          if (!response.ok) throw new Error((await response.json()).detail || "Registration failed");
        });
      }
      const token = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: form.email, password: form.password }),
      }).then(async (response) => {
        if (!response.ok) throw new Error((await response.json()).detail || "Login failed");
        return response.json();
      });
      onLogin(token.access_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-panel">
        <div>
          <p className="eyebrow">Expense Management</p>
          <h1>{mode === "login" ? "Sign in" : "Create account"}</h1>
        </div>
        <div className="segmented">
          <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>Login</button>
          <button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>Register</button>
        </div>
        <form onSubmit={submit} className="stack">
          {mode === "register" && (
            <div className="grid two">
              <Field label="First name">
                <input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
              </Field>
              <Field label="Last name">
                <input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
              </Field>
            </div>
          )}
          <Field label="Email">
            <input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </Field>
          <Field label="Password">
            <input type="password" required minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          </Field>
          {error && <div className="error">{error}</div>}
          <button className="primary" disabled={busy}>{busy ? "Working..." : mode === "login" ? "Login" : "Register"}</button>
        </form>
      </section>
    </main>
  );
}

function App() {
  const [token, setToken] = useState(localStorage.getItem("expense_token") || "");
  const [view, setView] = useState("dashboard");
  const [user, setUser] = useState(null);
  const [toast, setToast] = useState("");
  const api = useApi(token, logout);

  function login(nextToken) {
    localStorage.setItem("expense_token", nextToken);
    setToken(nextToken);
  }

  function logout() {
    localStorage.removeItem("expense_token");
    setToken("");
    setUser(null);
  }

  async function loadUser() {
    if (!token) return;
    try {
      const current = await api.get("/auth/me");
      setUser(current);
      document.documentElement.dataset.theme = current.theme === "dark" ? "dark" : "light";
    } catch (err) {
      setToast(err.message);
    }
  }

  useEffect(() => {
    loadUser();
  }, [token]);

  if (!token) return <AuthScreen onLogin={login} />;

  const ActiveIcon = navItems.find((item) => item.id === view)?.icon || LayoutDashboard;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <CircleDollarSign />
          <span>ExpenseOps</span>
        </div>
        <nav>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button key={item.id} className={view === item.id ? "active" : ""} onClick={() => setView(item.id)} title={item.label}>
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>
      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow"><ActiveIcon size={14} /> {navItems.find((item) => item.id === view)?.label}</p>
            <h1>{view[0].toUpperCase() + view.slice(1)}</h1>
          </div>
          <div className="top-actions">
            <button className="icon-btn" title="Toggle theme" onClick={() => setView("profile")}>
              {user?.theme === "dark" ? <Moon /> : <Sun />}
            </button>
            <button className="icon-btn" title="Logout" onClick={logout}><LogOut /></button>
          </div>
        </header>
        {toast && <button className="toast" onClick={() => setToast("")}>{toast}</button>}
        <ActiveView view={view} api={api} user={user} reloadUser={loadUser} setToast={setToast} />
      </main>
    </div>
  );
}

function ActiveView(props) {
  switch (props.view) {
    case "expenses": return <Expenses {...props} />;
    case "categories": return <Categories {...props} />;
    case "budgets": return <Budgets {...props} />;
    case "recurring": return <Recurring {...props} />;
    case "receipts": return <Receipts {...props} />;
    case "reports": return <Reports {...props} />;
    case "notifications": return <Notifications {...props} />;
    case "profile": return <Profile {...props} />;
    case "admin": return <Admin {...props} />;
    default: return <Dashboard {...props} />;
  }
}

function Dashboard({ api, user, setToast }) {
  const [data, setData] = useState({ summary: {}, recent: [], categories: [], trends: [], budgets: [] });
  useEffect(() => {
    Promise.all([
      api.get("/dashboard/summary"),
      api.get("/dashboard/recent-expenses"),
      api.get("/dashboard/spending-by-category"),
      api.get("/dashboard/spending-trend"),
      api.get("/dashboard/budget-overview"),
    ]).then(([summary, recent, categories, trends, budgets]) => setData({ summary, recent, categories, trends, budgets })).catch((e) => setToast(e.message));
  }, []);
  return (
    <section className="stack">
      <div className="metric-grid">
        <Metric label="Total" value={money(data.summary.total_expenses, user?.currency)} />
        <Metric label="Month" value={money(data.summary.monthly_expenses, user?.currency)} />
        <Metric label="Week" value={money(data.summary.weekly_expenses, user?.currency)} />
        <Metric label="Today" value={money(data.summary.daily_expenses, user?.currency)} />
      </div>
      <div className="content-grid">
        <Panel title="Category Spending">
          <Bars data={data.categories.map((x) => ({ label: x.category_name, value: x.total_amount }))} />
        </Panel>
        <Panel title="Spending Trend">
          <Bars data={data.trends.map((x) => ({ label: x.period, value: x.total_amount }))} />
        </Panel>
      </div>
      <Panel title="Recent Transactions">
        <DataTable rows={data.recent} columns={["title", "amount", "expense_date", "payment_method"]} currency={user?.currency} />
      </Panel>
    </section>
  );
}

function Metric({ label, value }) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong></div>;
}

function Panel({ title, children, action }) {
  return <section className="panel"><div className="panel-head"><h2>{title}</h2>{action}</div>{children}</section>;
}

function Bars({ data }) {
  const max = Math.max(...data.map((x) => Number(x.value || 0)), 1);
  if (!data.length) return <Empty label="No data yet" />;
  return (
    <div className="bars">
      {data.map((item) => (
        <div className="bar-row" key={item.label}>
          <span>{item.label}</span>
          <div><i style={{ width: `${Math.max(5, (item.value / max) * 100)}%` }} /></div>
          <b>{Number(item.value || 0).toFixed(0)}</b>
        </div>
      ))}
    </div>
  );
}

function DataTable({ rows, columns, currency }) {
  if (!rows?.length) return <Empty label="No records" />;
  return (
    <div className="table-wrap">
      <table>
        <thead><tr>{columns.map((column) => <th key={column}>{column.replaceAll("_", " ")}</th>)}</tr></thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id || JSON.stringify(row)}>
              {columns.map((column) => <td key={column}>{column.includes("amount") || column === "spent" || column === "remaining" ? money(row[column], currency) : String(row[column] ?? "")}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Expenses({ api, user, setToast }) {
  const [expenses, setExpenses] = useState([]);
  const [categories, setCategories] = useState([]);
  const [filters, setFilters] = useState({ search: "", sort_by: "expense_date", sort_order: "desc" });
  const [form, setForm] = useState({ title: "", amount: "", expense_date: todayInput(), category_id: "", payment_method: "card", description: "", notes: "" });

  async function load() {
    const query = new URLSearchParams(Object.fromEntries(Object.entries(filters).filter(([, v]) => v)));
    const [nextExpenses, nextCategories] = await Promise.all([api.get(`/expenses/?${query}`), api.get("/categories/")]);
    setExpenses(nextExpenses);
    setCategories(nextCategories);
  }
  useEffect(() => { load().catch((e) => setToast(e.message)); }, []);

  async function save(event) {
    event.preventDefault();
    await api.post("/expenses/", { ...form, amount: Number(form.amount), category_id: form.category_id ? Number(form.category_id) : null, expense_date: new Date(form.expense_date).toISOString() });
    setForm({ ...form, title: "", amount: "", description: "", notes: "" });
    await load();
  }

  async function remove(id) {
    await api.del(`/expenses/${id}`);
    await load();
  }

  return (
    <section className="stack">
      <Panel title="Add Expense">
        <form className="form-grid" onSubmit={(e) => save(e).catch((err) => setToast(err.message))}>
          <Field label="Title"><input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></Field>
          <Field label="Amount"><input required type="number" step="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} /></Field>
          <Field label="Date"><input type="datetime-local" value={form.expense_date} onChange={(e) => setForm({ ...form, expense_date: e.target.value })} /></Field>
          <Field label="Category"><select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}><option value="">Uncategorized</option>{categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></Field>
          <Field label="Payment"><select value={form.payment_method} onChange={(e) => setForm({ ...form, payment_method: e.target.value })}><option>card</option><option>cash</option><option>upi</option><option>bank</option></select></Field>
          <Field label="Description"><input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></Field>
          <button className="primary"><Plus size={16} /> Add</button>
        </form>
      </Panel>
      <Panel title="Expense History" action={<SearchBox filters={filters} setFilters={setFilters} onSearch={() => load().catch((e) => setToast(e.message))} />}>
        <div className="cards-list">
          {expenses.map((expense) => (
            <article className="row-card" key={expense.id}>
              <div><strong>{expense.title}</strong><span>{new Date(expense.expense_date).toLocaleString()}</span></div>
              <b>{money(expense.amount, user?.currency)}</b>
              <button className="icon-btn danger" title="Delete" onClick={() => remove(expense.id).catch((e) => setToast(e.message))}><Trash2 /></button>
            </article>
          ))}
          {!expenses.length && <Empty label="No expenses" />}
        </div>
      </Panel>
    </section>
  );
}

function SearchBox({ filters, setFilters, onSearch }) {
  return (
    <div className="search-row">
      <input placeholder="Search" value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} />
      <select value={filters.sort_by} onChange={(e) => setFilters({ ...filters, sort_by: e.target.value })}><option value="expense_date">Date</option><option value="amount">Amount</option><option value="created_at">Created</option></select>
      <button className="icon-btn" onClick={onSearch} title="Search"><Search /></button>
    </div>
  );
}

function Categories({ api, setToast }) {
  const [rows, setRows] = useState([]);
  const [form, setForm] = useState({ name: "", icon: "circle-dot", color: "#2563eb" });
  const load = () => api.get("/categories/").then(setRows).catch((e) => setToast(e.message));
  useEffect(() => {
    load().catch((e) => setToast(e.message));
  }, []);
  async function save(e) {
    e.preventDefault();
    await api.post("/categories/", form);
    setForm({ ...form, name: "" });
    load();
  }
  return (
    <section className="stack">
      <Panel title="Create Category">
        <form className="form-grid" onSubmit={(e) => save(e).catch((err) => setToast(err.message))}>
          <Field label="Name"><input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></Field>
          <Field label="Icon"><input value={form.icon} onChange={(e) => setForm({ ...form, icon: e.target.value })} /></Field>
          <Field label="Color"><input type="color" value={form.color} onChange={(e) => setForm({ ...form, color: e.target.value })} /></Field>
          <button className="primary"><Plus size={16} /> Create</button>
        </form>
      </Panel>
      <Panel title="Categories">
        <div className="tile-grid">{rows.map((row) => <div className="category-tile" key={row.id}><i style={{ background: row.color }} /> <strong>{row.name}</strong><span>{row.is_default ? "Default" : "Custom"}</span></div>)}</div>
      </Panel>
    </section>
  );
}

function Budgets({ api, user, setToast }) {
  const [budgets, setBudgets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [progress, setProgress] = useState([]);
  const [form, setForm] = useState({ name: "", amount: "", budget_type: "monthly", category_id: "", start_date: todayInput(), end_date: "" });
  async function load() {
    const [b, c] = await Promise.all([api.get("/budgets/"), api.get("/categories/")]);
    setBudgets(b);
    setCategories(c);
    const p = await Promise.all(b.map((budget) => api.get(`/budgets/${budget.id}/progress`).catch(() => null)));
    setProgress(p.filter(Boolean));
  }
  useEffect(() => { load().catch((e) => setToast(e.message)); }, []);
  async function save(e) {
    e.preventDefault();
    await api.post("/budgets/", { ...form, amount: Number(form.amount), category_id: form.category_id ? Number(form.category_id) : null, start_date: new Date(form.start_date).toISOString(), end_date: form.end_date ? new Date(form.end_date).toISOString() : null });
    setForm({ ...form, name: "", amount: "" });
    load();
  }
  return (
    <section className="stack">
      <Panel title="Create Budget">
        <form className="form-grid" onSubmit={(e) => save(e).catch((err) => setToast(err.message))}>
          <Field label="Name"><input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></Field>
          <Field label="Amount"><input required type="number" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} /></Field>
          <Field label="Type"><select value={form.budget_type} onChange={(e) => setForm({ ...form, budget_type: e.target.value })}><option>monthly</option><option>weekly</option><option>category</option></select></Field>
          <Field label="Category"><select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}><option value="">All</option>{categories.map((c) => <option value={c.id} key={c.id}>{c.name}</option>)}</select></Field>
          <Field label="Start"><input type="datetime-local" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} /></Field>
          <Field label="End"><input type="datetime-local" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} /></Field>
          <button className="primary"><Plus size={16} /> Save</button>
        </form>
      </Panel>
      <Panel title="Budget Progress">
        <div className="cards-list">{progress.map((item) => <article className="row-card" key={item.budget_id}><div><strong>{money(item.total_spent, user?.currency)} / {money(item.budget_amount, user?.currency)}</strong><span>{item.percentage_used}% used</span></div><progress value={Math.min(item.percentage_used, 100)} max="100" /><b>{money(item.remaining, user?.currency)}</b></article>)}</div>
      </Panel>
    </section>
  );
}

function Recurring({ api, user, setToast }) {
  const [rows, setRows] = useState([]);
  const [form, setForm] = useState({ title: "", amount: "", frequency: "monthly", next_due_date: todayInput() });
  const load = () => api.get("/recurring-expenses/").then(setRows).catch((e) => setToast(e.message));
  useEffect(() => {
    load().catch((e) => setToast(e.message));
  }, []);
  async function save(e) {
    e.preventDefault();
    const params = new URLSearchParams({ title: form.title, amount: form.amount, frequency: form.frequency, next_due_date: new Date(form.next_due_date).toISOString() });
    await api.post(`/recurring-expenses/?${params}`);
    setForm({ ...form, title: "", amount: "" });
    load();
  }
  return (
    <section className="stack">
      <Panel title="Create Recurring Expense">
        <form className="form-grid" onSubmit={(e) => save(e).catch((err) => setToast(err.message))}>
          <Field label="Title"><input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></Field>
          <Field label="Amount"><input required type="number" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} /></Field>
          <Field label="Frequency"><select value={form.frequency} onChange={(e) => setForm({ ...form, frequency: e.target.value })}><option>daily</option><option>weekly</option><option>monthly</option><option>yearly</option></select></Field>
          <Field label="Next due"><input type="datetime-local" value={form.next_due_date} onChange={(e) => setForm({ ...form, next_due_date: e.target.value })} /></Field>
          <button className="primary"><RefreshCw size={16} /> Create</button>
        </form>
      </Panel>
      <Panel title="Recurring Expenses"><DataTable rows={rows} columns={["title", "amount", "frequency", "next_due_date", "is_active"]} currency={user?.currency} /></Panel>
    </section>
  );
}

function Receipts({ api, setToast }) {
  const [expenseId, setExpenseId] = useState("");
  const [file, setFile] = useState(null);
  const [rows, setRows] = useState([]);
  async function load() {
    if (!expenseId) return;
    setRows(await api.get(`/receipts/expenses/${expenseId}`));
  }
  async function upload(e) {
    e.preventDefault();
    const data = new FormData();
    data.append("file", file);
    await api.post(`/receipts/expenses/${expenseId}`, data);
    load();
  }
  return (
    <section className="stack">
      <Panel title="Upload Receipt">
        <form className="form-grid" onSubmit={(e) => upload(e).catch((err) => setToast(err.message))}>
          <Field label="Expense ID"><input required value={expenseId} onChange={(e) => setExpenseId(e.target.value)} /></Field>
          <Field label="File"><input required type="file" onChange={(e) => setFile(e.target.files[0])} /></Field>
          <button className="primary"><Upload size={16} /> Upload</button>
          <button type="button" onClick={() => load().catch((e) => setToast(e.message))}>View</button>
        </form>
      </Panel>
      <Panel title="Receipts"><DataTable rows={rows} columns={["id", "file_name", "file_type", "file_size", "created_at"]} /></Panel>
    </section>
  );
}

function Reports({ api, setToast }) {
  async function download(path, name) {
    try {
      const blob = await api.download(path);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = name;
      link.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setToast(e.message);
    }
  }
  return (
    <section className="report-grid">
      <button className="report-card" onClick={() => download("/reports/expenses/csv", "expenses.csv")}><Download /> Expense CSV</button>
      <button className="report-card" onClick={() => download("/reports/expenses/by-category/csv", "category-report.csv")}><Download /> Category CSV</button>
      <button className="report-card" onClick={() => download("/reports/monthly-summary/csv", "monthly-summary.csv")}><Download /> Monthly CSV</button>
      <button className="report-card" onClick={() => download("/reports/yearly-summary/csv", "yearly-summary.csv")}><Download /> Yearly CSV</button>
      <button className="report-card" onClick={() => download("/reports/expenses/pdf", "expenses.pdf")}><Download /> Expense PDF</button>
    </section>
  );
}

function Notifications({ api, setToast }) {
  const [rows, setRows] = useState([]);
  const load = () => api.get("/notifications/").then(setRows).catch((e) => setToast(e.message));
  useEffect(() => {
    load().catch((e) => setToast(e.message));
  }, []);
  return (
    <Panel title="Notifications" action={<button onClick={() => api.put("/notifications/mark-all-as-read").then(load).catch((e) => setToast(e.message))}>Mark all read</button>}>
      <div className="cards-list">{rows.map((row) => <article className="row-card" key={row.id}><div><strong>{row.title}</strong><span>{row.message}</span></div><b>{row.is_read ? "Read" : "New"}</b></article>)}</div>
    </Panel>
  );
}

function Profile({ api, user, reloadUser, setToast }) {
  const [form, setForm] = useState(user || {});
  useEffect(() => setForm(user || {}), [user]);
  async function save(e) {
    e.preventDefault();
    const params = new URLSearchParams(["first_name", "last_name", "currency", "theme", "timezone", "language"].map((key) => [key, form[key] || ""]));
    await api.put(`/users/profile?${params}`);
    await reloadUser();
  }
  return (
    <Panel title="Profile Preferences">
      <form className="form-grid" onSubmit={(e) => save(e).catch((err) => setToast(err.message))}>
        <Field label="First name"><input value={form.first_name || ""} onChange={(e) => setForm({ ...form, first_name: e.target.value })} /></Field>
        <Field label="Last name"><input value={form.last_name || ""} onChange={(e) => setForm({ ...form, last_name: e.target.value })} /></Field>
        <Field label="Currency"><select value={form.currency || "USD"} onChange={(e) => setForm({ ...form, currency: e.target.value })}><option>USD</option><option>INR</option><option>EUR</option><option>GBP</option></select></Field>
        <Field label="Theme"><select value={form.theme || "light"} onChange={(e) => setForm({ ...form, theme: e.target.value })}><option>light</option><option>dark</option></select></Field>
        <Field label="Timezone"><input value={form.timezone || "UTC"} onChange={(e) => setForm({ ...form, timezone: e.target.value })} /></Field>
        <Field label="Language"><input value={form.language || "en"} onChange={(e) => setForm({ ...form, language: e.target.value })} /></Field>
        <button className="primary"><Settings size={16} /> Save</button>
      </form>
    </Panel>
  );
}

function Admin({ api, setToast }) {
  const [dashboard, setDashboard] = useState({});
  const [users, setUsers] = useState([]);
  useEffect(() => {
    Promise.all([api.get("/admin/dashboard"), api.get("/admin/users")]).then(([d, u]) => { setDashboard(d); setUsers(u); }).catch((e) => setToast(e.message));
  }, []);
  return (
    <section className="stack">
      <div className="metric-grid">
        <Metric label="Users" value={dashboard.total_users || 0} />
        <Metric label="Active" value={dashboard.active_users || 0} />
        <Metric label="Expenses" value={dashboard.total_expense_count || 0} />
        <Metric label="Recent Spend" value={dashboard.recent_expenses_last_30_days || 0} />
      </div>
      <Panel title="User Management"><DataTable rows={users} columns={["id", "email", "is_active", "is_verified", "created_at"]} /></Panel>
    </section>
  );
}

createRoot(document.getElementById("root")).render(<App />);
