/* eslint-disable react/prop-types */
import React from 'react'
import { ElementType, IAuditSettings } from '../../../types'
import Participants from './Participants'
import Contests from './Contests'
import Settings from './Settings'
import Review from './Review'
import { ISidebarMenuItem } from '../../Atoms/Sidebar'

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
  auditType: IAuditSettings['auditType']
}

const AASetup: React.FC<IProps> = ({
  stage,
  menuItems,
  refresh,
  auditType,
}) => {
  const activeStage = menuItems.find(m => m.id === stage)
  const nextStage: ISidebarMenuItem | undefined =
    menuItems[menuItems.indexOf(activeStage!) + 1]
  const prevStage: ISidebarMenuItem | undefined =
    menuItems[menuItems.indexOf(activeStage!) - 1]
  switch (stage) {
    case 'participants':
      // prevStage === undefined, so don't send it
      return (
        <Participants
          nextStage={nextStage!}
          locked={activeStage!.state === 'locked'}
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
        />
      )
    case 'review':
      // nextStage === undefined, so don't send it
      return (
        <Review
          prevStage={prevStage!}
          locked={activeStage!.state === 'locked'}
          refresh={refresh}
        />
      )
    /* istanbul ignore next */
    default:
      return null
  }
}

export default AASetup
