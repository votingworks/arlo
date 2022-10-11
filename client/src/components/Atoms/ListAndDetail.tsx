import React from 'react'
import styled from 'styled-components'
import { Card, InputGroup, Colors } from '@blueprintjs/core'

export const ListAndDetail = styled(Card)`
  display: grid;
  grid-template-columns: 1fr 3fr;
  padding: 0;
`

export const List = styled.div`
  height: 100%;
  border-right: 1px solid ${Colors.LIGHT_GRAY2};
`
export const ListItems = styled.ul`
  list-style: none;
  padding: 0;
  margin: 0;
  border-top: 1px solid ${Colors.LIGHT_GRAY2};
`

// TODO put a button inside for :active styling
export const ListItem = styled.li`
  padding: 10px 15px;
  border-bottom: 1px solid ${Colors.LIGHT_GRAY4};
  cursor: pointer;

  background-color: ${props => (props.selected ? Colors.LIGHT_GRAY4 : 'white')};

  &:hover {
    background-color: ${props =>
      props.selected ? Colors.LIGHT_GRAY4 : Colors.LIGHT_GRAY5};
  }
`

export const ListSearch = styled(InputGroup).attrs({
  type: 'search',
  leftIcon: 'search',
})`
  margin: 15px 10px;
`

export const Detail = styled.div`
  padding: 15px;
`
