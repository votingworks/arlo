import React, { ReactNode } from 'react'
import styled from 'styled-components'
import { Button, Card, Classes, Colors, InputGroup } from '@blueprintjs/core'

/**
 * A set of components to render a list-and-detail panel
 *
 * Example usage:
 *
 *  <ListAndDetail>
 *    <List>
 *      <ListItem>Item 1</ListItem>
 *      <ListItem selected>Item 2</ListItem>
 *    </List>
 *    <Detail>
 *      {detailsForSelectedListItem}
 *    </Detail>
 *  </ListAndDetail>
 */

export const ListAndDetail = styled(Card)`
  display: grid;
  grid-template-columns: 1fr 3fr;
  overflow-y: auto;
  padding: 0;
  width: 100%;
`

// ---------- List ----------

const ListContainer = styled.div`
  border-right: 1px solid ${Colors.LIGHT_GRAY2};
`

const ListSearch = styled(InputGroup).attrs({
  leftIcon: 'search',
  type: 'search',
})`
  margin: 16px 12px;
`

const ListItems = styled.ul<{ withTopBorder?: boolean }>`
  ${props =>
    props.withTopBorder && `border-top: 1px solid ${Colors.LIGHT_GRAY2};`}
  list-style: none;
  margin: 0;
  padding: 0;
  padding-bottom: 40px;
`

interface IListProps {
  search?: {
    placeholder: string
    setQuery: (query: string) => void
  }
}

export const List: React.FC<IListProps> = ({ search, children }) => {
  return (
    <ListContainer>
      {search && (
        <ListSearch
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            search.setQuery(e.target.value)
          }
          placeholder={search.placeholder}
        />
      )}
      <ListItems withTopBorder={Boolean(search)}>{children}</ListItems>
    </ListContainer>
  )
}

// ---------- ListItem ----------

const ListItemContainer = styled.li<{ selected?: boolean }>`
  border-bottom: 1px solid ${Colors.LIGHT_GRAY4};

  button.${Classes.BUTTON} {
    background-color: ${props =>
      props.selected
        ? 'rgba(19, 124, 189, 0.15)' // Blueprint <Button intent="primary" minimal> hover color
        : 'transparent'};
    border-radius: 0;
    padding: 12px 16px;
    width: 100%;
  }
`

interface IListItemProps {
  children?: ReactNode
  onClick: () => void
  selected?: boolean
}

export const ListItem: React.FC<IListItemProps> = ({
  children,
  onClick,
  selected,
}) => {
  return (
    <ListItemContainer selected={selected}>
      <Button
        alignText="left"
        intent={selected ? 'primary' : undefined}
        minimal
        onClick={onClick}
      >
        {children}
      </Button>
    </ListItemContainer>
  )
}

// ---------- Detail ----------

export const Detail = styled.div`
  padding: 16px;
`
