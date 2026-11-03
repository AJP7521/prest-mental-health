export async function api(path, options = {}, timeout = 5000) {
  const response = await fetch(`/api${path}`, { ...options, headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'mental-health-app' }, signal: AbortSignal.timeout(timeout) })
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    const failure = new Error(typeof error.detail === 'string' ? error.detail : 'Check your entries and try again.')
    failure.status = response.status
    throw failure
  }
  return response.status === 204 ? null : response.json()
}
