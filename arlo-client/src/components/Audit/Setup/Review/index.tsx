import React from 'react'
import { H4, Callout } from '@blueprintjs/core'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'
import H2Title from '../../../Atoms/H2Title'

interface IProps {
  locked: boolean
  prevStage: ISidebarMenuItem
}

const Review: React.FC<IProps> = ({ prevStage }: IProps) => {
  return (
    <div>
      <H2Title>Review &amp; Launch</H2Title>
      <Callout intent="warning">
        Once the audit is started, the audit definition will no longer be
        editable. Please make sure this data is correct before launching the
        audit.
      </Callout>
      <H4>Audit Settings</H4>
      <H4>Sample Size Options</H4>
      <FormButtonBar>
        <FormButton onClick={prevStage.activate}>Back</FormButton>
      </FormButtonBar>
    </div>
  )
}

export default Review
