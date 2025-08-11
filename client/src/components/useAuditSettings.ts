import {
  UseQueryResult,
  useQuery,
  UseMutationResult,
  useQueryClient,
  useMutation,
} from 'react-query'
import { fetchApi, ApiError } from '../utils/api'

export type AuditType =
  | 'BALLOT_POLLING'
  | 'BATCH_COMPARISON'
  | 'BALLOT_COMPARISON'
  | 'HYBRID'

export interface IAuditSettings {
  state: string | null
  electionName: string | null
  online: boolean | null
  randomSeed: string | null
  riskLimit: number | null
  auditType: AuditType
  auditMathType:
    | 'BRAVO'
    | 'MINERVA'
    | 'PROVIDENCE'
    | 'SUPERSIMPLE'
    | 'MACRO'
    | 'SUITE'
    | 'CARD_STYLE_DATA'
  auditName: string
}

type TNewSettings = Pick<
  IAuditSettings,
  'state' | 'electionName' | 'online' | 'randomSeed' | 'riskLimit'
>

const auditSettingsQueryKey = (electionId: string) => [
  'election',
  electionId,
  'settings',
]

export const useAuditSettings = (
  electionId: string
): UseQueryResult<IAuditSettings, ApiError> =>
  useQuery<IAuditSettings, ApiError>(auditSettingsQueryKey(electionId), () =>
    fetchApi(`/api/election/${electionId}/settings`)
  )

export const useUpdateAuditSettings = (
  electionId: string
): UseMutationResult<TNewSettings, ApiError, TNewSettings> => {
  const queryClient = useQueryClient()
  const putSettings = (newSettings: TNewSettings) => {
    const body = {
      ...queryClient.getQueryData<IAuditSettings>(
        auditSettingsQueryKey(electionId)
      ),
      ...newSettings,
    }
    return fetchApi(`/api/election/${electionId}/settings`, {
      method: 'PUT',
      body: JSON.stringify(body),
      headers: { 'Content-Type': 'application/json' },
    })
  }

  return useMutation(putSettings, {
    onSuccess: () => {
      queryClient.invalidateQueries(auditSettingsQueryKey(electionId))
    },
  })
}
