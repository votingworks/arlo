import React, { ReactNode } from 'react'
import { View } from '@react-pdf/renderer'

interface IPdfTableProps {
  children?: ReactNode
}

/**
 * The PDF equivalent of an HTML <table>
 */
export const PdfTable = ({ children }: IPdfTableProps): JSX.Element => {
  return (
    <View
      style={{
        alignItems: 'center',
        borderColor: 'black',
        borderLeftWidth: 1,
        borderTopWidth: 1,
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
      }}
    >
      {children}
    </View>
  )
}

interface IPdfTrProps {
  children?: ReactNode
}

/**
 * The PDF equivalent of an HTML <tr>
 */
export const PdfTr = ({ children }: IPdfTrProps): JSX.Element => {
  return (
    <View style={{ display: 'flex', flexDirection: 'row', width: '100%' }}>
      {children}
    </View>
  )
}

interface IPdfTdProps {
  children?: ReactNode
}

/**
 * The PDF equivalent of an HTML <td>
 */
export const PdfTd = ({ children }: IPdfTdProps): JSX.Element => {
  return (
    <View
      style={{
        borderBottomWidth: 1,
        borderColor: 'black',
        borderRightWidth: 1,
        flex: 1, // Results in table columns of equal width
        padding: 6,
      }}
    >
      {children}
    </View>
  )
}
