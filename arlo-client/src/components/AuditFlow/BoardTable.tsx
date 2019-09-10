import React from 'react'
import styled from 'styled-components'

const P = styled.p`
  margin-top: 100px;
`

interface Props {
  setIsLoading: (arg0: boolean) => void
  isLoading: boolean
}

const BoardTable: React.FC<Props> = ({  }: Props) => {
  return <P>Board Table</P>
}

export default BoardTable
