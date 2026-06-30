import type { ReactNode } from 'react'

interface Column<T> {
  header: string
  accessor?: keyof T
  render?: (row: T) => ReactNode
  className?: string
}

interface Props<T> {
  colonnes: Column<T>[]
  donnees: T[]
  keyFn: (row: T) => string | number
  vide?: string
}

export default function Table<T>({ colonnes, donnees, keyFn, vide = 'Aucune donnée' }: Props<T>) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-100">
            {colonnes.map(col => (
              <th key={col.header}
                className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 ${col.className ?? ''}`}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {donnees.length === 0 ? (
            <tr>
              <td colSpan={colonnes.length} className="px-4 py-10 text-center text-gray-400">
                {vide}
              </td>
            </tr>
          ) : (
            donnees.map(row => (
              <tr key={keyFn(row)} className="hover:bg-gray-50 transition-colors">
                {colonnes.map(col => (
                  <td key={col.header} className={`px-4 py-3 text-gray-700 ${col.className ?? ''}`}>
                    {col.render ? col.render(row) : col.accessor ? String(row[col.accessor] ?? '—') : '—'}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
