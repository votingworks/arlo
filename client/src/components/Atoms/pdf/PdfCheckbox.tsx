import React from 'react'
import { Text, View } from '@react-pdf/renderer'

interface IProps {
  fontSize: number | string
  marginBottom?: number | string
  textAfterCheckbox?: string
  textBeforeCheckbox?: string
}

const PdfCheckbox = ({
  fontSize,
  marginBottom,
  textAfterCheckbox,
  textBeforeCheckbox,
}: IProps): JSX.Element => {
  return (
    <View
      style={{ display: 'flex', flexDirection: 'row', fontSize, marginBottom }}
    >
      {textBeforeCheckbox && <Text>{textBeforeCheckbox}&nbsp;&nbsp;</Text>}
      <Text
        style={{
          borderColor: 'black',
          borderWidth: 1,
          height: fontSize,
          width: fontSize,
        }}
      />
      {textAfterCheckbox && <Text>&nbsp;{textAfterCheckbox}</Text>}
    </View>
  )
}

export default PdfCheckbox
