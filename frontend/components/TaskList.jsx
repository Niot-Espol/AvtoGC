function formatDate(value) {
  if (!value) return "Sin fecha";
  return new Intl.DateTimeFormat("es-EC", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function label(sourceType = "") {
  const labels = {
    canvas_assignment: "Tarea",
    canvas_sub_assignment: "Subtarea",
    canvas_quiz: "Evaluación",
    canvas_discussion_topic: "Foro",
    canvas_wiki_page: "Lección",
    canvas_announcement: "Anuncio",
    canvas_calendar_event: "Clase/Evento",
    canvas_planner_note: "Nota",
    canvas_assessment_request: "Evaluación por pares",
  };
  return labels[sourceType] || sourceType.replace("canvas_", "").replaceAll("_", " ");
}

export default function TaskList({ tasks }) {
  if (!tasks.length) {
    return <div className="empty-state">Consulta Canvas para mostrar tus próximas actividades.</div>;
  }

  return (
    <div className="task-grid">
      {tasks.map((task) => (
        <article className="task-card" key={task.id_tarea_av}>
          <div className="task-topline">
            <span className="pill">{label(task.source_type)}</span>
            <span>{formatDate(task.fin)}</span>
          </div>
          <h3>{task.titulo}</h3>
          <p>{task.course_name}</p>
          {task.source_url && (
            <a href={task.source_url} target="_blank" rel="noreferrer">
              Abrir en Canvas
            </a>
          )}
        </article>
      ))}
    </div>
  );
}