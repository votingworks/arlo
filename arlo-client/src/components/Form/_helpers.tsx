import React from 'react'
import styled from 'styled-components'

export const generateOptions = (count: number): JSX.Element[] => {
  let elements: JSX.Element[] = []
  for (let i = 1; i <= count; i++) {
    elements.push(<option key={i.toString()}>{i}</option>)
  }
  return elements
}

export const ErrorLabel = styled.p`
  color: #ff0000;
  font-size: 10px;
`

export default generateOptions
