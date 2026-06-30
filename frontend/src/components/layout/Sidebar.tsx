import { NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { X, LayoutDashboard, Store, Users, BookOpen, ShoppingCart, CreditCard, Package } from 'lucide-react'
import type { Role } from '../../types'

interface NavItem { label: string; to: string; icon: React.ReactNode }

const navByRole: Record<Role, NavItem[]> = {
  pdg: [
    { label: 'Tableau de bord', to: '/pdg/dashboard',    icon: <LayoutDashboard className="h-4 w-4" /> },
    { label: 'Boutiques',       to: '/pdg/boutiques',    icon: <Store className="h-4 w-4" /> },
    { label: 'Utilisateurs',    to: '/pdg/utilisateurs', icon: <Users className="h-4 w-4" /> },
    { label: 'Journal',         to: '/pdg/journal',      icon: <BookOpen className="h-4 w-4" /> },
  ],
  directeur: [
    { label: 'Tableau de bord', to: '/directeur/dashboard', icon: <LayoutDashboard className="h-4 w-4" /> },
    { label: 'Ventes',          to: '/directeur/ventes',    icon: <ShoppingCart className="h-4 w-4" /> },
    { label: 'Crédits',         to: '/directeur/credits',   icon: <CreditCard className="h-4 w-4" /> },
    { label: 'Achats',          to: '/directeur/achats',    icon: <Package className="h-4 w-4" /> },
    { label: 'Journal',         to: '/directeur/journal',   icon: <BookOpen className="h-4 w-4" /> },
  ],
  vendeur: [
    { label: 'Tableau de bord', to: '/vendeur/dashboard', icon: <LayoutDashboard className="h-4 w-4" /> },
    { label: 'Nouvelle vente',  to: '/vendeur/vente',     icon: <ShoppingCart className="h-4 w-4" /> },
    { label: 'Nouveau crédit',  to: '/vendeur/credit',    icon: <CreditCard className="h-4 w-4" /> },
  ],
}

interface Props { open: boolean; onClose: () => void }

export default function Sidebar({ open, onClose }: Props) {
  const role = useAuthStore(s => s.user?.role)
  const boutique = useAuthStore(s => s.user?.boutique_nom)
  const items = role ? navByRole[role] : []

  return (
    <>
      {open && (
        <div className="fixed inset-0 z-20 bg-black/30 lg:hidden" onClick={onClose} />
      )}
      <aside className={`fixed inset-y-0 left-0 z-30 flex w-60 flex-col bg-white border-r border-gray-200
        transition-transform duration-200 lg:relative lg:translate-x-0
        ${open ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex h-14 items-center justify-between px-4 border-b border-gray-100">
          <div>
            <p className="text-sm font-bold text-gray-900">MSTECH Gestion</p>
            {boutique && <p className="text-xs text-gray-400 truncate">{boutique}</p>}
          </div>
          <button onClick={onClose} className="lg:hidden rounded p-1 text-gray-400 hover:bg-gray-100">
            <X className="h-4 w-4" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5">
          {items.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            >
              {item.icon}
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-3 border-t border-gray-100">
          <p className="text-xs text-gray-400 text-center">© 2025 MSTECH</p>
        </div>
      </aside>
    </>
  )
}
