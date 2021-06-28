import { useQuery, useMutation, useQueryClient } from 'react-query'
import { tryJson } from '../utilities'

const fetchApi = async (url: string, options?: RequestInit) => {
  const response = await fetch(url, options)
  if (response.ok) return response.json()
  const text = await response.text()
  const { errors } = tryJson(text)
  const error = errors && errors.length && errors[0].message
  throw new Error(error || text)
}

export interface IOrganizationBase {
  id: string
  name: string
}

export interface IOrganization extends IOrganizationBase {
  elections: IElectionBase[]
  auditAdmins: IAuditAdmin[]
}

export interface IElectionBase {
  id: string
  auditName: string
  auditType:
    | 'BALLOT_POLLING'
    | 'BALLOT_COMPARISON'
    | 'BATCH_COMPARISON'
    | 'HYBRID'
  online: boolean
}

export interface IAuditAdmin {
  email: string
}

export interface IElection extends IElectionBase {
  jurisdictions: IJurisdictionBase[]
}

export interface IJurisdictionBase {
  id: string
  name: string
}

export interface IJurisdiction extends IJurisdictionBase {
  election: IElectionBase
  jurisdictionAdmins: IJurisdictionAdmin[]
  auditBoards: IAuditBoard[]
  recordedResultsAt: string | null
}

export interface IJurisdictionAdmin {
  email: string
}

export interface IAuditBoard {
  id: string
  name: string
  signedOffAt: string | null
}

export const useOrganizations = () =>
  useQuery<IOrganizationBase[], Error>('organizations', () =>
    fetchApi('/api/support/organizations')
  )

export const useCreateOrganization = () => {
  const postOrganization = async ({ name }: { name: string }) =>
    fetchApi(`/api/support/organizations`, {
      method: 'POST',
      body: JSON.stringify({ name }),
      headers: { 'Content-Type': 'application/json' },
    })

  const queryClient = useQueryClient()

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return useMutation<any, Error, any>(postOrganization, {
    onSuccess: () => queryClient.invalidateQueries('organizations'),
  })
}

export const useOrganization = (organizationId: string) =>
  useQuery<IOrganization, Error>(['organizations', organizationId], () =>
    fetchApi(`/api/support/organizations/${organizationId}`)
  )

export const useCreateAuditAdmin = () => {
  const postAuditAdmin = async ({
    organizationId,
    auditAdmin,
  }: {
    organizationId: string
    auditAdmin: IAuditAdmin
  }) =>
    fetchApi(`/api/support/organizations/${organizationId}/audit-admins`, {
      method: 'POST',
      body: JSON.stringify(auditAdmin),
      headers: { 'Content-Type': 'application/json' },
    })

  const queryClient = useQueryClient()

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return useMutation<any, Error, any>(postAuditAdmin, {
    onSuccess: (_data, variables) =>
      queryClient.invalidateQueries([
        'organizations',
        variables.organizationId,
      ]),
  })
}

export const useElection = (electionId: string) =>
  useQuery<IElection, Error>(['elections', electionId], () =>
    fetchApi(`/api/support/elections/${electionId}`)
  )

export const useJurisdiction = (jurisdictionId: string) =>
  useQuery<IJurisdiction, Error>(['jurisdictions', jurisdictionId], () =>
    fetchApi(`/api/support/jurisdictions/${jurisdictionId}`)
  )

export const useClearAuditBoards = () => {
  const deleteAuditBoards = async ({
    jurisdictionId,
  }: {
    jurisdictionId: string
  }) =>
    fetchApi(`/api/support/jurisdictions/${jurisdictionId}/audit-boards`, {
      method: 'DELETE',
    })

  const queryClient = useQueryClient()

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return useMutation<any, Error, any>(deleteAuditBoards, {
    onSuccess: (_data, variables) =>
      queryClient.invalidateQueries([
        'jurisdictions',
        variables.jurisdictionId,
      ]),
  })
}

export const useReopenAuditBoard = () => {
  const reopenAuditBoard = async ({
    auditBoardId,
  }: {
    jurisdictionId: string
    auditBoardId: string
  }) =>
    fetchApi(`/api/support/audit-boards/${auditBoardId}/sign-off`, {
      method: 'DELETE',
    })

  const queryClient = useQueryClient()

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return useMutation<any, Error, any>(reopenAuditBoard, {
    onSuccess: (_data, variables) =>
      queryClient.invalidateQueries([
        'jurisdictions',
        variables.jurisdictionId,
      ]),
  })
}

export const useClearOfflineResults = () => {
  const clearOfflineResults = async ({
    jurisdictionId,
  }: {
    jurisdictionId: string
  }) =>
    fetchApi(`/api/support/jurisdictions/${jurisdictionId}/results`, {
      method: 'DELETE',
    })

  const queryClient = useQueryClient()

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return useMutation<any, Error, any>(clearOfflineResults, {
    onSuccess: (_data, variables) =>
      queryClient.invalidateQueries([
        'jurisdictions',
        variables.jurisdictionId,
      ]),
  })
}
