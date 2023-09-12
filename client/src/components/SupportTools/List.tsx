import React from 'react'
import { useHistory } from 'react-router-dom'
import styled from 'styled-components'
import { Colors } from '@blueprintjs/core'

export const List = styled.ul`
  list-style: none;
  padding: 0;
  margin: 0;
`

const ItemContainer = styled.li`
  border-top: 1px solid ${Colors.LIGHT_GRAY4};
  &:last-child {
    border-bottom: 1px solid ${Colors.LIGHT_GRAY4};
  }

  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 10px;
  cursor: pointer;
  color: ${Colors.BLUE2};

  &:hover {
    text-decoration: none;
    color: ${Colors.BLUE1};
    background-color: ${Colors.LIGHT_GRAY4};
  }
  &:active {
    background-color: ${Colors.LIGHT_GRAY3};
  }
`

interface ILinkItemProps {
  children: React.ReactNode
  to: string
  style?: React.CSSProperties
}

export const LinkItem: React.FC<ILinkItemProps> = ({ to, children, style }) => {
  const history = useHistory()
  return (
    <ItemContainer role="link" onClick={() => history.push(to)} style={style}>
      {children}
    </ItemContainer>
  )
}
