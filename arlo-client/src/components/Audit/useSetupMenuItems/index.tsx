import { useState, useMemo, useCallback } from 'react'
import { toast } from 'react-toastify'
import { setupStages } from '../Setup'
import { ElementType } from '../../../types'
import { ISidebarMenuItem } from '../../Atoms/Sidebar'
import getJurisdictionFileStatus from './getJurisdictionFileStatus'
import { poll } from '../../utilities'

function useSetupMenuItems(
  stage: ElementType<typeof setupStages>,
  setStage: (s: ElementType<typeof setupStages>) => void,
  electionId: string
): [ISidebarMenuItem[], () => void] {
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
    const jurisdictionStatus = await getJurisdictionFileStatus(electionId)
    if (jurisdictionStatus === 'ERRORED' || jurisdictionStatus === 'NULL') {
      setContests('locked')
    } else if (jurisdictionStatus === 'PROCESSED') {
      setContests('live')
    } else {
      setContests('processing')
      const condition = async () => {
        const newJurisdictionStatus = await getJurisdictionFileStatus(
          electionId
        )
        if (newJurisdictionStatus === 'PROCESSED') return true
        return false
      }
      const complete = () => setContests('live')
      poll(condition, complete, (err: Error) => toast.error(err.message))
    }
  }, [electionId, setContests])

  const refresh = useCallback(() => {
    setParticipants('live')
    setOrPollParticipantsFile()
    setAuditSettings('live')
    setReviewLaunch('live')
  }, [
    setParticipants,
    setOrPollParticipantsFile,
    setAuditSettings,
    setReviewLaunch,
  ])

  const menuItems: ISidebarMenuItem[] = useMemo(
    () =>
      setupStages.map((s: ElementType<typeof setupStages>) => {
        const state = (() => {
          switch (s) {
            case 'Participants':
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
