import React from 'react'
import { Text, View } from '@react-pdf/renderer'
import { blankLine } from '../../../utils/string'

interface IProps {
  label?: string
  marginRight?: number | string
}

const PdfSignatureLine = ({ label, marginRight }: IProps): JSX.Element => {
  return (
    <View
      style={{
        alignItems: 'center',
        display: 'flex',
        flexDirection: 'column',
        marginRight,
      }}
    >
      <Text>x{blankLine(30)}</Text>
      {label && <Text style={{ fontSize: 9, marginTop: 6 }}>{label}</Text>}
    </View>
  )
}

export default PdfSignatureLine
