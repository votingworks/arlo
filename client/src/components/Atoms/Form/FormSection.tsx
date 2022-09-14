import React, { ReactNode } from 'react'
import { H5 } from '@blueprintjs/core'
import styled from 'styled-components'

export const Section = styled.div`
  margin: 20px 0 30px 0;
`

export const FormSectionDescription = styled.div`
  margin: 10px 0;
`

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
      {label ? <H5>{label}</H5> : undefined}
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
