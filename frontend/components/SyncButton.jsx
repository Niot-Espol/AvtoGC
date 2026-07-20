export default function SyncButton({ disabled, loading, onClick }) {
  return (
    <button className="button primary" disabled={disabled || loading} onClick={onClick}>
      {loading ? "Sincronizando…" : "Sincronizar con Google Calendar"}
    </button>
  );
}
