import React from 'react'
import { View } from '@react-pdf/renderer'

const PdfDividerLine = (): JSX.Element => {
  return (
    <View
      style={{
        borderColor: 'black',
        borderTopWidth: 1,
        width: '100%',
      }}
    />
  )
}

export default PdfDividerLine
