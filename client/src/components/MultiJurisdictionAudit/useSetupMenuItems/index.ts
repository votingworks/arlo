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
import getContestFileStatus from './getContestFileStatus'

function useSetupMenuItems(
  stage: ElementType<typeof setupStages>,
  setStage: (s: ElementType<typeof setupStages>) => void,
  electionId: string,
  isBallotComparison: boolean,
  isHybrid: boolean,
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

  const setOrPollFiles = useCallback(async () => {
    const jurisdictionProcessing = await getJurisdictionFileStatus(electionId)
    const jurisdictionStatus = jurisdictionProcessing
      ? jurisdictionProcessing.status
      : FileProcessingStatus.Blank
    let contestFileStatus: FileProcessingStatus = FileProcessingStatus.Processed // pretend it's processed by default
    if (isBallotComparison || isHybrid) {
      const contestFileProcessing = await getContestFileStatus(electionId)
      contestFileStatus = contestFileProcessing
        ? contestFileProcessing.status
        : FileProcessingStatus.Blank
    }
    if (
      jurisdictionStatus === FileProcessingStatus.Errored ||
      jurisdictionStatus === FileProcessingStatus.Blank ||
      contestFileStatus === FileProcessingStatus.Errored ||
      contestFileStatus === FileProcessingStatus.Blank
    ) {
      setContests('locked')
    } else if (
      jurisdictionStatus === FileProcessingStatus.Processed &&
      contestFileStatus === FileProcessingStatus.Processed
    ) {
      setContests('live')
    } else {
      setContests('processing')
      const condition = async () => {
        const jProcessing = await getJurisdictionFileStatus(electionId)
        const { status: jStatus } = jProcessing!
        let cStatus = FileProcessingStatus.Processed
        if (isBallotComparison || isHybrid) {
          const cProcessing = await getContestFileStatus(electionId)
          cStatus = cProcessing!.status
        }
        if (
          jStatus === FileProcessingStatus.Processed &&
          cStatus === FileProcessingStatus.Processed
        )
          return true
        if (
          jStatus === FileProcessingStatus.Errored ||
          cStatus === FileProcessingStatus.Errored
        )
          throw new Error('File processing error') // TODO test coverage isn't reaching this line
        return false
      }
      const complete = () => {
        setContests('live')
        setStage('target-contests')
        setRefreshId(uuidv4())
      }
      poll(condition, complete, (err: Error) => {
        setContests('locked')
        toast.error(err.message) // we need to toast the error from the server here instead 'File processing error'
        // eslint-disable-next-line no-console
        console.error(err.message)
      })
    }
  }, [
    electionId,
    setContests,
    setStage,
    isBallotComparison,
    isHybrid,
    setRefreshId,
  ])

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
    setOrPollFiles()
    setAuditSettings('live')
    setReviewLaunch('live')
    lockAllIfRounds()
    setRefreshId(uuidv4())
  }, [
    setParticipants,
    setOrPollFiles,
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
            (isBallotComparison || isHybrid) && s === 'participants'
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
      isBallotComparison,
      isHybrid,
      reviewLaunch,
      refresh,
    ]
  )
  return [menuItems, refresh]
}

export default useSetupMenuItems
