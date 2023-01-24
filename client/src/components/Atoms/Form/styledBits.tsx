import { HTMLSelect, Label } from '@blueprintjs/core'
import styled from 'styled-components'
import FormField from './FormField'

export const Select = styled(HTMLSelect)`
  margin-left: 5px;
`

export const TwoColumnSection = styled.div`
  display: flex;
  flex-direction: column;
  margin-top: 25px;
  width: 100%;
`

export const InputFieldRow = styled.div`
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  margin-bottom: 25px;
  width: 100%;
`

export const FlexField = styled(FormField)`
  flex-grow: 2;
  width: unset;
  padding-right: 60px;
`

export const InputLabel = styled(Label)`
  display: inline-block;
  flex-grow: 2;
  width: unset;
  flex-basis: 50%;
`

export const Action = styled.p`
  margin: 5px 0 0 0;
  width: max-content;
  color: #000088;
  &:hover {
    cursor: pointer;
  }
`
