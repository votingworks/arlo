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
  auditType: 'BALLOT_POLLING' | 'BALLOT_COMPARISON' | 'BATCH_COMPARISON'
}

export interface IAuditAdmin {
  email: string
}

export interface IElection extends IElectionBase {
  jurisdictions: IJurisdiction[]
}

export interface IJurisdiction {
  id: string
  name: string
  jurisdictionAdmins: IJurisdictionAdmin[]
}

export interface IJurisdictionAdmin {
  email: string
}

export const useOrganizations = () =>
  useQuery<IOrganizationBase[], Error>('organizations', () =>
    fetchApi('/api/support/organizations')
  )

export const useOrganization = (organizationId: string) =>
  useQuery<IOrganization, Error>(['organization', organizationId], () =>
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
    onSuccess: () => queryClient.invalidateQueries('organization'),
  })
}

export const useElection = (electionId: string) =>
  useQuery<IElection, Error>(['election', electionId], () =>
    fetchApi(`/api/support/elections/${electionId}`)
  )
