/* eslint-disable jsx-a11y/label-has-associated-control */
import React from 'react'
import ContestForm from './ContestForm'
import ContestSelect from './ContestSelect'
import { IAuditSettings } from '../../../useAuditSettings'

export interface IContestsProps {
  electionId: string
  auditType: IAuditSettings['auditType']
  isTargeted: boolean
  goToNextStage: () => void
  goToPrevStage: () => void
}

const Contests: React.FC<IContestsProps> = (props: IContestsProps) => {
  return props.auditType === 'BALLOT_COMPARISON' ? (
    <ContestSelect {...props} />
  ) : (
    <ContestForm {...props} />
  )
}

export default Contests
