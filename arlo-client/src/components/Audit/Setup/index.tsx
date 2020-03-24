/* eslint-disable react/prop-types */
import React from 'react'
import { ElementType, IAudit } from '../../../types'
import Participants from './Participants'
import Contests from './Contests'
import Settings from './Settings'
import Review from './Review'
import { ISidebarMenuItem } from '../../Atoms/Sidebar'

export const setupStages = [
  'Participants',
  'Target Contests',
  'Opportunistic Contests',
  'Audit Settings',
  'Review & Launch',
] as const

interface IProps {
  stage: ElementType<typeof setupStages>
  audit: IAudit
  prevStage: ISidebarMenuItem | undefined
  nextStage: ISidebarMenuItem | undefined
}

const Setup: React.FC<IProps> = ({ stage, prevStage, audit, nextStage }) => {
  switch (stage) {
    case 'Participants':
      // prevStage === undefined, so don't send it
      return <Participants audit={audit} nextStage={nextStage!} />
    case 'Target Contests':
      return (
        <Contests
          isTargeted
          key="targeted"
          audit={audit}
          nextStage={nextStage!}
          prevStage={prevStage!}
        />
      )
    case 'Opportunistic Contests':
      return (
        <Contests
          isTargeted={false}
          key="opportunistic"
          audit={audit}
          nextStage={nextStage!}
          prevStage={prevStage!}
        />
      )
    case 'Audit Settings':
      return (
        <Settings audit={audit} nextStage={nextStage!} prevStage={prevStage!} />
      )
    case 'Review & Launch':
      // nextStage === undefined, so don't send it
      return <Review audit={audit} prevStage={prevStage!} />
    /* istanbul ignore next */
    default:
      return null
  }
}

export default Setup
