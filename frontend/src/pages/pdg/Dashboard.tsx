import { useQuery } from '@tanstack/react-query'
import { Building2, Users, TrendingUp, AlertCircle } from 'lucide-react'
import { StatCard } from '../../components/ui/Card'
import Spinner from '../../components/ui/Spinner'
import { getBoutiques } from '../../api/boutiques'
import { formatMontant } from '../../utils/format'

export default function PdgDashboard() {
  const { data: boutiques, isLoading } = useQuery({
    queryKey: ['pdg', 'boutiques'],
    queryFn: getBoutiques,
  })

  if (isLoading) return <Spinner />

  const total   = boutiques?.length ?? 0
  const actives = boutiques?.filter(b => b.actif).length ?? 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Tableau de bord — PDG</h1>
        <p className="text-sm text-gray-500 mt-0.5">Vue d'ensemble de toute l'entreprise</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          titre="Boutiques actives"
          valeur={`${actives} / ${total}`}
          sous="boutiques opérationnelles"
          icone={<Building2 className="h-5 w-5" />}
          couleur="bg-blue-50 text-blue-600"
        />
        <StatCard
          titre="Boutiques inactives"
          valeur={total - actives}
          sous="à réactiver"
          icone={<AlertCircle className="h-5 w-5" />}
          couleur="bg-red-50 text-red-500"
        />
        <StatCard
          titre="Utilisateurs total"
          valeur={boutiques?.reduce((a, b) => a + (b.nb_utilisateurs ?? 0), 0) ?? '—'}
          sous="tous rôles confondus"
          icone={<Users className="h-5 w-5" />}
          couleur="bg-green-50 text-green-600"
        />
        <StatCard
          titre="Chiffre d'affaires"
          valeur="Voir rapports"
          sous="par boutique"
          icone={<TrendingUp className="h-5 w-5" />}
          couleur="bg-purple-50 text-purple-600"
        />
      </div>

      <div>
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Liste des boutiques</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {boutiques?.map(b => (
            <div key={b.id} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-semibold text-gray-900">{b.nom}</p>
                  {b.adresse && <p className="text-xs text-gray-500 mt-0.5">{b.adresse}</p>}
                  {b.telephone && <p className="text-xs text-gray-400">{b.telephone}</p>}
                </div>
                <span className={`text-xs rounded-full px-2 py-0.5 font-medium
                  ${b.actif ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                  {b.actif ? 'Active' : 'Inactive'}
                </span>
              </div>
              {b.nb_utilisateurs !== undefined && (
                <p className="mt-3 text-xs text-gray-500">
                  {b.nb_utilisateurs} utilisateur{b.nb_utilisateurs > 1 ? 's' : ''}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
