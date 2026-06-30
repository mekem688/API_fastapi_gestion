import client from './client'
import type { CreditVente, CreditAchat, ReponsePaginee } from '../types'

// ── Ventes à crédit (clients qui doivent de l'argent) ────────

export async function getCreditsVentes(
  page = 1, taille = 20, statut?: string,
): Promise<ReponsePaginee<CreditVente>> {
  const { data } = await client.get<ReponsePaginee<CreditVente>>('/credits/ventes', {
    params: { page, taille, ...(statut ? { statut } : {}) },
  })
  return data
}

export async function getCreditVente(id: number): Promise<CreditVente> {
  const { data } = await client.get<CreditVente>(`/credits/ventes/${id}`)
  return data
}

export async function creerCreditVente(payload: {
  client_nom:       string
  client_telephone: string
  client_entreprise?: string
  client_adresse?:   string
  montant_total:    number
  date_echeance:    string
  note?:            string
}): Promise<CreditVente> {
  const { data } = await client.post<CreditVente>('/credits/ventes', payload)
  return data
}

export async function payerCreditVente(
  id: number, montant_verse: number, note?: string,
): Promise<{ id: number; montant_verse: number; date_paiement: string }> {
  const { data } = await client.post(`/credits/ventes/${id}/paiement`, { montant_verse, note })
  return data
}

export async function historiquePaiementsVente(id: number) {
  const { data } = await client.get(`/credits/ventes/${id}/paiements`)
  return data
}

// ── Achats à crédit (la boutique doit aux fournisseurs) ──────

export async function getCreditsAchats(
  page = 1, taille = 20, statut?: string,
): Promise<ReponsePaginee<CreditAchat>> {
  const { data } = await client.get<ReponsePaginee<CreditAchat>>('/credits/achats', {
    params: { page, taille, ...(statut ? { statut } : {}) },
  })
  return data
}

export async function creerCreditAchat(payload: {
  fournisseur_nom:       string
  fournisseur_telephone: string
  fournisseur_entreprise?: string
  fournisseur_adresse?:    string
  montant_total:         number
  date_echeance:         string
  note?:                 string
}): Promise<CreditAchat> {
  const { data } = await client.post<CreditAchat>('/credits/achats', payload)
  return data
}

export async function payerCreditAchat(
  id: number, montant_verse: number, note?: string,
): Promise<{ id: number; montant_verse: number; date_paiement: string }> {
  const { data } = await client.post(`/credits/achats/${id}/paiement`, { montant_verse, note })
  return data
}

// ── Résumé financier ─────────────────────────────────────────

export interface ResumeCredits {
  boutique_id:          number
  total_a_encaisser:    number
  nb_clients_debiteurs: number
  nb_en_retard_ventes:  number
  total_a_payer:        number
  nb_fournisseurs_dus:  number
  nb_en_retard_achats:  number
  solde_net_credit:     number
}

export async function getResumeCredits(): Promise<ResumeCredits> {
  const { data } = await client.get<ResumeCredits>('/credits/resume')
  return data
}
