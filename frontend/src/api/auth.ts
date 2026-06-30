import client from './client'
import type { TokenReponse } from '../types'

export async function login(nom_utilisateur: string, mot_de_passe: string): Promise<TokenReponse> {
  const { data } = await client.post<TokenReponse>('/auth/connexion', { nom_utilisateur, mot_de_passe })
  return data
}
