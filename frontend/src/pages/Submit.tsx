import { FormEvent, useState } from "react";
import { api } from "../api/client";
import { ApiError, ComplaintOut, FieldError } from "../api/types";
import { Badge } from "../components/Badge";

interface FormState {
  text: string;
  location: string;
  reporter_contact: string;
}

const EMPTY_FORM: FormState = { text: "", location: "", reporter_contact: "" };

// Mirrors, but does not replace, the server's Pydantic constraints
// (ComplaintCreate: text 10-2000 chars, location 3-200 chars). The server
// re-validates every field regardless of what this function decides.
function validate(form: FormState): FieldError[] {
  const errors: FieldError[] = [];
  if (form.text.trim().length < 10) {
    errors.push({ field: "text", message: "Complaint text must be at least 10 characters." });
  } else if (form.text.length > 2000) {
    errors.push({ field: "text", message: "Complaint text must be at most 2000 characters." });
  }
  if (form.location.trim().length < 3) {
    errors.push({ field: "location", message: "Location must be at least 3 characters." });
  } else if (form.location.length > 200) {
    errors.push({ field: "location", message: "Location must be at most 200 characters." });
  }
  return errors;
}

export function Submit() {
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [clientErrors, setClientErrors] = useState<FieldError[]>([]);
  const [serverErrors, setServerErrors] = useState<FieldError[]>([]);
  const [status, setStatus] = useState<"idle" | "submitting" | "done" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [result, setResult] = useState<ComplaintOut | null>(null);

  function fieldError(field: string): string | undefined {
    return [...clientErrors, ...serverErrors].find((e) => e.field === field)?.message;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setServerErrors([]);
    setErrorMessage("");
    setResult(null);

    const errors = validate(form);
    setClientErrors(errors);
    if (errors.length > 0) return;

    setStatus("submitting"); // AI triage takes real seconds - render this honestly
    try {
      const created = await api.submitComplaint({
        text: form.text.trim(),
        location: form.location.trim(),
        reporter_contact: form.reporter_contact.trim() || null,
      });
      setResult(created);
      setStatus("done");
      setForm(EMPTY_FORM);
    } catch (err) {
      setStatus("error");
      if (err instanceof ApiError) {
        if (err.status === 400 && err.fieldErrors.length > 0) {
          setServerErrors(err.fieldErrors);
          setErrorMessage("Please fix the highlighted fields.");
        } else if (err.status === 429) {
          setErrorMessage(
            `You're submitting too quickly. Try again in ${err.retryAfter ?? "a few"} seconds.`
          );
        } else {
          setErrorMessage(err.message);
        }
      } else {
        setErrorMessage("Could not reach the server. Please try again.");
      }
    }
  }

  return (
    <div className="page submit-page">
      <h1>Report a complaint</h1>
      <form onSubmit={handleSubmit} noValidate>
        <label htmlFor="text">What happened?</label>
        <textarea
          id="text"
          rows={5}
          value={form.text}
          onChange={(e) => setForm({ ...form, text: e.target.value })}
          aria-invalid={!!fieldError("text")}
          aria-describedby="text-error"
          placeholder="Describe the issue - as much detail as you can give"
        />
        {fieldError("text") && (
          <p id="text-error" className="field-error" role="alert">
            {fieldError("text")}
          </p>
        )}

        <label htmlFor="location">Location</label>
        <input
          id="location"
          type="text"
          value={form.location}
          onChange={(e) => setForm({ ...form, location: e.target.value })}
          aria-invalid={!!fieldError("location")}
          placeholder="Street, sector, or landmark"
        />
        {fieldError("location") && (
          <p className="field-error" role="alert">
            {fieldError("location")}
          </p>
        )}

        <label htmlFor="contact">Contact (optional)</label>
        <input
          id="contact"
          type="text"
          value={form.reporter_contact}
          onChange={(e) => setForm({ ...form, reporter_contact: e.target.value })}
          placeholder="Phone or email, optional"
        />

        <button type="submit" disabled={status === "submitting"}>
          {status === "submitting" ? "Submitting..." : "Submit complaint"}
        </button>
      </form>

      {status === "submitting" && (
        <p role="status" className="loading-note">
          Triaging your complaint with AI — this can take a few seconds.
        </p>
      )}

      {status === "error" && errorMessage && (
        <p role="alert" className="form-error">
          {errorMessage}
        </p>
      )}

      {status === "done" && result && (
        <div className="triage-result" data-testid="triage-result">
          <h2>Complaint received</h2>
          <p>
            <strong>Category:</strong> <Badge label={result.category} />
          </p>
          <p>
            <strong>Priority:</strong> <Badge label={result.priority} tone={result.priority} />
          </p>
          <p>
            <strong>AI summary:</strong> {result.ai_summary}
          </p>
          <p className="provider-note">
            Triaged by <code>{result.triaged_by}</code> in {result.triage_latency_ms ?? 0} ms
          </p>
        </div>
      )}
    </div>
  );
}
