/* eslint-disable react/prop-types */
import React, { useState } from 'react'
import Participants from './Participants/Participants'
import Contests from './Contests/Contests'
import Settings from './Settings/Settings'
import Review from './Review/Review'
import { ElementType } from '../../../types'
import Sidebar from '../../Atoms/Sidebar'
import { ISampleSizes } from '../useRoundsAuditAdmin'
import { IAuditSettings } from '../../useAuditSettings'
import { Inner } from '../../Atoms/Wrapper'
import { isFileProcessed } from '../../useCSV'
import {
  useJurisdictionsFile,
  useStandardizedContestsFile,
} from '../../useFileUpload'

export const setupStages = [
  'participants',
  'target-contests',
  'opportunistic-contests',
  'settings',
  'review',
] as const

type Stage = ElementType<typeof setupStages>

const stageTitles: { [stage in Stage]: string } = {
  participants: 'Participants',
  'target-contests': 'Target Contests',
  'opportunistic-contests': 'Opportunistic Contests',
  settings: 'Audit Settings',
  review: 'Review & Launch',
}

export interface ISetupProps {
  electionId: string
  auditSettings: IAuditSettings
  startNextRound: (sampleSizes: ISampleSizes) => Promise<boolean>
  isAuditStarted: boolean
}

const Setup: React.FC<ISetupProps> = ({
  electionId,
  auditSettings,
  startNextRound,
  isAuditStarted,
}) => {
  const { auditType } = auditSettings
  const [currentStage, setCurrentStage] = useState<Stage>(
    isAuditStarted ? 'review' : 'participants'
  )

  const jurisdictionsFileUpload = useJurisdictionsFile(electionId)
  const isStandardizedContestsFileEnabled =
    auditType === 'BALLOT_COMPARISON' || auditType === 'HYBRID'
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

  const stages: readonly Stage[] =
    auditSettings.auditType === 'BATCH_COMPARISON'
      ? setupStages.filter(stage => stage !== 'opportunistic-contests')
      : setupStages

  const goToNextStage = () => {
    setCurrentStage(stages[stages.indexOf(currentStage) + 1])
  }

  const goToPrevStage = () => {
    setCurrentStage(stages[stages.indexOf(currentStage) - 1])
  }

  return (
    <Inner>
      <Sidebar
        title="Audit Setup"
        menuItems={stages.map(stage => ({
          id: stage,
          text: stageTitles[stage],
          active: currentStage === stage,
          disabled:
            (isAuditStarted && stage !== 'review') ||
            // If still working on file uploads, disable the rest of the stages
            (stage !== 'participants' && !areFileUploadsComplete),
          onClick: () => setCurrentStage(stage),
        }))}
      />
      <section>
        {(() => {
          switch (currentStage) {
            case 'participants':
              return (
                <Participants
                  electionId={electionId}
                  isStandardizedContestsFileEnabled={
                    isStandardizedContestsFileEnabled
                  }
                  goToNextStage={goToNextStage}
                />
              )
            case 'target-contests':
              return (
                <Contests
                  key="targeted"
                  electionId={electionId}
                  isTargeted
                  auditType={auditType}
                  goToPrevStage={goToPrevStage}
                  goToNextStage={goToNextStage}
                />
              )
            case 'opportunistic-contests':
              return (
                <Contests
                  key="opportunistic"
                  electionId={electionId}
                  isTargeted={false}
                  auditType={auditType}
                  goToPrevStage={goToPrevStage}
                  goToNextStage={goToNextStage}
                />
              )
            case 'settings':
              return (
                <Settings
                  electionId={electionId}
                  goToPrevStage={goToPrevStage}
                  goToNextStage={goToNextStage}
                />
              )
            case 'review':
              return (
                <Review
                  electionId={electionId}
                  goToPrevStage={goToPrevStage}
                  startNextRound={startNextRound}
                  locked={isAuditStarted}
                />
              )
            /* istanbul ignore next */
            default:
              return null
          }
        })()}
      </section>
    </Inner>
  )
}

export default Setup
