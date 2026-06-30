type Variant = 'green' | 'red' | 'yellow' | 'blue' | 'gray'

const cls: Record<Variant, string> = {
  green:  'bg-green-100 text-green-700',
  red:    'bg-red-100 text-red-700',
  yellow: 'bg-yellow-100 text-yellow-700',
  blue:   'bg-blue-100 text-blue-700',
  gray:   'bg-gray-100 text-gray-600',
}

interface Props { children: React.ReactNode; variant?: Variant }

export default function Badge({ children, variant = 'gray' }: Props) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${cls[variant]}`}>
      {children}
    </span>
  )
}

export function statutBadge(statut: string) {
  const map: Record<string, { label: string; variant: Variant }> = {
    solde:    { label: 'Soldé',    variant: 'green'  },
    en_cours: { label: 'En cours', variant: 'blue'   },
    en_retard:{ label: 'En retard',variant: 'red'    },
  }
  const { label, variant } = map[statut] ?? { label: statut, variant: 'gray' }
  return <Badge variant={variant}>{label}</Badge>
}
