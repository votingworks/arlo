import React from 'react'
import { Text, View } from '@react-pdf/renderer'

import { blankLine } from '../../../utils/string'
import { PdfStyle } from './styles'

interface IProps {
  label?: string
  marginRight?: number | string
  style?: PdfStyle
}

const PdfSignatureLine = ({
  label,
  marginRight,
  style,
}: IProps): JSX.Element => {
  return (
    <View
      style={{
        alignItems: 'center',
        display: 'flex',
        flexDirection: 'column',
        marginRight,
        ...style,
      }}
    >
      <Text>x{blankLine(30)}</Text>
      {label && (
        <Text
          style={{
            fontSize: 9,
            marginTop: 6,
          }}
        >
          {label}
        </Text>
      )}
    </View>
  )
}

export default PdfSignatureLine
