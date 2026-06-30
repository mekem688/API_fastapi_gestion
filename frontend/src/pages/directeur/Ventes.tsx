import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import Table      from '../../components/ui/Table'
import Pagination from '../../components/ui/Pagination'
import Spinner    from '../../components/ui/Spinner'
import { getVentes } from '../../api/ventes'
import { formatMontant, formatDateHeure } from '../../utils/format'
import type { Vente } from '../../types'

export default function DirVentes() {
  const [page, setPage] = useState(1)
  const taille = 20

  const { data, isLoading } = useQuery({
    queryKey: ['dir', 'ventes', page],
    queryFn: () => getVentes(page, taille),
  })

  if (isLoading) return <Spinner />

  return (
    <div className="space-y-5">
      <h1 className="text-xl font-bold text-gray-900">Ventes</h1>

      <Card>
        <CardHeader>
          <p className="text-sm font-medium text-gray-700">
            {data?.total ?? 0} vente{(data?.total ?? 0) > 1 ? 's' : ''} au total
          </p>
        </CardHeader>
        <CardBody className="p-0">
          <Table<Vente>
            donnees={data?.resultats ?? []}
            keyFn={v => v.id}
            colonnes={[
              { header: 'Date',    render: v => <span className="text-xs text-gray-500">{formatDateHeure(v.date)}</span> },
              { header: 'Article', render: v => v.article ?? '—' },
              { header: 'Qté',     render: v => v.quantite ?? '—', className: 'text-center' },
              { header: 'Montant', render: v => <span className="font-medium">{formatMontant(v.montant)}</span> },
              { header: 'Vendeur', render: v => v.vendeur_nom ?? `#${v.vendeur_id}` },
            ]}
            vide="Aucune vente enregistrée"
          />
          {data && (
            <div className="px-5">
              <Pagination page={page} nbPages={data.nb_pages} total={data.total} taille={taille} onChange={setPage} />
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  )
}
