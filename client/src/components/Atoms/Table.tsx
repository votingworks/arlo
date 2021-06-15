import React from 'react'
import { useTable, useSortBy, Column, Row } from 'react-table'
import styled from 'styled-components'
import { Icon, HTMLTable, Button } from '@blueprintjs/core'
import { downloadFile } from '../utilities'

const StyledTable = styled.table`
  width: 100%;
  table-layout: fixed;

  thead,
  tfoot {
    background-color: #e1e8ed; /* BlueprintJS light-gray3 */
    border-spacing: 0;
    color: #394b59; /* BlueprintJS dark-gray5 */
    font-weight: 700;
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

interface IDownloadCSVButtonProps {
  tableId: string
  fileName?: string
}

export const DownloadCSVButton = ({
  tableId,
  fileName,
}: IDownloadCSVButtonProps) => {
  const onClick = () => {
    const table = document.querySelector(`#${tableId}`)!
    const headers = Array.from(table.querySelectorAll('th')).map(
      header => header.innerText
    )
    const bodyAndFooter = Array.from(
      table.querySelectorAll('tbody tr, tfoot tr')
    ).map(row =>
      Array.from(row.querySelectorAll('td')).map(cell => cell.innerText)
    )
    const tableRows = [headers].concat(bodyAndFooter)
    const quotedRows = tableRows.map(row =>
      row.map(cell => `"${cell.replace(/"/g, '""')}"`)
    )
    const csvString = quotedRows.map(row => row.join(',')).join('\n')
    const csvBlob = new Blob([csvString], { type: 'text/csv' })
    downloadFile(csvBlob, fileName)
  }

  return (
    <Button icon="download" onClick={onClick}>
      Download as CSV
    </Button>
  )
}

interface ITableProps<T extends object> {
  data: T[]
  columns: Column<T>[]
  id?: string
}

export const Table = <T extends object>({
  data,
  columns,
  id,
}: ITableProps<T>) => {
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
    <StyledTable id={id} {...getTableProps()}>
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
      {columns.some(column => column.Footer) && (
        <tfoot>
          <tr>
            {headers.map(column => (
              <td {...column.getFooterProps()}>{column.render('Footer')}</td>
            ))}
          </tr>
        </tfoot>
      )}
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

// FlexTable uses flexbox styling to compute thead/tbody height.
// This allows us to create a scrollable table body when there's overflow.
// Columns will all have the same width by default.
// Based on https://stackoverflow.com/a/29512692/1472662
// eslint-disable-next-line no-unused-vars, @typescript-eslint/no-unused-vars
export const FlexTable = styled(({ scrollable, ...props }) => (
  <HTMLTable {...props} />
))`
  display: flex;
  flex-direction: column;
  box-shadow: 0 0 0 1px rgb(16 22 26 / 15%); /* Copied from Blueprint */
  width: 100%;

  thead {
    flex: 0 0 auto;
    box-shadow: inset 0 -1px 0 0 rgb(16 22 26 / 15%); /* Copied from Blueprint */
    width: 100%;
  }

  tbody {
    display: block;
    flex: 1 1 auto;
    overflow-y: ${props => (props.scrollable ? 'scroll' : 'none')};
  }

  /* Add a hidden scrollbar so headers line up with columns */
  thead tr::after {
    visibility: hidden;
    overflow-y: ${props => (props.scrollable ? 'scroll' : 'none')};
    content: '';
  }

  tr {
    display: flex;
  }

  th,
  td {
    flex: 1 0 0;
  }

  td {
    overflow-x: hidden;
    overflow-wrap: break-word;
  }

  /* Remove Blueprint border from first row */
  tbody tr:first-child td {
    box-shadow: none !important; /* stylelint-disable-line declaration-no-important */
  }
`

export default Table
