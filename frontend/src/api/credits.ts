import client from './client'
import type { CreditVente, CreditAchat, ReponsePaginee } from '../types'

export async function getCreditsVentes(page = 1, taille = 20): Promise<ReponsePaginee<CreditVente>> {
  const { data } = await client.get<ReponsePaginee<CreditVente>>('/directeur/credits/ventes', {
    params: { page, taille },
  })
  return data
}

export async function creerCreditVente(payload: {
  client_nom: string; montant_total: number; montant_paye: number; echeance?: string
}): Promise<CreditVente> {
  const { data } = await client.post<CreditVente>('/directeur/credits/ventes', payload)
  return data
}

export async function payerCreditVente(id: number, montant: number): Promise<CreditVente> {
  const { data } = await client.post<CreditVente>(`/directeur/credits/ventes/${id}/paiement`, { montant })
  return data
}

export async function getCreditsAchats(page = 1, taille = 20): Promise<ReponsePaginee<CreditAchat>> {
  const { data } = await client.get<ReponsePaginee<CreditAchat>>('/directeur/credits/achats', {
    params: { page, taille },
  })
  return data
}

export async function creerCreditAchat(payload: {
  fournisseur_nom: string; montant_total: number; montant_paye: number; echeance?: string
}): Promise<CreditAchat> {
  const { data } = await client.post<CreditAchat>('/directeur/credits/achats', payload)
  return data
}

export async function payerCreditAchat(id: number, montant: number): Promise<CreditAchat> {
  const { data } = await client.post<CreditAchat>(`/directeur/credits/achats/${id}/paiement`, { montant })
  return data
}
