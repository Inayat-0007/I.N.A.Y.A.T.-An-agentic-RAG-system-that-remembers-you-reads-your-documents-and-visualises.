/** Client-side UserId rules — keep in sync with core/identity.py. */

const USER_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;

export function validateUserId(raw) {
  const candidate = (raw ?? "").trim();
  if (!candidate) {
    return "Enter a workspace id to open the agent.";
  }
  if (candidate.length > 64) {
    return "Workspace id must be at most 64 characters.";
  }
  if (/\s/.test(candidate)) {
    return "Use underscores, not spaces (e.g. Moham_Khan).";
  }
  if (candidate === "." || candidate === "..") {
    return "Workspace id cannot be '.' or '..'.";
  }
  if (!USER_ID_PATTERN.test(candidate)) {
    return "Start with a letter or digit; only letters, digits, '.', '_' or '-'.";
  }
  return null;
}
