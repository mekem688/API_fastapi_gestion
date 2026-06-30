import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import type { Role } from '../../types'

export default function ProtectedRoute({ role }: { role: Role }) {
  const user = useAuthStore(s => s.user)
  if (!user) return <Navigate to="/login" replace />
  if (user.role !== role) return <Navigate to="/" replace />
  return <Outlet />
}
