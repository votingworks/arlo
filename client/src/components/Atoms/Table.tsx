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
    padding: 0.5rem 0.4rem;
    text-align: left;
  }

  tr:nth-child(even) {
    background-color: #f5f8fa; /* BlueprintJS light-gray5 */
  }
`

interface IFilterInputProps<T extends object> {
  placeholder: string
  value: string
  onChange: (value: string) => void
}

export const FilterInput = <T extends object>({
  placeholder,
  value,
  onChange,
}: IFilterInputProps<T>) => (
  <div className="bp3-input-group .modifier">
    <span className="bp3-icon bp3-icon-filter"></span>
    <input
      type="text"
      className="bp3-input"
      placeholder={placeholder}
      value={value}
      onChange={e => onChange(e.target.value)}
    />
  </div>
)

interface ITableProps<T extends object> {
  data: T[]
  columns: Column<T>[]
}

export const Table = <T extends object>({ data, columns }: ITableProps<T>) => {
  const {
    getTableProps,
    getTableBodyProps,
    headers,
    rows,
    prepareRow,
  } = useTable(
    {
      data: React.useMemo(() => data, [data]),
      columns: React.useMemo(() => columns, [columns]),
      autoResetSortBy: false,
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
            <th
              {...column.getHeaderProps(
                column.getSortByToggleProps({ title: column.Header })
              )}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  paddingRight: '15px',
                }}
              >
                <span style={{ marginRight: '5px' }}>
                  {column.render('Header')}
                </span>
                {column.canSort && (
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
                )}
              </div>
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

export const sortByRank = <T extends object>(rank: (data: T) => number) =>
  // react-table requires the sortBy function be memoized, but the linter only
  // expects useCallback to be called directly within a component/hook.
  // eslint-disable-next-line react-hooks/rules-of-hooks
  React.useCallback(
    (rowA: Row<T>, rowB: Row<T>) => rank(rowA.original) - rank(rowB.original),
    [rank]
  )

export default Table
