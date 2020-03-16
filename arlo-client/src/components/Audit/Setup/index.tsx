/* eslint-disable react/prop-types */
import React from 'react'
import { ElementType, IAudit } from '../../../types'
import FormButton from '../../Form/FormButton'
import Participants from './Participants'

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
  const nextStageButton = () => {
    if (currentIndex < setupStages.length - 1) {
      return (
        <FormButton onClick={() => setStage(setupStages[currentIndex + 1])}>
          Next
        </FormButton>
      )
    }
    return null
  }
  const prevStageButton = () => {
    if (currentIndex > 0) {
      return (
        <FormButton onClick={() => setStage(setupStages[currentIndex - 1])}>
          Previous
        </FormButton>
      )
    }
    return null
  }

  const step = (() => {
    switch (stage) {
      case 'Participants':
        return <Participants audit={audit} />
      case 'Target Contests':
        return <p>Target Contests</p>
      case 'Opportunistic Contests':
        return <p>Opportunistic Contests</p>
      case 'Audit Settings':
        return <p>Audit Settings</p>
      case 'Review & Launch':
        return <p>Review &amp; Launch</p>
      default:
        return null
    }
  })()

  return (
    <form>
      {step}
      {prevStageButton()}
      {nextStageButton()}
    </form>
  )
}

export default Setup
