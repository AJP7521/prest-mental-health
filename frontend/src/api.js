export async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, { ...options, headers: { 'Content-Type': 'application/json' }, signal: AbortSignal.timeout(5000) })
  if (!response.ok) throw new Error('History could not be saved or loaded. Your exercise controls still work.')
  return response.status === 204 ? null : response.json()
}
