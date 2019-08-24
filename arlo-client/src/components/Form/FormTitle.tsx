import React, { ReactNode } from 'react'
import styled from 'styled-components'

const StyledFormTitle = styled.div`
  margin: 40px 0 25px 0;
  text-align: center;
  font-size: 0.8em;
`

interface Props {
  children: ReactNode
}

const FormTitle: React.FC<Props> = ({ children }: Props) => (
  <StyledFormTitle>{children}</StyledFormTitle>
)

export default FormTitle
