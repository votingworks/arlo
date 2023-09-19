import styled from 'styled-components'
import { Colors } from '@blueprintjs/core'

const FormButtonBar = styled.div`
  background-color: ${Colors.LIGHT_GRAY4};
  padding: 10px;
  display: flex;
  justify-content: space-between;
  > :only-child {
    margin-left: auto;
  }
`

export default FormButtonBar
