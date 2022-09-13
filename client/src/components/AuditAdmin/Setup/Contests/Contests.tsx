/* eslint-disable jsx-a11y/label-has-associated-control */
import React from 'react'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'
import ContestForm from './ContestForm'
import ContestSelect from './ContestSelect'
import { IAuditSettings } from '../../../useAuditSettings'

interface IProps {
  isTargeted: boolean
  nextStage: ISidebarMenuItem
  prevStage: ISidebarMenuItem
  locked: boolean
  auditType: IAuditSettings['auditType']
}

const Contests: React.FC<IProps> = (props: IProps): React.ReactElement => {
  return props.auditType === 'BALLOT_COMPARISON' ? (
    <ContestSelect {...props} />
  ) : (
    <ContestForm {...props} />
  )
}

export default Contests
