import React from 'react'
import styled from 'styled-components'

const Button = styled.button`
  margin: 0 auto;
  border-radius: 5px;
  background: rgb(211, 211, 211);
  width: 200px;
  height: 30px;
  color: #000000;
  font-size: 0.4em;
  font-weight: 700;
`

const InlineButton = styled.button`
  margin: 10px 0 30px 0;
  border-radius: 5px;
  background: rgb(211, 211, 211);
  width: 275px;
  height: 20px;
  color: 700;
  font-size: 0.4em;
  font-weight: 700;
`

const SmallInlineButton = styled.button`
  margin: 10px 0 30px 0;
  border-radius: 5px;
  background: rgb(211, 211, 211);
  width: 170px;
  height: 20px;
  color: #000000;
  font-size: 0.4em;
  font-weight: 700;
`

interface Props {
  disabled?: boolean
  onClick?: any
  children?: any
  inline?: boolean
  size?: string
}
const FormButton = (props: Props) => {
  const { disabled, onClick, size, inline, children } = props
  return React.createElement(
    inline ? (size === 'sm' ? SmallInlineButton : InlineButton) : Button,
    { disabled, onClick, ...props },
    children
  )
}

export default FormButton
