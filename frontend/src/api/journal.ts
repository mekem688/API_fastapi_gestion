import client from './client'
import type { EntreeJournal, ReponsePaginee } from '../types'

export async function getJournalPdg(page = 1, taille = 50): Promise<ReponsePaginee<EntreeJournal>> {
  const { data } = await client.get<ReponsePaginee<EntreeJournal>>('/pdg/journal', {
    params: { page, taille },
  })
  return data
}

export async function getJournalBoutiquePdg(boutiqueId: number, page = 1, taille = 50): Promise<ReponsePaginee<EntreeJournal>> {
  const { data } = await client.get<ReponsePaginee<EntreeJournal>>(`/pdg/boutiques/${boutiqueId}/journal`, {
    params: { page, taille },
  })
  return data
}

export async function getJournalDirecteur(page = 1, taille = 50): Promise<ReponsePaginee<EntreeJournal>> {
  const { data } = await client.get<ReponsePaginee<EntreeJournal>>('/directeur/journal', {
    params: { page, taille },
  })
  return data
}
