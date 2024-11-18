import { useQuery, UseQueryResult } from 'react-query'
import { fetchApi, ApiError } from '../utils/api'
import { IAuditAdmin, IOrganization } from './UserContext'

function useAuditAdminsOrganizations(
  user: IAuditAdmin | null
): UseQueryResult<IOrganization[], ApiError> {
  return useQuery<IOrganization[], ApiError>(
    'orgs',
    () => fetchApi(`/api/audit_admins/${user!.id}/organizations`),
    { enabled: !!user }
  )
}

export default useAuditAdminsOrganizations
