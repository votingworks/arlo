import React from 'react'
import { H2 } from '@blueprintjs/core'
import styled from 'styled-components'

const StyledFormTitle = styled(H2)`
  margin: 40px 0 25px 0;
`

interface Props {
  children: any
}

const FormTitle = (props: Props) => {
  const { children } = props
  return <StyledFormTitle>{children}</StyledFormTitle>
}

export default FormTitle
