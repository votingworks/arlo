import React from 'react'
import styled from 'styled-components'

export const generateOptions = (count: number): JSX.Element[] => {
  const elements: JSX.Element[] = []
  for (let i = 1; i <= count; i += 1) {
    elements.push(
      <option value={i} key={i.toString()}>
        {i}
      </option>
    )
  }
  return elements
}

export const ErrorLabel = styled.p`
  color: #ff0000;
`

export default generateOptions
