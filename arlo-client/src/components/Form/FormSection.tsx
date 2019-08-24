import React, { ReactNode } from 'react'
import styled from 'styled-components'

export const Section = styled.div`
  margin: 20px 0 20px 0;
`

export const FormSectionDescription = styled.div`
  margin: 10px 0;
`

export const FormSectionLabel = styled.div`
  font-weight: 700;
  & + & {
    margin-top: 10px;
  }
`

interface Props {
  label?: string
  description?: string
  children: ReactNode
}

const FormSection: React.FC<Props> = ({
  label,
  description,
  children,
}: Props) => {
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
