import React, { ReactNode } from 'react'
import { Style } from '@react-pdf/types'
import { Text } from '@react-pdf/renderer'

interface IProps {
  children?: ReactNode
  lastInSection?: boolean
  style?: Style
}

const PdfP = ({ children, lastInSection, style }: IProps): JSX.Element => {
  return (
    <Text
      style={{
        marginBottom: lastInSection ? 0 : 10,
        overflow: 'hidden',
        ...style,
      }}
    >
      {children}
    </Text>
  )
}

export default PdfP
