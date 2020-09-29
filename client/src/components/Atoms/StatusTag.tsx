import styled from 'styled-components'
import { Tag } from '@blueprintjs/core'

const StatusTag = styled(Tag).attrs({ minimal: true })`
  text-transform: uppercase;
  font-weight: 500;
`

export default StatusTag
