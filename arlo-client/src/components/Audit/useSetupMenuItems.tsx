import { useState, useMemo } from 'react'
import { setupStages } from './Setup'
import { ElementType } from '../../types'
import { ISidebarMenuItem } from '../Atoms/Sidebar'

function useSetupMenuItems(
  stage: ElementType<typeof setupStages>,
  setStage: (s: ElementType<typeof setupStages>) => void
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

  const refresh = () => {
    setParticipants('live')
    setTargetContests('live')
    setOpportunisticContests('live')
    setAuditSettings('live')
    setReviewLaunch('live')
  }

  const menuItems: ISidebarMenuItem[] = useMemo(
    () =>
      setupStages.map((s: ElementType<typeof setupStages>) => {
        const state = (() => {
          // move these to useStates, so they can be asynchronously updated
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
            if (state === 'live') {
              if (!force) {
                // launch confirm dialog
              }
              setStage(s)
            }
          },
          state,
        }
      }),
    [stage, setupStages]
  )
  return [menuItems, refresh]
}

export default useSetupMenuItems
