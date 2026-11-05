declare global {
  interface Window {
    pywebview?: {
      api?: {
        open_source?: (url: string, title: string) => Promise<{ ok: boolean; error?: string }>
      }
    }
  }
}

export async function openResearchSource(url: string, title: string): Promise<void> {
  const bridge = window.pywebview?.api?.open_source
  if (bridge) {
    const result = await bridge(url, title)
    if (!result.ok) throw new Error(result.error ?? 'The source could not be opened.')
    return
  }

  // Development preview only. The packaged application always uses its contained
  // WebView bridge and never hands citations to an external browser.
  window.open(url, '_blank', 'noopener,noreferrer')
}

export {}
