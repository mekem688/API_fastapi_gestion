import type { ReactNode } from 'react'

interface CardProps { children: ReactNode; className?: string }
interface StatProps  { titre: string; valeur: string | number; sous?: string; icone?: ReactNode; couleur?: string }

export function Card({ children, className = '' }: CardProps) {
  return (
    <div className={`bg-white rounded-xl border border-gray-200 shadow-sm ${className}`}>
      {children}
    </div>
  )
}

export function CardHeader({ children, className = '' }: CardProps) {
  return <div className={`px-5 py-4 border-b border-gray-100 ${className}`}>{children}</div>
}

export function CardBody({ children, className = '' }: CardProps) {
  return <div className={`px-5 py-4 ${className}`}>{children}</div>
}

export function StatCard({ titre, valeur, sous, icone, couleur = 'bg-primary-50 text-primary-600' }: StatProps) {
  return (
    <div className="stat-card flex items-start justify-between gap-3">
      <div>
        <p className="text-sm text-gray-500">{titre}</p>
        <p className="mt-1 text-2xl font-semibold text-gray-900">{valeur}</p>
        {sous && <p className="mt-0.5 text-xs text-gray-400">{sous}</p>}
      </div>
      {icone && (
        <div className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg ${couleur}`}>
          {icone}
        </div>
      )}
    </div>
  )
}
