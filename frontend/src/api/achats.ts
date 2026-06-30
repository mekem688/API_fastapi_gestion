import client from './client'
import type { Achat, ReponsePaginee } from '../types'

export async function getAchats(page = 1, taille = 20): Promise<ReponsePaginee<Achat>> {
  const { data } = await client.get<ReponsePaginee<Achat>>('/directeur/achats', {
    params: { page, taille },
  })
  return data
}

export async function creerAchat(payload: {
  montant: number; article?: string; fournisseur?: string
}): Promise<Achat> {
  const { data } = await client.post<Achat>('/directeur/achats', payload)
  return data
}
