import { useState, useMemo, useCallback } from 'react'
import { toast } from 'react-toastify'
import uuidv4 from 'uuidv4'
import { setupStages, stageTitles } from '../AASetup'
import { ElementType } from '../../../types'
import { ISidebarMenuItem } from '../../Atoms/Sidebar'
import getJurisdictionFileStatus, {
  FileProcessingStatus,
} from './getJurisdictionFileStatus'
import { poll } from '../../utilities'
import getRoundStatus from './getRoundStatus'

function useSetupMenuItems(
  stage: ElementType<typeof setupStages>,
  setStage: (s: ElementType<typeof setupStages>) => void,
  electionId: string,
  isBallotComparison: boolean,
  setRefreshId: (arg0: string) => void
): [ISidebarMenuItem[], () => void] {
  const [participants, setParticipants] = useState<ISidebarMenuItem['state']>(
    'live'
  )
  const [targetContests, setTargetContests] = useState<
    ISidebarMenuItem['state']
  >('locked')
  const [opportunisticContests, setOpportunisticContests] = useState<
    ISidebarMenuItem['state']
  >('locked')
  const [auditSettings, setAuditSettings] = useState<ISidebarMenuItem['state']>(
    'locked'
  )
  const [reviewLaunch, setReviewLaunch] = useState<ISidebarMenuItem['state']>(
    'locked'
  )
  const setContests = useCallback(
    (s: ISidebarMenuItem['state']) => {
      setTargetContests(s)
      setOpportunisticContests(s)
    },
    [setTargetContests, setOpportunisticContests]
  )

  const setOrPollParticipantsFile = useCallback(async () => {
    // issue with ballot polling now?
    const processing = await getJurisdictionFileStatus(electionId)
    const jurisdictionStatus = processing
      ? processing.status
      : FileProcessingStatus.Blank
    if (
      jurisdictionStatus === FileProcessingStatus.Errored ||
      jurisdictionStatus === FileProcessingStatus.Blank
    ) {
      setContests('locked')
    } else if (jurisdictionStatus === FileProcessingStatus.Processed) {
      setContests('live')
    } else {
      setContests('processing')
      const condition = async () => {
        const fileProcessing = await getJurisdictionFileStatus(electionId)
        const { status } = fileProcessing!
        if (status === FileProcessingStatus.Processed) return true
        if (status === FileProcessingStatus.Errored)
          throw new Error('File processing error') // TODO test coverage isn't reaching this line
        return false
      }
      const complete = () => {
        setContests('live')
        setStage('target-contests')
        setRefreshId(uuidv4())
      }
      poll(condition, complete, (err: Error) => {
        toast.error(err.message)
        // eslint-disable-next-line no-console
        console.error(err.message)
      })
    }
  }, [electionId, setContests, setStage])

  const lockAllIfRounds = useCallback(async () => {
    const roundsExist = await getRoundStatus(electionId)
    if (roundsExist) {
      setStage('review')
      setParticipants('locked')
      setContests('locked')
      setAuditSettings('locked')
      setReviewLaunch('locked')
    }
  }, [
    setParticipants,
    setContests,
    setAuditSettings,
    setReviewLaunch,
    electionId,
    setStage,
  ])

  const refresh = useCallback(() => {
    setParticipants('live')
    setOrPollParticipantsFile()
    setAuditSettings('live')
    setReviewLaunch('live')
    lockAllIfRounds()
    setRefreshId(uuidv4())
  }, [
    setParticipants,
    setOrPollParticipantsFile,
    setAuditSettings,
    setReviewLaunch,
    lockAllIfRounds,
    setRefreshId,
  ])

  const menuItems: ISidebarMenuItem[] = useMemo(
    () =>
      setupStages.map((s: ElementType<typeof setupStages>) => {
        const state = (() => {
          switch (s) {
            case 'participants':
              return participants
            case 'target-contests':
              return targetContests
            case 'opportunistic-contests':
              return opportunisticContests
            case 'settings':
              return auditSettings
            case 'review':
              return reviewLaunch
            /* istanbul ignore next */
            default:
              return 'locked'
          }
        })()
        return {
          id: s,
          title:
            isBallotComparison && s === 'participants'
              ? 'Participants & Contests'
              : stageTitles[s],
          active: s === stage,
          activate: (_, force = false) => {
            refresh()
            /* istanbul ignore else */
            if (state === 'live') {
              /* istanbul ignore next */
              if (!force) {
                // launch confirm dialog here
              }
              setStage(s)
            } else if (reviewLaunch === 'locked') {
              setStage('review')
            }
          },
          state,
        }
      }),
    [
      stage,
      setStage,
      participants,
      targetContests,
      opportunisticContests,
      auditSettings,
      reviewLaunch,
      refresh,
    ]
  )
  return [menuItems, refresh]
}

export default useSetupMenuItems
