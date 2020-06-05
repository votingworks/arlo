import React from 'react'
import { useTable, useSortBy, Column, Row } from 'react-table'
import styled from 'styled-components'
import { Icon } from '@blueprintjs/core'

const StyledTable = styled.table`
  width: 100%;
  table-layout: fixed;

  thead {
    background-color: #e1e8ed; /* BlueprintJS light-gray3 */
    border-spacing: 0;
    color: #394b59; /* BlueprintJS dark-gray5 */
  }

  th,
  td {
    margin: 0;
    padding: 0.5rem;
    text-align: left;
  }

  tr:nth-child(even) {
    background-color: #f5f8fa; /* BlueprintJS light-gray5 */
  }
`

interface ITableProps<T extends object> {
  data: T[]
  columns: Column<T>[]
}

const Table = <T extends object>({ data, columns }: ITableProps<T>) => {
  const {
    getTableProps,
    getTableBodyProps,
    headers,
    rows,
    prepareRow,
  } = useTable(
    {
      data: React.useMemo(() => data, []),
      columns: React.useMemo(() => columns, []),
    },
    useSortBy
  )

  /* eslint-disable react/jsx-key */
  /* All the keys are added automatically by react-table */

  return (
    <StyledTable {...getTableProps()}>
      <thead>
        <tr>
          {headers.map(column => (
            <th {...column.getHeaderProps(column.getSortByToggleProps())}>
              {column.render('Header')}
              <span>
                {column.isSorted ? (
                  column.isSortedDesc ? (
                    <Icon icon="caret-down" />
                  ) : (
                    <Icon icon="caret-up" />
                  )
                ) : (
                  <Icon icon="double-caret-vertical" />
                )}
              </span>
            </th>
          ))}
        </tr>
      </thead>
      <tbody {...getTableBodyProps()}>
        {rows.map(row => {
          prepareRow(row)
          return (
            <tr {...row.getRowProps()}>
              {row.cells.map(cell => (
                <td {...cell.getCellProps()}>{cell.render('Cell')}</td>
              ))}
            </tr>
          )
        })}
      </tbody>
    </StyledTable>
  )
}

export const sortByRank = <T extends object>(rank: (data: T) => number) => (
  rowA: Row<T>,
  rowB: Row<T>
) => rank(rowA.original) - rank(rowB.original)

export default Table
