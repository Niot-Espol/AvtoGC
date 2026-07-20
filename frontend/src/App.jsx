import { useEffect, useMemo, useState } from "react";
import { API_URL, apiFetch } from "../api/client.js";
import CanvasAccessForm from "../components/CanvasAccessForm.jsx";
import SyncButton from "../components/SyncButton.jsx";
import TaskList from "../components/TaskList.jsx";

function inputDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function initialRange() {
  const start = new Date();
  const end = new Date();
  end.setDate(end.getDate() + 120);
  return { start: inputDate(start), end: inputDate(end) };
}

export default function App() {
  const range = useMemo(() => initialRange(), []);
  const [canvasConnected, setCanvasConnected] = useState(false);
  const [canvasProfile, setCanvasProfile] = useState(null);
  const [googleConnected, setGoogleConnected] = useState(false);
  const [calendars, setCalendars] = useState([]);
  const [calendarId, setCalendarId] = useState("primary");
  const [startDate, setStartDate] = useState(range.start);
  const [endDate, setEndDate] = useState(range.end);
  const [includeCompleted, setIncludeCompleted] = useState(false);
  const [courses, setCourses] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [stats, setStats] = useState({});
  const [search, setSearch] = useState("");
  const [message, setMessage] = useState("");
  const [accessError, setAccessError] = useState("");
  const [loading, setLoading] = useState(false);

  const filteredTasks = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return tasks;
    return tasks.filter((task) =>
      `${task.titulo} ${task.course_name} ${task.source_type}`
        .toLowerCase()
        .includes(query),
    );
  }, [tasks, search]);

  async function loadStatus() {
    const [canvas, google, dashboard] = await Promise.all([
      apiFetch("/api/canvas/status"),
      apiFetch("/api/google/status"),
      apiFetch("/api/dashboard-stats"),
    ]);
    setCanvasConnected(Boolean(canvas.connected));
    setCanvasProfile(canvas.profile || null);
    setGoogleConnected(Boolean(google.connected));
    setStats(dashboard || {});
    if (google.connected) {
      const result = await apiFetch("/api/google/calendars");
      setCalendars(result.items || []);
      const primary = (result.items || []).find((calendar) => calendar.primary);
      if (primary?.id) setCalendarId(primary.id);
    }
  }

  useEffect(() => {
    loadStatus().catch((error) => setMessage(error.message));
  }, []);

  async function connectCanvas(credentials) {
    setLoading(true);
    setAccessError("");
    try {
      const result = await apiFetch("/api/canvas/connect", {
        method: "POST",
        body: JSON.stringify(credentials),
      });
      setCanvasConnected(true);
      setCanvasProfile(result.profile);
      setMessage(`Canvas conectado como ${result.profile.name}.`);
    } catch (error) {
      setAccessError(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function disconnectCanvas() {
    await apiFetch("/api/canvas/disconnect", { method: "POST" });
    setCanvasConnected(false);
    setCanvasProfile(null);
    setCourses([]);
    setTasks([]);
    setMessage("La conexión de Canvas fue eliminada de la memoria del servidor.");
  }

  async function disconnectGoogle() {
    await apiFetch("/api/google/disconnect", { method: "POST" });
    setGoogleConnected(false);
    setCalendars([]);
    setMessage("Google Calendar fue desconectado.");
  }

  async function preview() {
    setLoading(true);
    setMessage("");
    try {
      const result = await apiFetch("/api/preview", {
        method: "POST",
        body: JSON.stringify({
          start_date: startDate,
          end_date: endDate,
          calendar_id: calendarId,
          include_completed: includeCompleted,
        }),
      });
      setCourses(result.courses || []);
      setTasks(result.tasks || []);
      setMessage(
        `Se encontraron ${result.raw_count} elementos. ${result.tasks.length} tienen fecha y hora para Google Calendar.`,
      );
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function synchronize() {
    setLoading(true);
    setMessage("");
    try {
      const result = await apiFetch("/api/sync", {
        method: "POST",
        body: JSON.stringify({
          start_date: startDate,
          end_date: endDate,
          calendar_id: calendarId,
          include_completed: includeCompleted,
        }),
      });
      setMessage(
        `Procesadas: ${result.processed}. Nuevas: ${result.counts.insertada}. Actualizadas: ${result.counts.actualizada}. Sin cambios: ${result.counts.sin_cambios}. Errores: ${result.counts.error}.`,
      );
      await loadStatus();
      await preview();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  if (!canvasConnected) {
    return (
      <CanvasAccessForm
        onConnect={connectCanvas}
        loading={loading}
        error={accessError}
      />
    );
  }

  return (
    <main className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Proyecto NIoT · Automatización académica</p>
          <h1>Canvas → Google Calendar</h1>
          <p className="lead">
            Visualiza lo que debes realizar en el aula virtual y sincroniza fechas y horas
            con tu calendario sin crear eventos duplicados.
          </p>
        </div>
        <div className="profile-card">
          <span className="status-dot" />
          <div>
            <strong>{canvasProfile?.name || "Usuario de Canvas"}</strong>
            <small>{canvasProfile?.primary_email || canvasProfile?.canvas_url}</small>
          </div>
        </div>
      </header>

      <section className="actions card">
        <div className="button-row">
          {!googleConnected ? (
            <a className="button primary" href={`${API_URL}/api/google/login`}>
              Conectar Google Calendar
            </a>
          ) : (
            <button className="button secondary" onClick={disconnectGoogle}>
              Desconectar Google
            </button>
          )}
          <button className="button ghost" onClick={disconnectCanvas}>
            Cambiar cuenta/token de Canvas
          </button>
        </div>
        <div className="connection-labels">
          <span className="badge success">Canvas conectado</span>
          <span className={`badge ${googleConnected ? "success" : "warning"}`}>
            Google {googleConnected ? "conectado" : "pendiente"}
          </span>
        </div>
      </section>

      {message && <div className="message">{message}</div>}

      <section className="filters card">
        <label>
          Desde
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        </label>
        <label>
          Hasta
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
        </label>
        <label>
          Calendario de destino
          <select value={calendarId} onChange={(e) => setCalendarId(e.target.value)}>
            <option value="primary">Calendario principal</option>
            {calendars
              .filter((calendar) => calendar.id !== "primary")
              .map((calendar) => (
                <option key={calendar.id} value={calendar.id}>
                  {calendar.summary}
                </option>
              ))}
          </select>
        </label>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={includeCompleted}
            onChange={(e) => setIncludeCompleted(e.target.checked)}
          />
          Incluir actividades completadas
        </label>
        <div className="button-row align-end">
          <button className="button secondary" onClick={preview} disabled={loading}>
            {loading ? "Consultando…" : "Consultar Canvas"}
          </button>
          <SyncButton
            disabled={!googleConnected}
            loading={loading}
            onClick={synchronize}
          />
        </div>
      </section>

      <section className="stats-grid">
        <article className="stat-card"><span>Cursos activos</span><strong>{courses.length}</strong></article>
        <article className="stat-card"><span>Actividades visibles</span><strong>{tasks.length}</strong></article>
        <article className="stat-card"><span>Sincronizadas</span><strong>{stats.total_tareas || 0}</strong></article>
        <article className="stat-card"><span>Errores</span><strong>{stats.errores || 0}</strong></article>
      </section>

      <section className="content card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Agenda académica</p>
            <h2>Próximas tareas, evaluaciones y clases</h2>
          </div>
          <input
            className="search-input"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Buscar por curso o actividad"
          />
        </div>
        <TaskList tasks={filteredTasks} />
      </section>
    </main>
  );
}
