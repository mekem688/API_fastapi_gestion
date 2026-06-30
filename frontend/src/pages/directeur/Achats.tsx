import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import Table      from '../../components/ui/Table'
import Pagination from '../../components/ui/Pagination'
import Button     from '../../components/ui/Button'
import Input      from '../../components/ui/Input'
import Modal      from '../../components/ui/Modal'
import Spinner    from '../../components/ui/Spinner'
import { getAchats, creerAchat } from '../../api/achats'
import { formatMontant, formatDateHeure } from '../../utils/format'
import type { Achat } from '../../types'

const schema = z.object({
  montant:     z.coerce.number().positive('Montant positif requis'),
  article:     z.string().optional(),
  fournisseur: z.string().optional(),
})
type Form = z.infer<typeof schema>

export default function DirAchats() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const taille = 20
  const [modal, setModal] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['dir', 'achats', page],
    queryFn: () => getAchats(page, taille),
  })

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<Form>({
    resolver: zodResolver(schema),
  })

  const mutCreer = useMutation({
    mutationFn: creerAchat,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['dir', 'achats'] }); setModal(false); reset() },
  })

  if (isLoading) return <Spinner />

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">Achats / Approvisionnements</h1>
        <Button size="sm" onClick={() => { reset(); setModal(true) }}>
          <Plus className="h-4 w-4" /> Nouvel achat
        </Button>
      </div>

      <Card>
        <CardHeader>
          <p className="text-sm font-medium text-gray-700">{data?.total ?? 0} achat{(data?.total ?? 0) > 1 ? 's' : ''}</p>
        </CardHeader>
        <CardBody className="p-0">
          <Table<Achat>
            donnees={data?.resultats ?? []}
            keyFn={a => a.id}
            colonnes={[
              { header: 'Date',        render: a => <span className="text-xs text-gray-500">{formatDateHeure(a.date)}</span> },
              { header: 'Article',     render: a => a.article ?? '—' },
              { header: 'Fournisseur', render: a => a.fournisseur ?? '—' },
              { header: 'Montant',     render: a => <span className="font-medium">{formatMontant(a.montant)}</span> },
            ]}
            vide="Aucun achat enregistré"
          />
          {data && (
            <div className="px-5">
              <Pagination page={page} nbPages={data.nb_pages} total={data.total} taille={taille} onChange={setPage} />
            </div>
          )}
        </CardBody>
      </Card>

      <Modal open={modal} onClose={() => { setModal(false); reset() }} titre="Nouvel achat">
        <form onSubmit={handleSubmit(d => mutCreer.mutate(d))} className="space-y-3">
          <Input label="Article / Description" {...register('article')} />
          <Input label="Fournisseur"           {...register('fournisseur')} />
          <Input label="Montant (FCFA)" type="number" error={errors.montant?.message} {...register('montant')} />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => { setModal(false); reset() }}>Annuler</Button>
            <Button type="submit" loading={isSubmitting}>Enregistrer</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
