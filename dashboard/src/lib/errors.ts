/** Parse FastAPI / API errors into human-readable messages. */
export function parseApiError(raw: string): string {
  try {
    const data = JSON.parse(raw);
    if (data.detail) {
      if (typeof data.detail === "string") return data.detail;
      if (Array.isArray(data.detail)) {
        return data.detail
          .map((d: { loc?: string[]; msg?: string }) => {
            const field = d.loc?.slice(-1)[0] ?? "field";
            const msg = d.msg ?? "invalid";
            if (field === "expected_response" && msg.includes("at least")) {
              return "Expected reply must be at least 10 characters — paste a full reference response.";
            }
            if (field === "email" && msg.includes("at least")) {
              return "Email body must be at least 10 characters.";
            }
            return `${String(field).replace(/_/g, " ")}: ${msg}`;
          })
          .join(" · ");
      }
    }
    if (data.message) return data.message;
  } catch {
    /* not JSON */
  }
  if (raw.includes("Failed to fetch") || raw.includes("NetworkError")) {
    return "Cannot reach API — start backend with: python cli.py serve";
  }
  return raw.length > 200 ? raw.slice(0, 200) + "…" : raw;
}
