import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ApiError,
  getDataset,
  getDatasetInsights,
  getDatasetProfile,
} from "../api/client";
import type { Dataset, DatasetInsights, DatasetProfile } from "../api/types";

export function DatasetDetailPage() {
  const params = useParams<{ projectId: string; datasetId: string }>();
  const projectId = Number(params.projectId);
  const datasetId = Number(params.datasetId);

  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [insights, setInsights] = useState<DatasetInsights | null>(null);
  const [notProfiled, setNotProfiled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (Number.isNaN(projectId) || Number.isNaN(datasetId)) {
      setError("Identificativi di progetto/dataset non validi.");
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);
    setNotProfiled(false);

    async function load() {
      try {
        const datasetData = await getDataset(projectId, datasetId);
        if (cancelled) return;
        setDataset(datasetData);

        try {
          const [profileData, insightsData] = await Promise.all([
            getDatasetProfile(projectId, datasetId),
            getDatasetInsights(projectId, datasetId),
          ]);
          if (cancelled) return;
          setProfile(profileData);
          setInsights(insightsData);
        } catch (err) {
          if (cancelled) return;
          if (err instanceof ApiError && err.status === 404) {
            setNotProfiled(true);
          } else {
            throw err;
          }
        }
      } catch (err) {
        if (cancelled) return;
        setError(
          err instanceof ApiError
            ? err.message
            : "Errore nel caricamento del dataset.",
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, [projectId, datasetId]);

  if (loading) return <p>Caricamento…</p>;

  if (error) {
    return (
      <div>
        <p>
          <Link to="/datasets">&larr; Torna ai dataset</Link>
        </p>
        <p className="form-error" role="alert">
          {error}
        </p>
      </div>
    );
  }

  if (!dataset) return <p>Dataset non trovato.</p>;

  return (
    <div>
      <p>
        <Link to="/datasets">&larr; Torna ai dataset</Link>
      </p>
      <h2>{dataset.name}</h2>
      <p>
        Stato:{" "}
        <span className={`status-badge status-${dataset.status}`}>
          {dataset.status}
        </span>
        {" · "}Sorgente: {dataset.source_type}
      </p>

      {notProfiled && (
        <p className="notice">
          Dataset non ancora profilato. Avvia l'ingestione per generare
          profilo e insight.
        </p>
      )}

      {profile && insights && (
        <>
          <section>
            <h3>Metriche</h3>
            <div className="metrics-grid">
              <div className="metric-card">
                <span className="metric-label">Righe</span>
                <span className="metric-value">
                  {insights.metrics.row_count}
                </span>
              </div>
              <div className="metric-card">
                <span className="metric-label">Colonne</span>
                <span className="metric-value">
                  {insights.metrics.column_count}
                </span>
              </div>
              <div className="metric-card">
                <span className="metric-label">Valori mancanti</span>
                <span className="metric-value">
                  {insights.metrics.total_missing_values}
                </span>
              </div>
              <div className="metric-card">
                <span className="metric-label">Completezza</span>
                <span className="metric-value">
                  {(insights.metrics.completeness_score * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </section>

          <section>
            <h3>Colonne</h3>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Colonna</th>
                  <th>Tipo</th>
                  <th>Valori mancanti</th>
                  <th>% mancanti</th>
                </tr>
              </thead>
              <tbody>
                {Object.keys(profile.column_dtypes).map((column) => (
                  <tr key={column}>
                    <td>{column}</td>
                    <td>{profile.column_dtypes[column]}</td>
                    <td>{profile.column_missing_counts[column] ?? 0}</td>
                    <td>
                      {(
                        (insights.metrics.column_missing_ratios[column] ?? 0) *
                        100
                      ).toFixed(1)}
                      %
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section>
            <h3>Issue di qualità ({insights.issues.length})</h3>
            {insights.issues.length === 0 && <p>Nessuna issue rilevata.</p>}
            {insights.issues.length > 0 && (
              <ul className="issues-list">
                {insights.issues.map((issue) => (
                  <li key={issue.id} className={`issue issue-${issue.severity}`}>
                    <span className="issue-severity">{issue.severity}</span>
                    <span className="issue-rule">{issue.rule_code}</span>
                    <p className="issue-message">{issue.message}</p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}
