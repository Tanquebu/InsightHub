import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, listDatasets, listProjects } from "../api/client";
import type { Dataset, Project } from "../api/types";

/**
 * Assunzione di prodotto: la selezione multi-progetto è gestita con un
 * semplice <select> che mostra i dataset del progetto scelto (di default
 * il primo della lista), invece di un elenco "tutti i dataset di tutti i
 * progetti" appiattito. Scelta minimale, coerente con l'MVP.
 */
export function ProjectsDatasetsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(
    null,
  );
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [loadingDatasets, setLoadingDatasets] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoadingProjects(true);
    setError(null);

    listProjects()
      .then((data) => {
        if (cancelled) return;
        setProjects(data);
        if (data.length > 0) {
          setSelectedProjectId(data[0].id);
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(
          err instanceof ApiError
            ? err.message
            : "Errore nel caricamento dei progetti.",
        );
      })
      .finally(() => {
        if (!cancelled) setLoadingProjects(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (selectedProjectId === null) {
      setDatasets([]);
      return;
    }

    let cancelled = false;
    setLoadingDatasets(true);
    setError(null);

    listDatasets(selectedProjectId)
      .then((data) => {
        if (!cancelled) setDatasets(data);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(
          err instanceof ApiError
            ? err.message
            : "Errore nel caricamento dei dataset.",
        );
      })
      .finally(() => {
        if (!cancelled) setLoadingDatasets(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedProjectId]);

  return (
    <div>
      <h2>Dataset</h2>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      {loadingProjects && <p>Caricamento progetti…</p>}

      {!loadingProjects && projects.length === 0 && !error && (
        <p>Nessun progetto disponibile.</p>
      )}

      {projects.length > 0 && (
        <div className="field-row">
          <label htmlFor="project-select">Progetto</label>
          <select
            id="project-select"
            value={selectedProjectId ?? ""}
            onChange={(event) => setSelectedProjectId(Number(event.target.value))}
          >
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {loadingDatasets && <p>Caricamento dataset…</p>}

      {!loadingDatasets &&
        selectedProjectId !== null &&
        datasets.length === 0 && <p>Nessun dataset in questo progetto.</p>}

      {datasets.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Nome</th>
              <th>Stato</th>
              <th>Sorgente</th>
            </tr>
          </thead>
          <tbody>
            {datasets.map((dataset) => (
              <tr key={dataset.id}>
                <td>
                  <Link
                    to={`/projects/${dataset.project_id}/datasets/${dataset.id}`}
                  >
                    {dataset.name}
                  </Link>
                </td>
                <td>
                  <span className={`status-badge status-${dataset.status}`}>
                    {dataset.status}
                  </span>
                </td>
                <td>{dataset.source_type}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
