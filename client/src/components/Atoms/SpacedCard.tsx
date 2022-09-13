import React from 'react'
import styled from 'styled-components'
import { Card, Elevation, ICardProps } from '@blueprintjs/core'

const SpacedCard = styled(Card)`
  &:not(:first-of-type) {
    margin-top: 20px;
  }
`

const ElevatedCard = (props: ICardProps): React.ReactElement => (
  <SpacedCard elevation={Elevation.TWO} {...props} />
)

export default ElevatedCard
