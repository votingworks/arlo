import { api, checkAndToast } from '../../utilities'
import { IErrorResponse } from '../../../types'

export enum FileProcessingStatus {
  ReadyToProcess = 'READY_TO_PROCESS',
  Processing = 'PROCESSING',
  Processed = 'PROCESSED',
  Errored = 'ERRORED',
}

export interface IJurisdictionsFileResponse {
  file: {
    contents: null | string
    name: string
    uploadedAt: string
  } | null
  processing: {
    status: FileProcessingStatus
    startedAt: string | null
    completedAt: string | null
    error: string | null
  } | null
}

const getJurisdictionFileStatus = async (
  electionId: string
): Promise<FileProcessingStatus> => {
  const jurisdictionsOrError:
    | IJurisdictionsFileResponse
    | IErrorResponse = await api(`/election/${electionId}/jurisdiction/file`)
  if (checkAndToast(jurisdictionsOrError)) {
    return FileProcessingStatus.Errored
  }
  if (jurisdictionsOrError.processing) {
    return jurisdictionsOrError.processing!.status
  }
  return FileProcessingStatus.ReadyToProcess
}

export default getJurisdictionFileStatus
