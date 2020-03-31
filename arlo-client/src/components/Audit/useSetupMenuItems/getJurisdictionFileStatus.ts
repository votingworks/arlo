import { api, checkAndToast } from '../../utilities'
import { IErrorResponse } from '../../../types'

type IJurisdictionsFileResponse =
  | { file: null; processing: null }
  | {
      file: {
        contents: null | string
        name: string
        uploadedAt: string
      }
      processing:
        | {
            status: 'READY_TO_PROCESS'
            startedAt: null
            completedAt: null
            error: null
          }
        | {
            status: 'PROCESSING'
            startedAt: string
            completedAt: null
            error: null
          }
        | {
            status: 'PROCESSED'
            startedAt: string
            completedAt: string
            error: null
          }
        | {
            status: 'ERRORED'
            startedAt: string
            completedAt: string
            error: string
          }
    }

const getJurisdictionFileStatus = async (
  electionId: string
): Promise<
  | 'ERRORED'
  | 'PROCESSING'
  | 'PROCESSED'
  | 'ERRORED'
  | 'READY_TO_PROCESS'
  | 'NULL'
> => {
  const jurisdictionsOrError:
    | IJurisdictionsFileResponse
    | IErrorResponse = await api(`/election/${electionId}/jurisdiction/file`)
  if (checkAndToast(jurisdictionsOrError)) {
    return 'ERRORED'
  }
  if (jurisdictionsOrError.processing) {
    return jurisdictionsOrError.processing!.status
  }
  return 'NULL'
}

export default getJurisdictionFileStatus
