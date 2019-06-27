import React from 'react'
import styled from 'styled-components'

const StyledFormTitle = styled.div`
  margin: 40px 0 25px 0;
  text-align: center;
  font-size: 0.8em;
`

interface Props {
  children: any
}

const FormTitle = (props: Props) => {
  const { children } = props
  return <StyledFormTitle>{children}</StyledFormTitle>
}

export default FormTitle
