import React, { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'
import FormWrapper from '../../../Atoms/Form/FormWrapper'
import useAuditSettings from '../../../useAuditSettings'
import {
  useJurisdictionsFile,
  useStandardizedContestsFile,
  isFileProcessed,
} from '../../../useCSV'
import CSVFile from '../../../Atoms/CSVForm'

interface IProps {
  nextStage: ISidebarMenuItem
  refresh: () => void
}

const Participants: React.FC<IProps> = ({
  nextStage,
  refresh,
}: IProps): React.ReactElement | null => {
  const { electionId } = useParams<{ electionId: string }>()
  const [auditSettings] = useAuditSettings(electionId)
  const [jurisdictionsFile, uploadJurisdictionsFile] = useJurisdictionsFile(
    electionId
  )
  const [
    standardizedContestsFile,
    uploadStandardizedContestsFile,
  ] = useStandardizedContestsFile(electionId, auditSettings, jurisdictionsFile)

  const isBallotComparison =
    auditSettings && auditSettings.auditType === 'BALLOT_COMPARISON'
  const isHybrid = auditSettings && auditSettings.auditType === 'HYBRID'

  // Once the file uploads are complete, we need to notify the setupMenuItems to
  // refresh and unlock the next stage.
  useEffect(() => {
    if (
      auditSettings &&
      jurisdictionsFile &&
      isFileProcessed(jurisdictionsFile) &&
      (!(isBallotComparison || isHybrid) ||
        (standardizedContestsFile &&
          isFileProcessed(standardizedContestsFile))) &&
      nextStage.state === 'locked'
    )
      refresh()
  })

  if (
    !auditSettings ||
    !jurisdictionsFile ||
    ((isBallotComparison || isHybrid) && !standardizedContestsFile)
  )
    return null // Still loading

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
        <CSVFile
          csvFile={standardizedContestsFile!}
          uploadCSVFiles={uploadStandardizedContestsFile}
          title="Standardized Contests"
          description='Click "Browse" to choose the appropriate file from your computer. This file should be a comma-separated list of all the contests on the ballot, the vote choices available in each, and the jurisdiction(s) where each contest appeared on the ballot.'
          sampleFileLink="/sample_standardized_contests.csv"
          enabled={isFileProcessed(jurisdictionsFile)}
        />
      )}
      <FormButtonBar>
        <FormButton
          type="submit"
          intent="primary"
          disabled={nextStage.state === 'locked'}
          onClick={() => nextStage.activate && nextStage.activate()}
        >
          Next
        </FormButton>
      </FormButtonBar>
    </FormWrapper>
  )
}

export default Participants
