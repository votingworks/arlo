import React from 'react'
import styled from 'styled-components'

const ButtonBar = styled.div`
  margin: 50px 0 50px 0;
  text-align: center;
`

interface Props {
  children: any
}

const FormButtonBar = (props: Props) => {
  return <ButtonBar>{props.children}</ButtonBar>
}

export default FormButtonBar
