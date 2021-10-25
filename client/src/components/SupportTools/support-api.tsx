import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useHistory } from 'react-router-dom'
import { tryJson, addCSRFToken } from '../utilities'

export class ApiError extends Error {
  public statusCode: number

  public constructor(message: string, statusCode: number) {
    super(message)
    this.statusCode = statusCode
  }
}

export const fetchApi = async (url: string, options?: RequestInit) => {
  const response = await fetch(url, addCSRFToken(options))
  if (response.ok) return response.json()
  const text = await response.text()
  const { errors } = tryJson(text)
  const error = errors && errors.length && errors[0].message
  throw new ApiError(error || text, response.status)
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
  id: string
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

  return useMutation(postOrganization, {
    onSuccess: () => queryClient.invalidateQueries('organizations'),
  })
}

export const useOrganization = (organizationId: string) =>
  useQuery<IOrganization, Error>(['organizations', organizationId], () =>
    fetchApi(`/api/support/organizations/${organizationId}`)
  )

export const useRenameOrganization = (organizationId: string) => {
  const renameOrganization = (body: { name: string }) =>
    fetchApi(`/api/support/organizations/${organizationId}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
      headers: { 'Content-Type': 'application/json' },
    })

  const queryClient = useQueryClient()

  return useMutation(renameOrganization, {
    onSuccess: () =>
      queryClient.invalidateQueries(['organizations', organizationId]),
  })
}

export const useDeleteOrganization = (organizationId: string) => {
  const deleteOrganization = async () =>
    fetchApi(`/api/support/organizations/${organizationId}`, {
      method: 'DELETE',
    })

  const queryClient = useQueryClient()
  const history = useHistory()

  return useMutation(deleteOrganization, {
    onSuccess: () => {
      queryClient.removeQueries(['organizations', organizationId])
      queryClient.resetQueries('organizations')
      history.push('/support')
    },
  })
}

export const useCreateAuditAdmin = (organizationId: string) => {
  const postAuditAdmin = async (auditAdmin: IAuditAdmin) =>
    fetchApi(`/api/support/organizations/${organizationId}/audit-admins`, {
      method: 'POST',
      body: JSON.stringify(auditAdmin),
      headers: { 'Content-Type': 'application/json' },
    })

  const queryClient = useQueryClient()

  return useMutation(postAuditAdmin, {
    onSuccess: () =>
      queryClient.invalidateQueries(['organizations', organizationId]),
  })
}

export const useRemoveAuditAdmin = (organizationId: string) => {
  const removeAuditAdmin = async ({ auditAdminId }: { auditAdminId: string }) =>
    fetchApi(
      `/api/support/organizations/${organizationId}/audit-admins/${auditAdminId}`,
      { method: 'DELETE' }
    )

  const queryClient = useQueryClient()

  return useMutation(removeAuditAdmin, {
    onSuccess: () =>
      queryClient.invalidateQueries(['organizations', organizationId]),
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

  return useMutation(deleteAuditBoards, {
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

  return useMutation(reopenAuditBoard, {
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

  return useMutation(clearOfflineResults, {
    onSuccess: (_data, variables) =>
      queryClient.invalidateQueries([
        'jurisdictions',
        variables.jurisdictionId,
      ]),
  })
}
