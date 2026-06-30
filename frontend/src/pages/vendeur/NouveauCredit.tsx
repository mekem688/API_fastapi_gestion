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
  client_nom:    z.string().min(1, 'Nom du client requis'),
  montant_total: z.coerce.number().positive('Montant positif requis'),
  montant_paye:  z.coerce.number().min(0, 'Acompte ≥ 0'),
  echeance:      z.string().optional(),
}).refine(d => d.montant_paye <= d.montant_total, {
  message: 'L\'acompte ne peut pas dépasser le total',
  path: ['montant_paye'],
})
type Form = z.infer<typeof schema>

export default function VenNouveauCredit() {
  const [succes, setSucces] = useState<{ client: string; reste: number } | null>(null)

  const { register, handleSubmit, reset, watch, formState: { errors, isSubmitting } } = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: { montant_paye: 0 },
  })

  const total = watch('montant_total') || 0
  const paye  = watch('montant_paye')  || 0
  const reste = Math.max(0, total - paye)

  const mut = useMutation({
    mutationFn: creerCreditVente,
    onSuccess: (c) => { setSucces({ client: c.client_nom, reste: c.reste }); reset() },
  })

  return (
    <div className="max-w-md space-y-5">
      <h1 className="text-xl font-bold text-gray-900">Nouveau crédit client</h1>

      {succes && (
        <div className="flex items-center gap-3 rounded-xl bg-green-50 border border-green-200 px-4 py-3">
          <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-green-800">Crédit enregistré pour {succes.client}</p>
            <p className="text-xs text-green-600">Restant à payer : {formatMontant(succes.reste)}</p>
          </div>
          <button onClick={() => setSucces(null)} className="ml-auto text-xs text-green-500 hover:underline">
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
            <Input
              label="Nom du client"
              placeholder="ex : Jean Dupont"
              error={errors.client_nom?.message}
              {...register('client_nom')}
            />
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Montant total (FCFA)"
                type="number"
                placeholder="10000"
                error={errors.montant_total?.message}
                {...register('montant_total')}
              />
              <Input
                label="Acompte versé (FCFA)"
                type="number"
                placeholder="0"
                error={errors.montant_paye?.message}
                {...register('montant_paye')}
              />
            </div>

            {total > 0 && (
              <div className="rounded-lg bg-orange-50 border border-orange-100 px-3 py-2 text-sm">
                <span className="text-orange-700">Restant à payer : </span>
                <strong className="text-orange-800">{formatMontant(reste)}</strong>
              </div>
            )}

            <Input
              label="Date d'échéance (optionnel)"
              type="date"
              {...register('echeance')}
            />
            <Button type="submit" className="w-full" loading={isSubmitting} size="lg">
              Enregistrer le crédit
            </Button>
          </form>
        </CardBody>
      </Card>
    </div>
  )
}
