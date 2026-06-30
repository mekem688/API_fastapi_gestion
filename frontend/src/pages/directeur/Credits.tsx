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
import { statutBadge } from '../../components/ui/Badge'
import { getCreditsVentes, creerCreditVente, payerCreditVente } from '../../api/credits'
import { formatMontant, formatDate } from '../../utils/format'
import type { CreditVente } from '../../types'

const schemaNv = z.object({
  client_nom:    z.string().min(1, 'Nom client requis'),
  montant_total: z.coerce.number().positive('Montant positif'),
  montant_paye:  z.coerce.number().min(0),
  echeance:      z.string().optional(),
})
const schemaPay = z.object({ montant: z.coerce.number().positive() })

type FormNv  = z.infer<typeof schemaNv>
type FormPay = z.infer<typeof schemaPay>

export default function DirCredits() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const taille = 20
  const [modalNv, setModalNv]     = useState(false)
  const [modalPay, setModalPay]   = useState<CreditVente | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['dir', 'credits', page],
    queryFn: () => getCreditsVentes(page, taille),
  })

  const formNv = useForm<FormNv>({ resolver: zodResolver(schemaNv), defaultValues: { montant_paye: 0 } })
  const formPay = useForm<FormPay>({ resolver: zodResolver(schemaPay) })

  const mutNv = useMutation({
    mutationFn: creerCreditVente,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['dir', 'credits'] }); setModalNv(false); formNv.reset() },
  })
  const mutPay = useMutation({
    mutationFn: ({ id, montant }: { id: number; montant: number }) => payerCreditVente(id, montant),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['dir', 'credits'] }); setModalPay(null); formPay.reset() },
  })

  if (isLoading) return <Spinner />

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">Crédits clients</h1>
        <Button size="sm" onClick={() => { formNv.reset(); setModalNv(true) }}>
          <Plus className="h-4 w-4" /> Nouveau crédit
        </Button>
      </div>

      <Card>
        <CardHeader>
          <p className="text-sm font-medium text-gray-700">{data?.total ?? 0} crédit{(data?.total ?? 0) > 1 ? 's' : ''}</p>
        </CardHeader>
        <CardBody className="p-0">
          <Table<CreditVente>
            donnees={data?.resultats ?? []}
            keyFn={c => c.id}
            colonnes={[
              { header: 'Client',   accessor: 'client_nom' },
              { header: 'Total',    render: c => formatMontant(c.montant_total) },
              { header: 'Payé',     render: c => formatMontant(c.montant_paye) },
              { header: 'Restant',  render: c => <span className="font-semibold text-red-600">{formatMontant(c.reste)}</span> },
              { header: 'Échéance', render: c => c.echeance ? formatDate(c.echeance) : '—' },
              { header: 'Statut',   render: c => statutBadge(c.statut) },
              {
                header: 'Action',
                render: c => c.statut !== 'solde' ? (
                  <button
                    onClick={() => { formPay.reset(); setModalPay(c) }}
                    className="text-xs text-primary-600 hover:underline"
                  >Payer</button>
                ) : null,
              },
            ]}
            vide="Aucun crédit enregistré"
          />
          {data && (
            <div className="px-5">
              <Pagination page={page} nbPages={data.nb_pages} total={data.total} taille={taille} onChange={setPage} />
            </div>
          )}
        </CardBody>
      </Card>

      <Modal open={modalNv} onClose={() => { setModalNv(false); formNv.reset() }} titre="Nouveau crédit client">
        <form onSubmit={formNv.handleSubmit(d => mutNv.mutate(d))} className="space-y-3">
          <Input label="Nom du client" error={formNv.formState.errors.client_nom?.message} {...formNv.register('client_nom')} />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Montant total" type="number" error={formNv.formState.errors.montant_total?.message} {...formNv.register('montant_total')} />
            <Input label="Acompte versé" type="number" {...formNv.register('montant_paye')} />
          </div>
          <Input label="Date d'échéance" type="date" {...formNv.register('echeance')} />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => { setModalNv(false); formNv.reset() }}>Annuler</Button>
            <Button type="submit" loading={formNv.formState.isSubmitting}>Enregistrer</Button>
          </div>
        </form>
      </Modal>

      <Modal open={modalPay !== null} onClose={() => { setModalPay(null); formPay.reset() }} titre={`Paiement — ${modalPay?.client_nom ?? ''}`} taille="sm">
        <form onSubmit={formPay.handleSubmit(d => mutPay.mutate({ id: modalPay!.id, montant: d.montant }))} className="space-y-3">
          {modalPay && <p className="text-sm text-gray-600">Restant : <strong>{formatMontant(modalPay.reste)}</strong></p>}
          <Input label="Montant payé" type="number" error={formPay.formState.errors.montant?.message} {...formPay.register('montant')} />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalPay(null)}>Annuler</Button>
            <Button type="submit" loading={formPay.formState.isSubmitting}>Confirmer</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
