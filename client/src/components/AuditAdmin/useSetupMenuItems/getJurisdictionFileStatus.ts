import { api } from '../../utilities'

export enum FileProcessingStatus {
  Blank = 'NULL', // only returned from getJurisdictionFileStatus, represents the null state from the server
  ReadyToProcess = 'READY_TO_PROCESS', // only received from the server, never returned from getJurisdictionFileStatus; equivalent to 'Processing'
  Processing = 'PROCESSING',
  Processed = 'PROCESSED',
  Errored = 'ERRORED',
}

export interface IJurisdictionsFileResponse {
  file: {
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
): Promise<{ status: FileProcessingStatus } | null> => {
  const fileStatus = await api<IJurisdictionsFileResponse>(
    `/election/${electionId}/jurisdiction/file`
  )
  if (!fileStatus) return { status: FileProcessingStatus.Errored }
  return fileStatus.processing
}

export default getJurisdictionFileStatus
