import React, { ReactNode } from 'react'
import styled from 'styled-components'
import FormTitle from './FormTitle'

const StyledFormWrapper = styled.div`
  display: block;
  position: relative;
  max-width: 20rem;
  text-align: left;
`

interface Props {
  title?: string
  children?: ReactNode
}

const FormWrapper: React.FC<Props> = ({ children, title }: Props) => (
  <StyledFormWrapper>
    <FormTitle>{title}</FormTitle>
    {children}
  </StyledFormWrapper>
)

export default React.memo(FormWrapper)
