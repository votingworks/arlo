import React from 'react'

export const generateOptions = (count: number): JSX.Element[] => {
  let elements: JSX.Element[] = []
  for (let i = 1; i <= count; i++) {
    elements.push(<option key={i.toString()}>{i}</option>)
  }
  return elements
}

export default generateOptions
