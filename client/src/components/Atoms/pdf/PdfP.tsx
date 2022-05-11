import React, { ReactNode } from 'react'
import { Text } from '@react-pdf/renderer'

import { PdfStyle } from './styles'

interface IProps {
  children?: ReactNode
  lastInSection?: boolean
  style?: PdfStyle
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
