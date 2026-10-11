import { useRef, useState } from "react";
import { AlertCircle, CheckCircle2, Download, Upload, X } from "lucide-react";
import { api, Plan, ValidationReport } from "../../api/client";

type Mode = "scenario" | "schedule";
type Props = {
  onClose: () => void;
  onScenarioUploaded: (name: string) => void;
  onScheduleImported: (plan: Plan, report: ValidationReport, valid: boolean) => void;
};

const templates = ["scenario_json", "locations_csv", "vehicles_csv", "deliveries_csv", "matrix_csv", "schedule_csv"];

export function UploadDialog({ onClose, onScenarioUploaded, onScheduleImported }: Props) {
  const [mode, setMode] = useState<Mode>("scenario");
  const [files, setFiles] = useState<File[]>([]);
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [preview, setPreview] = useState<Awaited<ReturnType<typeof api.uploadScenarioPreview>>>();
  const [importPreview, setImportPreview] = useState<Awaited<ReturnType<typeof api.importPlanPreview>>>();
  const [result, setResult] = useState<string>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const inputRef = useRef<HTMLInputElement>(null);

  const chooseFiles = (selected: FileList | null) => {
    if (selected) setFiles(Array.from(selected));
    setError(undefined);
  };
  const review = async () => {
    if (!files.length) return;
    setBusy(true); setError(undefined);
    try {
      if (mode === "scenario") {
        setPreview(await api.uploadScenarioPreview(files));
      } else {
        setImportPreview(await api.importPlanPreview(files[0]));
      }
      setStep(3);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Upload preview failed.");
    } finally { setBusy(false); }
  };
  const confirm = async () => {
    setBusy(true); setError(undefined);
    try {
      if (mode === "scenario" && preview) {
        const uploaded = await api.confirmScenarioUpload(preview.token);
        setResult(uploaded.scenario_name);
        onScenarioUploaded(uploaded.scenario_name);
      } else if (mode === "schedule" && importPreview) {
        const imported = await api.confirmPlanImport(importPreview.token);
        setResult(imported.is_valid ? "Imported schedule validated." : "Imported, not valid.");
        onScheduleImported(imported.plan, imported.validation_report, imported.is_valid);
      }
      setStep(4);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Upload confirmation failed.");
    } finally { setBusy(false); }
  };
  const errors = mode === "scenario" ? preview?.errors ?? [] : importPreview?.errors ?? [];
  return <div className="rr-upload-backdrop" role="presentation">
    <section className="rr-upload-dialog" role="dialog" aria-modal="true" aria-labelledby="upload-title">
      <header><div><p className="p12-kicker">DISPATCH WORKSPACE</p><h2 id="upload-title">Upload schedule</h2></div><button className="p12-small-button" aria-label="Close upload dialog" onClick={onClose}><X size={18} /></button></header>
      <ol className="rr-upload-steps" aria-label="Upload steps">{["Choose mode", "Drop files", "Review", "Done"].map((label, index) => <li className={step === index + 1 ? "active" : ""} key={label}>{index + 1}. {label}</li>)}</ol>
      {step === 1 && <div className="rr-upload-body"><h3>What are you uploading?</h3><div className="rr-upload-mode"><button className={mode === "scenario" ? "selected" : ""} onClick={() => setMode("scenario")}>Scenario inputs</button><button className={mode === "schedule" ? "selected" : ""} onClick={() => setMode("schedule")}>Existing schedule</button></div><p>Scenario inputs build a fresh initial plan. Existing schedules require the current scenario and are simulated again.</p><button className="p12-primary-button" onClick={() => setStep(2)}>Continue</button></div>}
      {step === 2 && <div className="rr-upload-body"><label className="rr-drop-zone" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); chooseFiles(event.dataTransfer.files); }}><Upload /><b>Drop files here</b><span>or choose files from your computer</span><input ref={inputRef} type="file" multiple accept={mode === "scenario" ? ".json,.csv,.zip" : ".csv,.json"} onChange={(event) => chooseFiles(event.target.files)} /></label>{files.length > 0 && <ul>{files.map((file) => <li key={file.name}>{file.name} ({Math.ceil(file.size / 1024)} KB)</li>)}</ul>}<p className="rr-template-links">Templates: {templates.map((kind) => <a key={kind} href={`/templates/${kind}`} download><Download size={12} />{kind}</a>)}</p><button className="p12-primary-button" disabled={!files.length || busy} onClick={() => void review()}>{busy ? "Reading…" : "Review upload"}</button></div>}
      {step === 3 && <div className="rr-upload-body"><h3>Review</h3>{(preview || importPreview) && <div className="rr-upload-counts">{Object.entries((preview ?? importPreview)?.counts ?? {}).map(([key, value]) => <span key={key}><b>{value}</b> {key}</span>)}</div>}{preview?.format && <p>Detected format: <b>{preview.format}</b></p>}{(preview?.assumptions ?? []).map((item) => <div className="rr-upload-assumption" key={item}>Assumption: {item}</div>)}{(preview?.warnings ?? importPreview?.arrival_warnings ?? []).map((item) => <div className="rr-upload-warning" key={item}>{item}</div>)}{errors.length > 0 && <div className="rr-upload-errors"><b><AlertCircle size={15} /> Fix these errors before confirming</b>{errors.map((item) => <div key={item}>{item}</div>)}</div>}{preview?.column_mapping && Object.keys(preview.column_mapping).length > 0 && <table><tbody>{Object.entries(preview.column_mapping).map(([from, to]) => <tr key={from}><td>{from}</td><td>→ {to}</td></tr>)}</tbody></table>}<div className="rr-upload-actions"><button className="p12-small-button" onClick={() => setStep(2)}>Back</button><button className="p12-primary-button" disabled={busy || errors.length > 0 || !((preview?.token ?? importPreview?.token))} onClick={() => void confirm()}>{busy ? "Confirming…" : "Confirm upload"}</button></div></div>}
      {step === 4 && <div className="rr-upload-body rr-upload-done"><CheckCircle2 /><h3>Upload complete</h3><p>{result}</p><button className="p12-primary-button" onClick={onClose}>Open plan</button></div>}
      {error && <div className="rr-upload-errors" role="alert">{error}</div>}
    </section>
  </div>;
}
