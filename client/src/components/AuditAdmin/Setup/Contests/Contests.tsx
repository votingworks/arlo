/* eslint-disable jsx-a11y/label-has-associated-control */
import React from 'react'
import ContestForm from './ContestForm'
import ContestSelect from './ContestSelect'
import { IAuditSettings } from '../../../useAuditSettings'

interface IProps {
  isTargeted: boolean
  goToNextStage: () => void
  goToPrevStage: () => void
  auditType: IAuditSettings['auditType']
}

const Contests: React.FC<IProps> = (props: IProps) => {
  return props.auditType === 'BALLOT_COMPARISON' ? (
    <ContestSelect {...props} />
  ) : (
    <ContestForm {...props} />
  )
}

export default Contests
