import React, { ReactNode } from 'react'
import { H3 } from '@blueprintjs/core'
import styled from 'styled-components'

export const Section = styled.div`
  margin: 20px 0 20px 0;
`

export const FormSectionDescription = styled.div`
  margin: 10px 0;
`

/* stylelint-disable declaration-no-important */
export const FormSectionLabel = styled(H3)`
  font-size: 18px !important;
  & + & {
    margin-top: 10px;
  }
`
/* stylelint-enable */

interface IProps {
  label?: string
  description?: string
  children: ReactNode
}

const FormSection: React.FC<IProps> = ({
  label,
  description,
  children,
}: IProps) => {
  return (
    <Section>
      {label ? <FormSectionLabel>{label}</FormSectionLabel> : undefined}
      {description ? (
        <FormSectionDescription>{description}</FormSectionDescription>
      ) : (
        undefined
      )}
      {children}
    </Section>
  )
}

export default FormSection
