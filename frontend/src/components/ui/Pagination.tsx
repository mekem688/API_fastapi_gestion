import { ChevronLeft, ChevronRight } from 'lucide-react'

interface Props {
  page: number
  nbPages: number
  total: number
  taille: number
  onChange: (page: number) => void
}

export default function Pagination({ page, nbPages, total, taille, onChange }: Props) {
  if (nbPages <= 1) return null
  const debut = (page - 1) * taille + 1
  const fin   = Math.min(page * taille, total)

  return (
    <div className="flex items-center justify-between border-t border-gray-100 px-1 py-3">
      <p className="text-sm text-gray-500">
        {debut}–{fin} sur {total} résultats
      </p>
      <div className="flex items-center gap-1">
        <button
          disabled={page === 1}
          onClick={() => onChange(page - 1)}
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200
            text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        {Array.from({ length: nbPages }, (_, i) => i + 1)
          .filter(p => Math.abs(p - page) < 3 || p === 1 || p === nbPages)
          .reduce<(number | '...')[]>((acc, p, i, arr) => {
            if (i > 0 && (p as number) - (arr[i - 1] as number) > 1) acc.push('...')
            acc.push(p)
            return acc
          }, [])
          .map((p, i) =>
            p === '...' ? (
              <span key={`sep-${i}`} className="w-8 text-center text-sm text-gray-400">…</span>
            ) : (
              <button
                key={p}
                onClick={() => onChange(p as number)}
                className={`h-8 w-8 rounded-lg text-sm font-medium transition-colors
                  ${page === p
                    ? 'bg-primary-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'}`}
              >
                {p}
              </button>
            ),
          )}
        <button
          disabled={page === nbPages}
          onClick={() => onChange(page + 1)}
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200
            text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
