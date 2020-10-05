import { useState, useMemo, useCallback } from 'react'
import { toast } from 'react-toastify'
import uuidv4 from 'uuidv4'
import { setupStages } from '../AASetup'
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
  electionId: string
): [ISidebarMenuItem[], () => void, string] {
  const [refreshId, setRefreshId] = useState(uuidv4())
  const [participants, setParticipants] = useState<ISidebarMenuItem['state']>(
    'live'
  )
  const [targetContests, setTargetContests] = useState<
    ISidebarMenuItem['state']
  >('live')
  const [opportunisticContests, setOpportunisticContests] = useState<
    ISidebarMenuItem['state']
  >('live')
  const [auditSettings, setAuditSettings] = useState<ISidebarMenuItem['state']>(
    'live'
  )
  const [reviewLaunch, setReviewLaunch] = useState<ISidebarMenuItem['state']>(
    'live'
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
        setStage('Target Contests')
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
      setStage('Review & Launch')
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
            case 'Participants':
            case 'Participants & Contests':
              return participants
            case 'Target Contests':
              return targetContests
            case 'Opportunistic Contests':
              return opportunisticContests
            case 'Audit Settings':
              return auditSettings
            case 'Review & Launch':
              return reviewLaunch
            /* istanbul ignore next */
            default:
              return 'locked'
          }
        })()
        return {
          title: s,
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
              setStage('Review & Launch')
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
  return [menuItems, refresh, refreshId]
}

export default useSetupMenuItems
