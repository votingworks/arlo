import React, { ReactNode } from 'react'
import styled from 'styled-components'
import {
  Button,
  Card,
  Classes,
  Colors,
  IconName,
  InputGroup,
} from '@blueprintjs/core'

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
  grid-template-columns: 240px 1fr;
  overflow-y: auto;
  padding: 0;
  width: 100%;
`

// ---------- List ----------

const ListContainer = styled.div`
  border-right: 1px solid ${Colors.LIGHT_GRAY2};
  overflow-y: auto;
`

const ListSearch = styled.div`
  border-bottom: 1px solid ${Colors.LIGHT_GRAY2};
  padding: 16px 12px;
`

const ListItems = styled.ul`
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
        <ListSearch>
          <InputGroup
            leftIcon="search"
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              search.setQuery(e.target.value)
            }
            placeholder={search.placeholder}
            type="search"
          />
        </ListSearch>
      )}
      <ListItems>{children}</ListItems>
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
  rightIcon?: IconName
  selected?: boolean
}

export const ListItem: React.FC<IListItemProps> = ({
  children,
  onClick,
  rightIcon,
  selected,
}) => {
  return (
    <ListItemContainer selected={selected}>
      <Button
        alignText="left"
        intent={selected ? 'primary' : undefined}
        minimal
        onClick={onClick}
        rightIcon={rightIcon}
      >
        {children}
      </Button>
    </ListItemContainer>
  )
}

// ---------- Detail ----------

export const Detail = styled.div`
  overflow-y: auto;
  padding: 16px;
`
