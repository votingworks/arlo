import React, { ReactNode } from 'react'
import { Text } from '@react-pdf/renderer'

interface IPdfHeadingProps {
  children?: ReactNode
}

export const PdfHeading = ({ children }: IPdfHeadingProps): JSX.Element => {
  return (
    <Text
      style={{
        fontSize: 18,
      }}
    >
      {children}
    </Text>
  )
}

interface IPdfSubHeadingProps {
  children?: ReactNode
}

export const PdfSubHeading = ({
  children,
}: IPdfSubHeadingProps): JSX.Element => {
  return (
    <Text
      style={{
        fontSize: 16,
        marginTop: 10,
      }}
    >
      {children}
    </Text>
  )
}
