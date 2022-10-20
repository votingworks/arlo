import { useQuery, UseQueryResult } from 'react-query'
import { IContest } from '../../types'
import { fetchApi, ApiError } from '../../utils/api'

const useContestsJurisdictionAdmin = (
  electionId: string,
  jurisdictionId: string
): UseQueryResult<IContest[], ApiError> =>
  useQuery(['jurisdictions', jurisdictionId, 'contests'], async () => {
    return (
      await fetchApi(
        `/api/election/${electionId}/jurisdiction/${jurisdictionId}/contest`
      )
    ).contests
  })

export default useContestsJurisdictionAdmin
