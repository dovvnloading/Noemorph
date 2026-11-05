import type { ResearchProfileValue as ResearchProfileValueType } from '../types'

export function researchProfileText(value?: ResearchProfileValueType): string {
  if (!value) return ''
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value.join(' ')
  return Object.entries(value)
    .flatMap(([key, item]) => [key, ...(Array.isArray(item) ? item : [item])])
    .join(' ')
}

export function ResearchProfileValue({ value }: { value: ResearchProfileValueType }) {
  if (typeof value === 'string') return <p>{value}</p>
  if (Array.isArray(value)) return <ul>{value.map((item) => <li key={item}>{item}</li>)}</ul>

  return (
    <dl className="research-profile-structure">
      {Object.entries(value).map(([key, item]) => (
        <div key={key}>
          <dt>{key.replaceAll('_', ' ')}</dt>
          <dd>
            {Array.isArray(item)
              ? <ul>{item.map((entry) => <li key={entry}>{entry}</li>)}</ul>
              : item}
          </dd>
        </div>
      ))}
    </dl>
  )
}
