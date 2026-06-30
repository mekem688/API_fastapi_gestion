import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { login } from '../../api/auth'
import Button from '../../components/ui/Button'
import Input  from '../../components/ui/Input'
import { useState } from 'react'
import type { User } from '../../types'

const schema = z.object({
  email:        z.string().email('Email invalide'),
  mot_de_passe: z.string().min(1, 'Mot de passe requis'),
})
type Form = z.infer<typeof schema>

export default function Login() {
  const navigate   = useNavigate()
  const loginStore = useAuthStore(s => s.login)
  const [erreur, setErreur] = useState('')

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Form>({
    resolver: zodResolver(schema),
  })

  async function onSubmit(data: Form) {
    setErreur('')
    try {
      const res = await login(data.email, data.mot_de_passe)
      const user: User = {
        id:          res.id,
        nom:         res.nom,
        prenom:      res.prenom,
        email:       res.email,
        role:        res.role,
        boutique_id: res.boutique_id,
      }
      loginStore(res.access_token, user)
      if (res.role === 'pdg')       navigate('/pdg/dashboard')
      else if (res.role === 'directeur') navigate('/directeur/dashboard')
      else navigate('/vendeur/dashboard')
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setErreur(msg ?? 'Identifiants incorrects. Vérifiez votre email et mot de passe.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary-600">
            <span className="text-xl font-bold text-white">M</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">MSTECH Gestion</h1>
          <p className="mt-1 text-sm text-gray-500">Connectez-vous à votre compte</p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Input
              label="Email"
              type="email"
              placeholder="nom@exemple.com"
              autoComplete="email"
              error={errors.email?.message}
              {...register('email')}
            />
            <Input
              label="Mot de passe"
              type="password"
              placeholder="••••••••"
              autoComplete="current-password"
              error={errors.mot_de_passe?.message}
              {...register('mot_de_passe')}
            />

            {erreur && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {erreur}
              </div>
            )}

            <Button type="submit" className="w-full" loading={isSubmitting}>
              Se connecter
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
