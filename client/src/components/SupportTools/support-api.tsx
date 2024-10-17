/* eslint-disable @typescript-eslint/explicit-module-boundary-types */
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useHistory } from 'react-router-dom'
import { fetchApi } from '../../utils/api'

export interface IOrganizationBase {
  id: string
  name: string
}

export interface IOrganization extends IOrganizationBase {
  defaultState: string | null
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
  deletedAt: string | null
  createdAt: string
}

export interface IAuditAdmin {
  id: string
  email: string
}

export interface IRound {
  id: string
  endedAt: string | null
  roundNum: number
}

export interface IElectionWithOrg extends IElectionBase {
  organization: IOrganizationBase
}

export interface IElection extends IElectionWithOrg {
  jurisdictions: IJurisdictionBase[]
  rounds: IRound[]
}

export interface IJurisdictionBase {
  id: string
  name: string
}

export interface IJurisdiction extends IJurisdictionBase {
  organization: IOrganizationBase
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

export const useActiveElections = () =>
  useQuery<IElectionWithOrg[], Error>(['elections', 'active'], () =>
    fetchApi('/api/support/elections/active')
  )

export const useOrganizations = () =>
  useQuery<IOrganizationBase[], Error>(['organizations'], () =>
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
    onSuccess: () => queryClient.invalidateQueries(['organizations']),
  })
}

export const useOrganization = (organizationId: string) =>
  useQuery<IOrganization, Error>(['organizations', organizationId], () =>
    fetchApi(`/api/support/organizations/${organizationId}`)
  )

export const useUpdateOrganization = (organizationId: string) => {
  const updateOrganization = (body: {
    name: string
    defaultState: string | null
  }) =>
    fetchApi(`/api/support/organizations/${organizationId}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
      headers: { 'Content-Type': 'application/json' },
    })

  const queryClient = useQueryClient()

  return useMutation(updateOrganization, {
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
      queryClient.resetQueries(['organizations'], { exact: true })
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

export const useDeleteElection = () => {
  const deleteElection = async ({
    electionId,
  }: {
    electionId: string
    organizationId: string
  }) =>
    fetchApi(`/api/support/elections/${electionId}`, {
      method: 'DELETE',
    })

  const queryClient = useQueryClient()

  return useMutation(deleteElection, {
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries(['organizations', variables.organizationId])
      queryClient.invalidateQueries(['elections', 'active'])
    },
  })
}

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

export const useUndoRoundStart = (electionId: string) => {
  const undoRoundStart = async ({ roundId }: { roundId: string }) =>
    fetchApi(`/api/support/rounds/${roundId}`, {
      method: 'DELETE',
    })

  const queryClient = useQueryClient()

  return useMutation(undoRoundStart, {
    onSuccess: () => {
      queryClient.invalidateQueries(['elections', electionId])
    },
  })
}

export const useReopenCurrentRound = () => {
  const reopenCurrentRound = async ({ electionId }: { electionId: string }) =>
    fetchApi(`/api/support/elections/${electionId}/reopen-current-round`, {
      method: 'PATCH',
    })

  const queryClient = useQueryClient()

  return useMutation(reopenCurrentRound, {
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries(['elections', variables.electionId])
    },
  })
}
