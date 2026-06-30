import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Input  from '../../components/ui/Input'
import Modal  from '../../components/ui/Modal'
import Badge  from '../../components/ui/Badge'
import Spinner from '../../components/ui/Spinner'
import { getBoutiques, creerBoutique, modifierBoutique } from '../../api/boutiques'
import type { Boutique } from '../../types'

const schema = z.object({
  nom:       z.string().min(1, 'Nom requis'),
  adresse:   z.string().optional(),
  telephone: z.string().optional(),
})
type Form = z.infer<typeof schema>

export default function PdgBoutiques() {
  const qc = useQueryClient()
  const [modal, setModal] = useState<'creer' | Boutique | null>(null)

  const { data: boutiques = [], isLoading } = useQuery({
    queryKey: ['pdg', 'boutiques'],
    queryFn: getBoutiques,
  })

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<Form>({
    resolver: zodResolver(schema),
    values: modal && modal !== 'creer' ? { nom: modal.nom, adresse: modal.adresse ?? '', telephone: modal.telephone ?? '' } : undefined,
  })

  const mutCreer = useMutation({
    mutationFn: creerBoutique,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['pdg', 'boutiques'] }); setModal(null); reset() },
  })
  const mutModif = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<Boutique> }) => modifierBoutique(id, payload),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['pdg', 'boutiques'] }); setModal(null); reset() },
  })

  async function onSubmit(data: Form) {
    if (modal === 'creer') await mutCreer.mutateAsync(data)
    else if (modal) await mutModif.mutateAsync({ id: modal.id, payload: data })
  }

  if (isLoading) return <Spinner />

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">Boutiques</h1>
        <Button size="sm" onClick={() => { reset(); setModal('creer') }}>
          <Plus className="h-4 w-4" /> Nouvelle boutique
        </Button>
      </div>

      <Card>
        <CardHeader>
          <p className="text-sm font-medium text-gray-700">{boutiques.length} boutique{boutiques.length > 1 ? 's' : ''}</p>
        </CardHeader>
        <CardBody className="p-0">
          <div className="divide-y divide-gray-50">
            {boutiques.map(b => (
              <div key={b.id} className="flex items-center justify-between px-5 py-3 hover:bg-gray-50">
                <div>
                  <p className="font-medium text-gray-900">{b.nom}</p>
                  <p className="text-xs text-gray-400">{b.adresse ?? '—'} · {b.telephone ?? '—'}</p>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant={b.actif ? 'green' : 'gray'}>{b.actif ? 'Active' : 'Inactive'}</Badge>
                  <button onClick={() => setModal(b)} className="rounded p-1.5 text-gray-400 hover:bg-gray-100">
                    <Pencil className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            ))}
            {boutiques.length === 0 && (
              <p className="px-5 py-10 text-center text-sm text-gray-400">Aucune boutique</p>
            )}
          </div>
        </CardBody>
      </Card>

      <Modal
        open={modal !== null}
        onClose={() => { setModal(null); reset() }}
        titre={modal === 'creer' ? 'Nouvelle boutique' : `Modifier — ${(modal as Boutique)?.nom ?? ''}`}
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input label="Nom" error={errors.nom?.message} {...register('nom')} />
          <Input label="Adresse" {...register('adresse')} />
          <Input label="Téléphone" {...register('telephone')} />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => { setModal(null); reset() }}>Annuler</Button>
            <Button type="submit" loading={isSubmitting}>
              {modal === 'creer' ? 'Créer' : 'Enregistrer'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
