import client from './client'
import type { Utilisateur } from '../types'

export async function getUtilisateurs(): Promise<Utilisateur[]> {
  const { data } = await client.get<Utilisateur[]>('/pdg/utilisateurs')
  return data
}

export async function getUtilisateursBoutique(boutiqueId: number): Promise<Utilisateur[]> {
  const { data } = await client.get<Utilisateur[]>(`/pdg/boutiques/${boutiqueId}/utilisateurs`)
  return data
}

export async function creerUtilisateur(boutiqueId: number, payload: {
  nom: string; prenom: string; email: string; mot_de_passe: string; role: string
}): Promise<Utilisateur> {
  const { data } = await client.post<Utilisateur>(`/pdg/boutiques/${boutiqueId}/utilisateurs`, payload)
  return data
}

export async function getUtilisateursBoutiqueDir(): Promise<Utilisateur[]> {
  const { data } = await client.get<Utilisateur[]>('/directeur/utilisateurs')
  return data
}

export async function creerUtilisateurDir(payload: {
  nom: string; prenom: string; email: string; mot_de_passe: string
}): Promise<Utilisateur> {
  const { data } = await client.post<Utilisateur>('/directeur/utilisateurs', payload)
  return data
}
