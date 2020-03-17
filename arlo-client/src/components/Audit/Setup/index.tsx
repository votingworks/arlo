/* eslint-disable react/prop-types */
import React from 'react'
import { ElementType, IAudit } from '../../../types'
import Participants from './Participants'
import Contests from './Contests'
import Settings from './Settings'
import Review from './Review'

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
  setStage: (stage: ElementType<typeof setupStages>) => void
}

const Setup: React.FC<IProps> = ({ stage, setStage, audit }) => {
  const currentIndex = setupStages.indexOf(stage)
  const nextStage = () => {
    /* istanbul ignore else */
    if (currentIndex < setupStages.length - 1)
      setStage(setupStages[currentIndex + 1])
  }
  const prevStage = () => {
    // modal warn that form data may be lost
    /* istanbul ignore else */
    if (currentIndex > 0) setStage(setupStages[currentIndex - 1])
  }

  switch (stage) {
    case 'Participants':
      return <Participants audit={audit} nextStage={nextStage} />
    case 'Target Contests':
      return (
        <Contests
          isTargeted
          key="targeted"
          audit={audit}
          nextStage={nextStage}
          prevStage={prevStage}
        />
      )
    case 'Opportunistic Contests':
      return (
        <Contests
          isTargeted={false}
          key="opportunistic"
          audit={audit}
          nextStage={nextStage}
          prevStage={prevStage}
        />
      )
    case 'Audit Settings':
      return (
        <Settings audit={audit} nextStage={nextStage} prevStage={prevStage} />
      )
    case 'Review & Launch':
      return (
        <Review audit={audit} nextStage={nextStage} prevStage={prevStage} />
      )
    /* istanbul ignore next */
    default:
      return null
  }
}

export default Setup
