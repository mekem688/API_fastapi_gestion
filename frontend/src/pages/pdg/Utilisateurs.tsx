import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import Table   from '../../components/ui/Table'
import Button  from '../../components/ui/Button'
import Input   from '../../components/ui/Input'
import Modal   from '../../components/ui/Modal'
import Badge   from '../../components/ui/Badge'
import Spinner from '../../components/ui/Spinner'
import { getUtilisateurs, creerUtilisateur } from '../../api/utilisateurs'
import { getBoutiques } from '../../api/boutiques'
import { formatRole } from '../../utils/format'
import type { Utilisateur } from '../../types'

const schema = z.object({
  boutique_id:  z.coerce.number().min(1, 'Sélectionnez une boutique'),
  nom:          z.string().min(1, 'Nom requis'),
  prenom:       z.string().min(1, 'Prénom requis'),
  email:        z.string().email('Email invalide'),
  mot_de_passe: z.string().min(6, '6 caractères minimum'),
  role:         z.enum(['directeur', 'vendeur']),
})
type Form = z.infer<typeof schema>

export default function PdgUtilisateurs() {
  const qc = useQueryClient()
  const [modal, setModal] = useState(false)

  const { data: utilisateurs = [], isLoading } = useQuery({ queryKey: ['pdg', 'utilisateurs'], queryFn: getUtilisateurs })
  const { data: boutiques    = [] }            = useQuery({ queryKey: ['pdg', 'boutiques'],    queryFn: getBoutiques })

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: { role: 'vendeur' },
  })

  const mutCreer = useMutation({
    mutationFn: ({ boutique_id, ...rest }: Form) => creerUtilisateur(boutique_id, rest),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['pdg', 'utilisateurs'] }); setModal(false); reset() },
  })

  if (isLoading) return <Spinner />

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">Utilisateurs</h1>
        <Button size="sm" onClick={() => { reset(); setModal(true) }}>
          <Plus className="h-4 w-4" /> Nouvel utilisateur
        </Button>
      </div>

      <Card>
        <CardHeader>
          <p className="text-sm font-medium text-gray-700">{utilisateurs.length} utilisateur{utilisateurs.length > 1 ? 's' : ''}</p>
        </CardHeader>
        <CardBody className="p-0">
          <Table<Utilisateur>
            donnees={utilisateurs}
            keyFn={u => u.id}
            colonnes={[
              { header: 'Nom',       render: u => `${u.prenom} ${u.nom}` },
              { header: 'Email',     accessor: 'email' },
              { header: 'Rôle',      render: u => <Badge variant={u.role === 'directeur' ? 'blue' : 'gray'}>{formatRole(u.role)}</Badge> },
              { header: 'Boutique',  render: u => u.boutique_nom ?? '—' },
              { header: 'Statut',    render: u => <Badge variant={u.actif ? 'green' : 'red'}>{u.actif ? 'Actif' : 'Inactif'}</Badge> },
            ]}
            vide="Aucun utilisateur"
          />
        </CardBody>
      </Card>

      <Modal open={modal} onClose={() => { setModal(false); reset() }} titre="Nouvel utilisateur">
        <form onSubmit={handleSubmit(d => mutCreer.mutate(d))} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Input label="Prénom" error={errors.prenom?.message} {...register('prenom')} />
            <Input label="Nom"    error={errors.nom?.message}    {...register('nom')} />
          </div>
          <Input label="Email" type="email" error={errors.email?.message} {...register('email')} />
          <Input label="Mot de passe" type="password" error={errors.mot_de_passe?.message} {...register('mot_de_passe')} />
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-700">Boutique</label>
            <select {...register('boutique_id')} className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
              <option value="">Choisir…</option>
              {boutiques.map(b => <option key={b.id} value={b.id}>{b.nom}</option>)}
            </select>
            {errors.boutique_id && <p className="text-xs text-red-600">{errors.boutique_id.message}</p>}
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-700">Rôle</label>
            <select {...register('role')} className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
              <option value="vendeur">Vendeur</option>
              <option value="directeur">Directeur</option>
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => { setModal(false); reset() }}>Annuler</Button>
            <Button type="submit" loading={isSubmitting}>Créer</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
