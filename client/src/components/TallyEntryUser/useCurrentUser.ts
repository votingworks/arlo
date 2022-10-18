import { useQuery, UseQueryOptions, UseQueryResult } from 'react-query'
import { IUser, IAuthData } from '../UserContext'
import { fetchApi } from '../../utils/api'

const useCurrentUser = (
  options: UseQueryOptions<IAuthData, unknown, IUser | null> = {}
): UseQueryResult<IUser | null> => {
  return useQuery<IAuthData, unknown, IUser | null>(
    ['user'],
    () => fetchApi('/api/me'),
    {
      ...options,
      select: data => data.user,
    }
  )
}

export default useCurrentUser
