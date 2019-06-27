import React from 'react'
import styled from 'styled-components'

const Section = styled.div`
  margin: 20px 0 20px 0;
`

const SectionDescription = styled.div`
  margin-top: 10px;
  font-size: 0.4em;
`

const SectionLabel = styled.div`
  font-size: 0.5em;
  font-weight: 700;
`

interface Props {
  label: string
  description?: string
  children: any
}

const FormSection = (props: Props) => {
  const { label, description, children } = props
  return (
    <Section>
      {label ? <SectionLabel>{label}</SectionLabel> : undefined}
      {description ? (
        <SectionDescription>{description}</SectionDescription>
      ) : (
        undefined
      )}
      {children}
    </Section>
  )
}

export default FormSection
