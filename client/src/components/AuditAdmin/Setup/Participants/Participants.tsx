import React from 'react'
import { useParams } from 'react-router-dom'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import FormWrapper from '../../../Atoms/Form/FormWrapper'
import { IAuditSettings } from '../../../useAuditSettings'
import {
  useJurisdictionsFile,
  useStandardizedContestsFile,
  isFileProcessed,
} from '../../../useCSV'
import CSVFile from '../../../Atoms/CSVForm'

interface IProps {
  goToNextStage: () => void
  auditType: IAuditSettings['auditType']
}

const Participants: React.FC<IProps> = ({
  goToNextStage,
  auditType,
}: IProps) => {
  const { electionId } = useParams<{ electionId: string }>()
  const [jurisdictionsFile, uploadJurisdictionsFile] = useJurisdictionsFile(
    electionId
  )
  const [
    standardizedContestsFile,
    uploadStandardizedContestsFile,
  ] = useStandardizedContestsFile(electionId, auditType, jurisdictionsFile)

  const isBallotComparison = auditType === 'BALLOT_COMPARISON'
  const isHybrid = auditType === 'HYBRID'

  if (
    !jurisdictionsFile ||
    ((isBallotComparison || isHybrid) && !standardizedContestsFile)
  )
    return null // Still loading

  const areFileUploadsComplete =
    isFileProcessed(jurisdictionsFile) &&
    (!(isBallotComparison || isHybrid) ||
      isFileProcessed(standardizedContestsFile!))

  return (
    <FormWrapper
      title={
        isBallotComparison || isHybrid
          ? 'Participants & Contests'
          : 'Participants'
      }
    >
      <CSVFile
        csvFile={jurisdictionsFile}
        uploadCSVFiles={uploadJurisdictionsFile}
        title={
          isBallotComparison || isHybrid
            ? 'Participating Jurisdictions'
            : undefined
        }
        description='Click "Browse" to choose the appropriate file from your computer. This file should be a comma-separated list of all the jurisdictions participating in the audit, plus email addresses for audit administrators in each participating jurisdiction.'
        sampleFileLink="/sample_jurisdiction_filesheet.csv"
        enabled
      />
      {(isBallotComparison || isHybrid) && (
        <div style={{ marginTop: '30px' }}>
          <CSVFile
            csvFile={standardizedContestsFile!}
            uploadCSVFiles={uploadStandardizedContestsFile}
            title="Standardized Contests"
            description='Click "Browse" to choose the appropriate file from your computer. This file should be a comma-separated list of all the contests on the ballot, the vote choices available in each, and the jurisdiction(s) where each contest appeared on the ballot.'
            sampleFileLink="/sample_standardized_contests.csv"
            enabled={isFileProcessed(jurisdictionsFile)}
          />
        </div>
      )}
      <FormButtonBar>
        <FormButton
          type="submit"
          intent="primary"
          disabled={!areFileUploadsComplete}
          onClick={goToNextStage}
        >
          Next
        </FormButton>
      </FormButtonBar>
    </FormWrapper>
  )
}

export default Participants
