import React, { ReactNode } from 'react'
import styled from 'styled-components'

const ButtonBar = styled.div`
  margin: 50px 0 50px 0;
  text-align: center;
`

interface IProps {
  children: ReactNode
}

const FormButtonBar: React.FC<IProps> = ({ children }: IProps) => {
  return <ButtonBar>{children}</ButtonBar>
}

export default FormButtonBar
