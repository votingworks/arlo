import React from 'react'
import { Text } from '@react-pdf/renderer'

interface IProps {
  fontSize: number | string
}

const PdfCheckbox = ({ fontSize }: IProps): JSX.Element => {
  return (
    <Text
      style={{
        borderColor: 'black',
        borderWidth: 1,
        height: fontSize,
        width: fontSize,
      }}
    />
  )
}

export default PdfCheckbox
