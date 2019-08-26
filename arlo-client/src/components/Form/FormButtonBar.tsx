import React, { ReactNode } from 'react'
import styled from 'styled-components'

const ButtonBar = styled.div`
  margin: 50px 0 50px 0;
  text-align: center;
`

interface Props {
  children: ReactNode
}

const FormButtonBar: React.FC<Props> = ({ children }: Props) => {
  return <ButtonBar>{children}</ButtonBar>
}

export default FormButtonBar
