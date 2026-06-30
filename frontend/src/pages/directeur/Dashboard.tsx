import { useQuery } from '@tanstack/react-query'
import { ShoppingCart, CreditCard, Package, TrendingUp } from 'lucide-react'
import { StatCard } from '../../components/ui/Card'
import Spinner from '../../components/ui/Spinner'
import { getVentes } from '../../api/ventes'
import { getCreditsVentes, getCreditsAchats } from '../../api/credits'
import { getAchats } from '../../api/achats'
import { formatMontant } from '../../utils/format'

export default function DirDashboard() {
  const { data: ventes,  isLoading: lv } = useQuery({ queryKey: ['dir', 'ventes', 1],   queryFn: () => getVentes(1, 5) })
  const { data: credits, isLoading: lc } = useQuery({ queryKey: ['dir', 'credits', 1],  queryFn: () => getCreditsVentes(1, 5) })
  const { data: achats,  isLoading: la } = useQuery({ queryKey: ['dir', 'achats', 1],   queryFn: () => getAchats(1, 5) })
  const { data: credA,   isLoading: lca} = useQuery({ queryKey: ['dir', 'creditsA', 1], queryFn: () => getCreditsAchats(1, 5) })

  if (lv || lc || la || lca) return <Spinner />

  const totalVentes  = ventes?.resultats.reduce((a, v) => a + v.montant, 0) ?? 0
  const totalCredits = credits?.resultats.reduce((a, c) => a + c.reste, 0) ?? 0
  const totalAchats  = achats?.resultats.reduce((a, a2) => a + a2.montant, 0) ?? 0
  const totalCredA   = credA?.resultats.reduce((a, c) => a + c.reste, 0) ?? 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Tableau de bord</h1>
        <p className="text-sm text-gray-500 mt-0.5">Résumé de votre boutique</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          titre="Ventes récentes"
          valeur={formatMontant(totalVentes)}
          sous={`${ventes?.total ?? 0} ventes au total`}
          icone={<ShoppingCart className="h-5 w-5" />}
          couleur="bg-green-50 text-green-600"
        />
        <StatCard
          titre="Crédits clients (restant)"
          valeur={formatMontant(totalCredits)}
          sous={`${credits?.total ?? 0} crédits`}
          icone={<CreditCard className="h-5 w-5" />}
          couleur="bg-orange-50 text-orange-500"
        />
        <StatCard
          titre="Achats récents"
          valeur={formatMontant(totalAchats)}
          sous={`${achats?.total ?? 0} achats au total`}
          icone={<Package className="h-5 w-5" />}
          couleur="bg-blue-50 text-blue-600"
        />
        <StatCard
          titre="Dettes fournisseurs"
          valeur={formatMontant(totalCredA)}
          sous={`${credA?.total ?? 0} crédits achats`}
          icone={<TrendingUp className="h-5 w-5" />}
          couleur="bg-red-50 text-red-500"
        />
      </div>
    </div>
  )
}
