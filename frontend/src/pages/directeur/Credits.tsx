import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, AlertCircle, Clock, CheckCircle2, TrendingDown } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Card, CardBody, CardHeader, StatCard } from '../../components/ui/Card'
import Table      from '../../components/ui/Table'
import Pagination from '../../components/ui/Pagination'
import Button     from '../../components/ui/Button'
import Input      from '../../components/ui/Input'
import Modal      from '../../components/ui/Modal'
import Spinner    from '../../components/ui/Spinner'
import { statutBadge } from '../../components/ui/Badge'
import {
  getCreditsVentes, creerCreditVente, payerCreditVente,
  getResumeCredits,
} from '../../api/credits'
import { formatMontant, formatDate } from '../../utils/format'
import type { CreditVente } from '../../types'

const schemaCredit = z.object({
  client_nom:        z.string().min(2, 'Nom client requis (2 car. min)'),
  client_telephone:  z.string().min(8, 'Téléphone requis (8 car. min)'),
  client_entreprise: z.string().optional(),
  client_adresse:    z.string().optional(),
  montant_total:     z.coerce.number().positive('Montant positif requis'),
  date_echeance:     z.string().min(1, 'Date d\'échéance requise'),
  note:              z.string().optional(),
})

const schemaPaiement = z.object({
  montant_verse: z.coerce.number().positive('Montant positif requis'),
  note:          z.string().optional(),
})

type FormCredit   = z.infer<typeof schemaCredit>
type FormPaiement = z.infer<typeof schemaPaiement>

const FILTRES = [
  { label: 'Tous',              valeur: undefined },
  { label: 'En cours',          valeur: 'en_cours' },
  { label: 'Partiel',           valeur: 'partiellement_paye' },
  { label: 'En retard',         valeur: 'en_retard' },
  { label: 'Soldés',            valeur: 'solde' },
]

export default function DirCredits() {
  const qc = useQueryClient()
  const [page, setPage]         = useState(1)
  const [filtre, setFiltre]     = useState<string | undefined>(undefined)
  const taille                  = 20
  const [modalCredit, setModalCredit]     = useState(false)
  const [modalPaiement, setModalPaiement] = useState<CreditVente | null>(null)

  const { data, isLoading }    = useQuery({
    queryKey: ['dir', 'credits', page, filtre],
    queryFn:  () => getCreditsVentes(page, taille, filtre),
  })
  const { data: resume }       = useQuery({
    queryKey: ['dir', 'credits', 'resume'],
    queryFn:  getResumeCredits,
  })

  const formCredit   = useForm<FormCredit>({   resolver: zodResolver(schemaCredit) })
  const formPaiement = useForm<FormPaiement>({ resolver: zodResolver(schemaPaiement) })

  const mutCredit = useMutation({
    mutationFn: creerCreditVente,
    onSuccess:  () => {
      qc.invalidateQueries({ queryKey: ['dir', 'credits'] })
      setModalCredit(false)
      formCredit.reset()
    },
  })

  const mutPaiement = useMutation({
    mutationFn: ({ id, montant_verse, note }: { id: number; montant_verse: number; note?: string }) =>
      payerCreditVente(id, montant_verse, note),
    onSuccess:  () => {
      qc.invalidateQueries({ queryKey: ['dir', 'credits'] })
      setModalPaiement(null)
      formPaiement.reset()
    },
  })

  if (isLoading) return <Spinner />

  return (
    <div className="space-y-5">

      {/* En-tête */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Crédits clients</h1>
          <p className="text-sm text-gray-500 mt-0.5">Argent que les clients vous doivent</p>
        </div>
        <Button size="sm" onClick={() => { formCredit.reset(); setModalCredit(true) }}>
          <Plus className="h-4 w-4" /> Nouveau crédit
        </Button>
      </div>

      {/* Cartes résumé */}
      {resume && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard
            titre="Total à encaisser"
            valeur={formatMontant(resume.total_a_encaisser)}
            sous={`${resume.nb_clients_debiteurs} client(s) débiteur(s)`}
            icone={<TrendingDown className="h-5 w-5" />}
            couleur="bg-orange-50 text-orange-500"
          />
          <StatCard
            titre="En retard"
            valeur={resume.nb_en_retard_ventes}
            sous="dépassement d'échéance"
            icone={<AlertCircle className="h-5 w-5" />}
            couleur="bg-red-50 text-red-500"
          />
          <StatCard
            titre="Dettes fournisseurs"
            valeur={formatMontant(resume.total_a_payer)}
            sous={`${resume.nb_fournisseurs_dus} fournisseur(s)`}
            icone={<Clock className="h-5 w-5" />}
            couleur="bg-yellow-50 text-yellow-600"
          />
          <StatCard
            titre="Solde net"
            valeur={formatMontant(resume.solde_net_credit)}
            sous={resume.solde_net_credit >= 0 ? 'en votre faveur' : 'déficitaire'}
            icone={<CheckCircle2 className="h-5 w-5" />}
            couleur={resume.solde_net_credit >= 0 ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-500'}
          />
        </div>
      )}

      {/* Filtres */}
      <div className="flex flex-wrap gap-2">
        {FILTRES.map(f => (
          <button
            key={f.label}
            onClick={() => { setFiltre(f.valeur); setPage(1) }}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors
              ${filtre === f.valeur
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Tableau */}
      <Card>
        <CardHeader>
          <p className="text-sm font-medium text-gray-700">
            {data?.total ?? 0} crédit{(data?.total ?? 0) > 1 ? 's' : ''}
            {filtre ? ` (${FILTRES.find(f => f.valeur === filtre)?.label})` : ''}
          </p>
        </CardHeader>
        <CardBody className="p-0">
          <Table<CreditVente>
            donnees={data?.resultats ?? []}
            keyFn={c => c.id}
            colonnes={[
              {
                header: 'Client',
                render: c => (
                  <div>
                    <p className="font-medium text-gray-900">{c.client_nom}</p>
                    <p className="text-xs text-gray-400">{c.client_telephone}</p>
                    {c.client_entreprise && (
                      <p className="text-xs text-gray-400 italic">{c.client_entreprise}</p>
                    )}
                  </div>
                ),
              },
              { header: 'Total',    render: c => formatMontant(c.montant_total) },
              { header: 'Payé',     render: c => formatMontant(c.montant_paye) },
              {
                header: 'Restant',
                render: c => (
                  <span className={`font-semibold ${c.montant_restant > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {formatMontant(c.montant_restant)}
                  </span>
                ),
              },
              { header: 'Échéance', render: c => formatDate(c.date_echeance) },
              { header: 'Statut',   render: c => statutBadge(c.statut) },
              {
                header: 'Action',
                render: c => c.statut !== 'solde' ? (
                  <button
                    onClick={() => { formPaiement.reset(); setModalPaiement(c) }}
                    className="text-xs font-medium text-primary-600 hover:text-primary-800 hover:underline"
                  >
                    Enregistrer paiement
                  </button>
                ) : (
                  <span className="text-xs text-green-600 font-medium">✓ Soldé</span>
                ),
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

      {/* Modal : nouveau crédit */}
      <Modal
        open={modalCredit}
        onClose={() => { setModalCredit(false); formCredit.reset() }}
        titre="Nouveau crédit client"
        taille="lg"
      >
        <form onSubmit={formCredit.handleSubmit(d => mutCredit.mutate(d))} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Nom du client *"
              placeholder="ex : Jean Dupont"
              error={formCredit.formState.errors.client_nom?.message}
              {...formCredit.register('client_nom')}
            />
            <Input
              label="Téléphone *"
              placeholder="ex : 690000000"
              error={formCredit.formState.errors.client_telephone?.message}
              {...formCredit.register('client_telephone')}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input label="Entreprise (optionnel)" {...formCredit.register('client_entreprise')} />
            <Input label="Adresse (optionnel)"    {...formCredit.register('client_adresse')} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Montant total (FCFA) *"
              type="number"
              error={formCredit.formState.errors.montant_total?.message}
              {...formCredit.register('montant_total')}
            />
            <Input
              label="Date d'échéance *"
              type="datetime-local"
              error={formCredit.formState.errors.date_echeance?.message}
              {...formCredit.register('date_echeance')}
            />
          </div>
          <Input label="Note (optionnel)" {...formCredit.register('note')} />

          <div className="rounded-lg bg-blue-50 border border-blue-100 px-3 py-2 text-xs text-blue-700">
            ℹ️ Le crédit est créé sans acompte. Pour enregistrer un premier versement, utilisez le bouton "Enregistrer paiement" après la création.
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => { setModalCredit(false); formCredit.reset() }}>
              Annuler
            </Button>
            <Button type="submit" loading={formCredit.formState.isSubmitting}>
              Créer le crédit
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal : enregistrer paiement */}
      <Modal
        open={modalPaiement !== null}
        onClose={() => { setModalPaiement(null); formPaiement.reset() }}
        titre={`Paiement reçu — ${modalPaiement?.client_nom ?? ''}`}
        taille="sm"
      >
        <form
          onSubmit={formPaiement.handleSubmit(d =>
            mutPaiement.mutate({ id: modalPaiement!.id, ...d })
          )}
          className="space-y-3"
        >
          {modalPaiement && (
            <div className="rounded-lg bg-gray-50 border border-gray-100 px-3 py-2 text-sm space-y-1">
              <p className="text-gray-600">
                Client : <strong>{modalPaiement.client_nom}</strong>
              </p>
              <p className="text-gray-600">
                Tél. : <strong>{modalPaiement.client_telephone}</strong>
              </p>
              <p className="text-gray-600">
                Restant : <strong className="text-red-600">{formatMontant(modalPaiement.montant_restant)}</strong>
              </p>
            </div>
          )}
          <Input
            label="Montant versé (FCFA) *"
            type="number"
            error={formPaiement.formState.errors.montant_verse?.message}
            {...formPaiement.register('montant_verse')}
          />
          <Input label="Note (optionnel)" {...formPaiement.register('note')} />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalPaiement(null)}>
              Annuler
            </Button>
            <Button type="submit" loading={formPaiement.formState.isSubmitting}>
              Confirmer le paiement
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
