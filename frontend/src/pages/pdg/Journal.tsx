import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import Table      from '../../components/ui/Table'
import Pagination from '../../components/ui/Pagination'
import Spinner    from '../../components/ui/Spinner'
import { getJournalPdg } from '../../api/journal'
import { formatDateHeure } from '../../utils/format'
import type { EntreeJournal } from '../../types'

export default function PdgJournal() {
  const [page, setPage] = useState(1)
  const taille = 30

  const { data, isLoading } = useQuery({
    queryKey: ['pdg', 'journal', page],
    queryFn: () => getJournalPdg(page, taille),
  })

  if (isLoading) return <Spinner />

  return (
    <div className="space-y-5">
      <h1 className="text-xl font-bold text-gray-900">Journal d'activité global</h1>

      <Card>
        <CardHeader>
          <p className="text-sm font-medium text-gray-700">
            {data?.total ?? 0} entrée{(data?.total ?? 0) > 1 ? 's' : ''} au total
          </p>
        </CardHeader>
        <CardBody className="p-0">
          <Table<EntreeJournal>
            donnees={data?.resultats ?? []}
            keyFn={e => e.id}
            colonnes={[
              { header: 'Date/Heure',  render: e => <span className="text-xs text-gray-500 whitespace-nowrap">{formatDateHeure(e.date)}</span> },
              { header: 'Utilisateur', accessor: 'utilisateur_nom' },
              { header: 'Boutique',    render: e => e.boutique_nom ?? '—' },
              { header: 'Action',      accessor: 'action' },
              { header: 'Détails',     render: e => <span className="text-xs text-gray-500">{e.details ?? '—'}</span> },
            ]}
            vide="Aucune entrée dans le journal"
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
