import React from 'react'
import ContestForm from './ContestForm'
import ContestSelect from './ContestSelect'
import { IAuditSettings } from '../../../useAuditSettings'

export interface IContestsProps {
  electionId: string
  auditType: IAuditSettings['auditType']
  auditMathType: IAuditSettings['auditMathType']
  electionState: IAuditSettings['state']
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
