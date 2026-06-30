import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { CheckCircle } from 'lucide-react'
import { useState } from 'react'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import Button  from '../../components/ui/Button'
import Input   from '../../components/ui/Input'
import { creerVente } from '../../api/ventes'
import { formatMontant } from '../../utils/format'

const schema = z.object({
  article:  z.string().min(1, 'Article requis'),
  quantite: z.coerce.number().int().positive('Quantité positive').optional(),
  montant:  z.coerce.number().positive('Montant positif requis'),
})
type Form = z.infer<typeof schema>

export default function VenNouvelleVente() {
  const [succes, setSucces] = useState<number | null>(null)

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<Form>({
    resolver: zodResolver(schema),
  })

  const mut = useMutation({
    mutationFn: creerVente,
    onSuccess: (v) => { setSucces(v.montant); reset() },
  })

  return (
    <div className="max-w-md space-y-5">
      <h1 className="text-xl font-bold text-gray-900">Nouvelle vente</h1>

      {succes !== null && (
        <div className="flex items-center gap-3 rounded-xl bg-green-50 border border-green-200 px-4 py-3">
          <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-green-800">Vente enregistrée !</p>
            <p className="text-xs text-green-600">Montant : {formatMontant(succes)}</p>
          </div>
          <button onClick={() => setSucces(null)} className="ml-auto text-xs text-green-500 hover:underline">
            Fermer
          </button>
        </div>
      )}

      <Card>
        <CardHeader>
          <p className="text-sm font-medium text-gray-700">Informations de la vente</p>
        </CardHeader>
        <CardBody>
          <form onSubmit={handleSubmit(d => mut.mutate(d))} className="space-y-4">
            <Input
              label="Article vendu"
              placeholder="ex : Sac de riz 25kg"
              error={errors.article?.message}
              {...register('article')}
            />
            <Input
              label="Quantité"
              type="number"
              placeholder="1"
              error={errors.quantite?.message}
              {...register('quantite')}
            />
            <Input
              label="Montant total (FCFA)"
              type="number"
              placeholder="5000"
              error={errors.montant?.message}
              {...register('montant')}
            />
            <Button type="submit" className="w-full" loading={isSubmitting} size="lg">
              Enregistrer la vente
            </Button>
          </form>
        </CardBody>
      </Card>
    </div>
  )
}
