/**
 * Comparison URLs identify two existing catalog records, not a relationship.
 * Keep the same URL parameter on desktop and the public read-only atlas.
 */
export const PUBLIC_ATLAS_URL = 'https://dovvnloading.github.io/Noemorph/'

export function parseComparisonIds(search: string): string[] {
  const values = new URLSearchParams(search).getAll('compare')
  if (values.length !== 1) return []
  const ids = values[0].split(',')
  if (ids.length !== 2 || ids[0] === ids[1]) return []
  if (ids.some((id) => !/^[A-Za-z0-9_-]{1,160}$/.test(id))) return []
  return ids
}

export function publicComparisonUrl(ids: string[]): string | undefined {
  if (ids.length !== 2 || ids[0] === ids[1]) return undefined
  if (ids.some((id) => !/^[A-Za-z0-9_-]{1,160}$/.test(id))) return undefined
  const url = new URL(PUBLIC_ATLAS_URL)
  url.searchParams.set('compare', ids.join(','))
  url.hash = 'catalog'
  return url.toString()
}
