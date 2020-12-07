import React, { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'
import useAuditSettings from '../../useAuditSettings'
import {
  useJurisdictionsFile,
  useStandardizedContestsFile,
  isFileProcessed,
} from '../../useCSV'
import CSVFile from '../../CSVForm'
import FormWrapper from '../../../Atoms/Form/FormWrapper'

interface IProps {
  nextStage: ISidebarMenuItem
  locked: boolean
  refresh: () => void
}

const Participants: React.FC<IProps> = ({ nextStage, refresh }: IProps) => {
  const { electionId } = useParams<{ electionId: string }>()
  const [auditSettings] = useAuditSettings(electionId)
  const [jurisdictionsFile, uploadJurisdictionsFile] = useJurisdictionsFile(
    electionId
  )
  const [
    standardizedContestsFile,
    uploadStandardizedContestsFile,
  ] = useStandardizedContestsFile(electionId, auditSettings)

  // Once the file uploads are complete, we need to notify the setupMenuItems to
  // refresh and unlock the next stage.
  useEffect(() => {
    if (
      jurisdictionsFile &&
      auditSettings &&
      standardizedContestsFile &&
      isFileProcessed(jurisdictionsFile) &&
      (auditSettings.auditType !== 'BALLOT_COMPARISON' ||
        isFileProcessed(standardizedContestsFile)) &&
      nextStage.state === 'locked'
    )
      refresh()
  })

  if (!auditSettings || !jurisdictionsFile || !standardizedContestsFile)
    return null // Still loading

  const isBallotComparison = auditSettings.auditType === 'BALLOT_COMPARISON'

  return (
    <FormWrapper
      title={isBallotComparison ? 'Participants & Contests' : 'Participants'}
    >
      <CSVFile
        csvFile={jurisdictionsFile}
        uploadCSVFile={uploadJurisdictionsFile}
        title={isBallotComparison ? 'Participating Jurisdictions' : undefined}
        description='Click "Browse" to choose the appropriate file from your computer. This file should be a comma-separated list of all the jurisdictions participating in the audit, plus email addresses for audit administrators in each participating jurisdiction.'
        sampleFileLink="/sample_jurisdiction_filesheet.csv"
        enabled
      />
      {isBallotComparison && (
        <CSVFile
          csvFile={standardizedContestsFile}
          uploadCSVFile={uploadStandardizedContestsFile}
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
