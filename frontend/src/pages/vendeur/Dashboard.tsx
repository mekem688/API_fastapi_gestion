import { useAuthStore } from '../../stores/authStore'
import { ShoppingCart, CreditCard } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function VenDashboard() {
  const user = useAuthStore(s => s.user)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">
          Bonjour, {user?.prenom} 👋
        </h1>
        <p className="text-sm text-gray-500 mt-0.5">Que voulez-vous enregistrer aujourd'hui ?</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Link
          to="/vendeur/vente"
          className="flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed
            border-primary-200 bg-primary-50 p-8 text-primary-700 hover:bg-primary-100 transition-colors"
        >
          <ShoppingCart className="h-10 w-10" />
          <div className="text-center">
            <p className="font-semibold">Nouvelle vente</p>
            <p className="text-sm text-primary-500 mt-0.5">Enregistrer une vente au comptant</p>
          </div>
        </Link>

        <Link
          to="/vendeur/credit"
          className="flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed
            border-orange-200 bg-orange-50 p-8 text-orange-700 hover:bg-orange-100 transition-colors"
        >
          <CreditCard className="h-10 w-10" />
          <div className="text-center">
            <p className="font-semibold">Nouveau crédit</p>
            <p className="text-sm text-orange-500 mt-0.5">Enregistrer une vente à crédit</p>
          </div>
        </Link>
      </div>
    </div>
  )
}
