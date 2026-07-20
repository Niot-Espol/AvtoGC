import { useState } from "react";

export default function CanvasAccessForm({ onConnect, loading, error }) {
  const [baseUrl, setBaseUrl] = useState("");
  const [token, setToken] = useState("");
  const [showToken, setShowToken] = useState(false);

  function submit(event) {
    event.preventDefault();
    onConnect({ base_url: baseUrl.trim(), token: token.trim() });
  }

  return (
    <main className="access-page">
      <section className="access-card">
        <div className="brand-mark">AV</div>
        <p className="eyebrow">Proyecto NIoT</p>
        <h1>Conecta tu aula virtual</h1>
        <p className="lead">
          Ingresa la dirección de Canvas y tu token personal. La aplicación los valida
          antes de mostrar tus cursos, tareas, evaluaciones y eventos.
        </p>

        <form onSubmit={submit} className="access-form">
          <label>
            Dirección de Canvas
            <input
              type="url"
              required
              value={baseUrl}
              onChange={(event) => setBaseUrl(event.target.value)}
              placeholder="https://tu-institucion.instructure.com"
              autoComplete="url"
            />
          </label>

          <label>
            Token de acceso personal
            <div className="token-row">
              <input
                type={showToken ? "text" : "password"}
                required
                minLength={20}
                value={token}
                onChange={(event) => setToken(event.target.value)}
                placeholder="Pega aquí el token completo"
                autoComplete="off"
              />
              <button
                type="button"
                className="icon-button"
                onClick={() => setShowToken((current) => !current)}
                aria-label={showToken ? "Ocultar token" : "Mostrar token"}
              >
                {showToken ? "Ocultar" : "Mostrar"}
              </button>
            </div>
          </label>

          {error && <div className="error-box">{error}</div>}

          <button className="button primary full" disabled={loading}>
            {loading ? "Validando con Canvas…" : "Ingresar y consultar mis clases"}
          </button>
        </form>

        <div className="security-note">
          <strong>Protección del token:</strong> no se guarda en SQLite ni en el navegador.
          Se conserva únicamente en la memoria de FastAPI y se elimina al desconectar o
          reiniciar el backend.
        </div>
      </section>
    </main>
  );
}
