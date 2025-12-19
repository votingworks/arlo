import React from 'react'
import { H3 } from '@blueprintjs/core'
import styled from 'styled-components'

/* stylelint-disable declaration-no-important */
const StyledH3 = styled(H3)`
  margin: 25px 0 10px 0;
  font-size: 19px !important;
`
/* stylelint-enable */

interface IProps {
  children: React.ReactNode
}

const H3Title: React.FC<IProps> = ({ children }: IProps) => (
  <StyledH3>{children}</StyledH3>
)

export default H3Title
