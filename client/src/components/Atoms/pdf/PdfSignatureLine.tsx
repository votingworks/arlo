import React from 'react'
import { Style } from '@react-pdf/types'
import { Text, View } from '@react-pdf/renderer'

import { blankLine } from '../../../utils/string'

interface IProps {
  label?: string
  marginRight?: number | string
  style?: Style
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
            fontSize: 10,
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
