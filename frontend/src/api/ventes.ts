import client from './client'
import type { Vente, ReponsePaginee } from '../types'

export async function getVentes(page = 1, taille = 20): Promise<ReponsePaginee<Vente>> {
  const { data } = await client.get<ReponsePaginee<Vente>>('/directeur/ventes', {
    params: { page, taille },
  })
  return data
}

export async function creerVente(payload: { montant: number; article?: string; quantite?: number }): Promise<Vente> {
  const { data } = await client.post<Vente>('/vendeur/ventes', payload)
  return data
}
