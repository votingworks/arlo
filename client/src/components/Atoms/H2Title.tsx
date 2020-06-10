import React from 'react'
import { H2 } from '@blueprintjs/core'
import styled from 'styled-components'

/* stylelint-disable declaration-no-important */
const StyledH2 = styled(H2)`
  margin: 40px 0 25px 0;
  font-size: 21px !important;
`
/* stylelint-enable */

interface IProps {
  children: React.ReactNode
}

const H2Title: React.FC<IProps> = ({ children }: IProps) => (
  <StyledH2>{children}</StyledH2>
)

export default H2Title
