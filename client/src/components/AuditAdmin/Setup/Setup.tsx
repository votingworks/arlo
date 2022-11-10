/* eslint-disable react/prop-types */
import React from 'react'
import Participants from './Participants/Participants'
import Contests from './Contests/Contests'
import Settings from './Settings/Settings'
import Review from './Review/Review'
import { ElementType, IContest } from '../../../types'
import { ISidebarMenuItem } from '../../Atoms/Sidebar'
import { ISampleSizes } from '../useRoundsAuditAdmin'
import { IAuditSettings } from '../../useAuditSettings'

export const setupStages = [
  'participants',
  'target-contests',
  'opportunistic-contests',
  'settings',
  'review',
] as const

export const stageTitles: { [keys in typeof setupStages[number]]: string } = {
  participants: 'Participants',
  'target-contests': 'Target Contests',
  'opportunistic-contests': 'Opportunistic Contests',
  settings: 'Audit Settings',
  review: 'Review & Launch',
}

interface IProps {
  stage: ElementType<typeof setupStages>
  menuItems: ISidebarMenuItem[]
  refresh: () => void
  auditSettings: IAuditSettings
  startNextRound: (sampleSizes: ISampleSizes) => Promise<boolean>
  contests: IContest[]
}

const Setup: React.FC<IProps> = ({
  stage,
  menuItems,
  refresh,
  auditSettings,
  startNextRound,
  contests,
}) => {
  const activeStage = menuItems.find(m => m.id === stage)
  const nextStage: ISidebarMenuItem | undefined =
    menuItems[menuItems.indexOf(activeStage!) + 1]
  const prevStage: ISidebarMenuItem | undefined =
    menuItems[menuItems.indexOf(activeStage!) - 1]
  const { auditType } = auditSettings
  switch (stage) {
    case 'participants':
      // prevStage === undefined, so don't send it
      return (
        <Participants
          nextStage={nextStage!}
          refresh={refresh}
          auditType={auditType}
        />
      )
    case 'target-contests':
      return (
        <Contests
          isTargeted
          key="targeted"
          nextStage={nextStage!}
          prevStage={prevStage!}
          locked={activeStage!.state === 'locked'}
          auditType={auditType}
        />
      )
    case 'opportunistic-contests':
      return (
        <Contests
          isTargeted={false}
          key="opportunistic"
          nextStage={nextStage!}
          prevStage={prevStage!}
          locked={activeStage!.state === 'locked'}
          auditType={auditType}
        />
      )
    case 'settings':
      return (
        <Settings
          nextStage={nextStage!}
          prevStage={prevStage!}
          locked={activeStage!.state === 'locked'}
          auditSettings={auditSettings}
        />
      )
    case 'review':
      // nextStage === undefined, so don't send it
      return (
        <Review
          prevStage={prevStage!}
          locked={activeStage!.state === 'locked'}
          refresh={refresh}
          startNextRound={startNextRound}
          auditSettings={auditSettings}
          contests={contests}
        />
      )
    /* istanbul ignore next */
    default:
      return null
  }
}

export default Setup
