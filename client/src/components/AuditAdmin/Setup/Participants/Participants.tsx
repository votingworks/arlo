import React from 'react'
import { Button } from '@blueprintjs/core'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormWrapper from '../../../Atoms/Form/FormWrapper'
import CSVFile from '../../../Atoms/CSVForm'
import {
  useJurisdictionsFile,
  useStandardizedContestsFile,
} from '../../../useFileUpload'
import { isFileProcessed } from '../../../useCSV'

export interface IParticipantsProps {
  electionId: string
  isStandardizedContestsFileEnabled: boolean
  goToNextStage: () => void
}

const Participants: React.FC<IParticipantsProps> = ({
  electionId,
  isStandardizedContestsFileEnabled,
  goToNextStage,
}: IParticipantsProps) => {
  const jurisdictionsFileUpload = useJurisdictionsFile(electionId)
  const standardizedContestsFileUpload = useStandardizedContestsFile(
    electionId,
    { enabled: isStandardizedContestsFileEnabled }
  )
  if (
    !jurisdictionsFileUpload.uploadedFile.isSuccess ||
    (isStandardizedContestsFileEnabled &&
      !standardizedContestsFileUpload.uploadedFile.isSuccess)
  )
    return null

  const areFileUploadsComplete =
    isFileProcessed(jurisdictionsFileUpload.uploadedFile.data) &&
    (!isStandardizedContestsFileEnabled ||
      isFileProcessed(standardizedContestsFileUpload.uploadedFile.data!))

  return (
    <FormWrapper
      title={
        isStandardizedContestsFileEnabled
          ? 'Participants & Contests'
          : 'Participants'
      }
    >
      <CSVFile
        csvFile={jurisdictionsFileUpload.uploadedFile.data}
        uploadCSVFile={async file => {
          await jurisdictionsFileUpload.uploadFiles([file])
          return true
        }}
        title={
          isStandardizedContestsFileEnabled
            ? 'Participating Jurisdictions'
            : undefined
        }
        description='Click "Browse" to choose the appropriate file from your computer. This file should be a comma-separated list of all the jurisdictions participating in the audit, plus email addresses for audit administrators in each participating jurisdiction.'
        sampleFileLink="/sample_jurisdiction_filesheet.csv"
        enabled
      />
      {isStandardizedContestsFileEnabled && (
        <div style={{ marginTop: '30px' }}>
          <CSVFile
            csvFile={standardizedContestsFileUpload.uploadedFile.data!}
            uploadCSVFile={async file => {
              await standardizedContestsFileUpload.uploadFiles([file])
              return true
            }}
            title="Standardized Contests"
            description='Click "Browse" to choose the appropriate file from your computer. This file should be a comma-separated list of all the contests on the ballot, the jurisdiction(s) where each contest appeared on the ballot, and optionally the vote choices available in each.'
            sampleFileLink="/sample_standardized_contests.csv"
            enabled={isFileProcessed(jurisdictionsFileUpload.uploadedFile.data)}
          />
        </div>
      )}
      <FormButtonBar style={{ marginTop: '20px' }}>
        <Button
          intent="primary"
          rightIcon="arrow-right"
          disabled={!areFileUploadsComplete}
          onClick={goToNextStage}
        >
          Next
        </Button>
      </FormButtonBar>
    </FormWrapper>
  )
}

export default Participants
