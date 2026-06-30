import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { CheckCircle } from 'lucide-react'
import { useState } from 'react'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Input  from '../../components/ui/Input'
import { creerCreditVente } from '../../api/credits'
import { formatMontant } from '../../utils/format'

const schema = z.object({
  client_nom:        z.string().min(2, 'Nom du client requis (2 car. min)'),
  client_telephone:  z.string().min(8, 'Téléphone requis (8 chiffres min)'),
  client_entreprise: z.string().optional(),
  client_adresse:    z.string().optional(),
  montant_total:     z.coerce.number().positive('Montant positif requis'),
  date_echeance:     z.string().min(1, "Date d'échéance requise"),
  note:              z.string().optional(),
})
type Form = z.infer<typeof schema>

export default function VenNouveauCredit() {
  const [succes, setSucces] = useState<{ client: string; reste: number } | null>(null)

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<Form>({
    resolver: zodResolver(schema),
  })

  const mut = useMutation({
    mutationFn: creerCreditVente,
    onSuccess: (c) => {
      setSucces({ client: c.client_nom, reste: c.montant_restant })
      reset()
    },
  })

  return (
    <div className="max-w-lg space-y-5">
      <h1 className="text-xl font-bold text-gray-900">Nouveau crédit client</h1>

      {succes && (
        <div className="flex items-start gap-3 rounded-xl bg-green-50 border border-green-200 px-4 py-3">
          <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-green-800">
              Crédit enregistré pour {succes.client}
            </p>
            <p className="text-xs text-green-600 mt-0.5">
              Montant dû : {formatMontant(succes.reste)}
            </p>
            <p className="text-xs text-green-500 mt-1">
              Le directeur peut enregistrer les versements depuis son espace.
            </p>
          </div>
          <button onClick={() => setSucces(null)} className="text-xs text-green-500 hover:underline flex-shrink-0">
            Fermer
          </button>
        </div>
      )}

      <Card>
        <CardHeader>
          <p className="text-sm font-medium text-gray-700">Informations du crédit</p>
        </CardHeader>
        <CardBody>
          <form onSubmit={handleSubmit(d => mut.mutate(d))} className="space-y-4">

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input
                label="Nom du client *"
                placeholder="ex : Jean Dupont"
                error={errors.client_nom?.message}
                {...register('client_nom')}
              />
              <Input
                label="Téléphone *"
                placeholder="ex : 690000000"
                error={errors.client_telephone?.message}
                {...register('client_telephone')}
              />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input
                label="Entreprise (optionnel)"
                placeholder="ex : Société XYZ"
                {...register('client_entreprise')}
              />
              <Input
                label="Adresse (optionnel)"
                placeholder="ex : Rue des Fleurs, Yaoundé"
                {...register('client_adresse')}
              />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input
                label="Montant total (FCFA) *"
                type="number"
                placeholder="10000"
                error={errors.montant_total?.message}
                {...register('montant_total')}
              />
              <Input
                label="Date d'échéance *"
                type="datetime-local"
                error={errors.date_echeance?.message}
                {...register('date_echeance')}
              />
            </div>

            <Input
              label="Note (optionnel)"
              placeholder="ex : Livraison de 2 sacs de riz"
              {...register('note')}
            />

            <div className="rounded-lg bg-orange-50 border border-orange-100 px-3 py-2 text-xs text-orange-700">
              ℹ️ Le téléphone du client est obligatoire pour la traçabilité et le suivi des paiements.
            </div>

            <Button type="submit" className="w-full" loading={isSubmitting} size="lg">
              Enregistrer le crédit
            </Button>
          </form>
        </CardBody>
      </Card>
    </div>
  )
}
