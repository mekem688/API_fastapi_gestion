import { LogOut, Menu } from 'lucide-react'
import { useAuthStore } from '../../stores/authStore'
import { useNavigate } from 'react-router-dom'
import { initiales, formatRole } from '../../utils/format'

interface Props { onMenuToggle: () => void }

export default function Header({ onMenuToggle }: Props) {
  const user     = useAuthStore(s => s.user)
  const logout   = useAuthStore(s => s.logout)
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <header className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-4 lg:px-6">
      <button
        onClick={onMenuToggle}
        className="lg:hidden rounded-lg p-1.5 text-gray-500 hover:bg-gray-100"
      >
        <Menu className="h-5 w-5" />
      </button>

      <div className="flex-1 lg:flex-none" />

      <div className="flex items-center gap-3">
        <div className="text-right hidden sm:block">
          <p className="text-sm font-medium text-gray-900">
            {user?.prenom} {user?.nom}
          </p>
          <p className="text-xs text-gray-400">{user ? formatRole(user.role) : ''}</p>
        </div>
        <div className="h-8 w-8 rounded-full bg-primary-100 text-primary-700
          flex items-center justify-center text-xs font-semibold uppercase">
          {user ? initiales(user.nom, user.prenom) : '?'}
        </div>
        <button
          onClick={handleLogout}
          title="Se déconnecter"
          className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </header>
  )
}
