import React, { ReactNode } from 'react'
import styled from 'styled-components'

const ButtonBar = styled.div`
  margin: 50px 0 50px 0;
  text-align: center;
`

const RightButtonBar = styled.div`
  margin: 0;
  text-align: right;
`

interface IProps {
  right?: boolean
  children: ReactNode
}

const FormButtonBar: React.FC<IProps> = ({ children, right }: IProps) => {
  return right ? (
    <RightButtonBar>{children}</RightButtonBar>
  ) : (
    <ButtonBar>{children}</ButtonBar>
  )
}

export default FormButtonBar
