import React, { ReactNode } from 'react'
import styled from 'styled-components'
import H3Title from '../H3Title'

export const Section = styled.div`
  margin: 20px 0 30px 0;
  h5 {
    margin-bottom: 3px;
  }
`

export const FormSectionDescription = styled.div`
  margin: 10px 0;
`

interface IProps {
  label?: string
  description?: string
  children: ReactNode
  style?: React.CSSProperties
}

const FormSection: React.FC<IProps> = ({
  label,
  description,
  children,
  style,
}: IProps) => {
  return (
    <Section style={style}>
      {label ? <H3Title>{label}</H3Title> : undefined}
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
