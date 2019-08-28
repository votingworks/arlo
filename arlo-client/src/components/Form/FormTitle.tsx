import React from 'react'
import { H2 } from '@blueprintjs/core'
import styled from 'styled-components'

/* stylelint-disable declaration-no-important */
const StyledFormTitle = styled(H2)`
  margin: 40px 0 25px 0;
  font-size: 21px !important;
`
/* stylelint-enable */

interface Props {
  children: React.ReactNode
}

const FormTitle: React.FC<Props> = ({ children }: Props) => (
  <StyledFormTitle>{children}</StyledFormTitle>
)

export default FormTitle
