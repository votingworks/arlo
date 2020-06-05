import React from 'react'
import {
  useTable,
  useSortBy,
  useFilters,
  Column,
  Row,
  ColumnInstance,
} from 'react-table'
import styled from 'styled-components'
import { Icon } from '@blueprintjs/core'

const Wrapper = styled.div``

const FilterWrapper = styled.div`
  display: flex;
  justify-content: flex-end;
  margin-bottom: 0.5rem;

  > div {
    width: 50%;
  }
`

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

const FilterInput = <T extends object>({
  column: { filterValue, setFilter },
}: {
  column: ColumnInstance<T>
}) => (
  <FilterWrapper>
    <div className="bp3-input-group .modifier">
      <span className="bp3-icon bp3-icon-filter"></span>
      <input
        type="text"
        className="bp3-input"
        placeholder="Filter by jurisdiction name..."
        value={filterValue || ''}
        onChange={e => setFilter(e.target.value || undefined)}
      />
    </div>
  </FilterWrapper>
)

const Table = <T extends object>({ data, columns }: ITableProps<T>) => {
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
      defaultColumn: React.useMemo(() => ({ Filter: FilterInput }), []),
    },
    useFilters,
    useSortBy
  )

  /* eslint-disable react/jsx-key */
  /* All the keys are added automatically by react-table */

  const filterableColumns = headers.filter(column => column.filter)
  if (filterableColumns.length > 1)
    throw Error('Only allowed to have one filterable column max')
  const [filterColumn] = filterableColumns
  console.log(headers, headers[0].canFilter, filterColumn)

  return (
    <Wrapper>
      {filterColumn && filterColumn.render('Filter')}
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
    </Wrapper>
  )
}

export const sortByRank = <T extends object>(rank: (data: T) => number) =>
  // eslint-disable-next-line react-hooks/rules-of-hooks
  React.useCallback(
    (rowA: Row<T>, rowB: Row<T>) => rank(rowA.original) - rank(rowB.original),
    [rank]
  )

export default Table
