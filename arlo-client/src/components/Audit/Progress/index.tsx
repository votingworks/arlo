import React, { useState, useLayoutEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import styled from 'styled-components'
import { Table, Column, Cell } from '@blueprintjs/table'
import H2Title from '../../Atoms/H2Title'
import useJurisdictions, { JurisdictionRoundStatus } from '../useJurisdictions'

const PaddedCell = styled(Cell)`
  padding: 5px 5px 4px 5px;
`

const Progress: React.FC = () => {
  const { electionId } = useParams()
  const jurisdictions = useJurisdictions(electionId!)

  const columns = [
    <Column
      key="name"
      name="Jurisdiction Name"
      cellRenderer={(row: number) => (
        <PaddedCell>{jurisdictions[row].name}</PaddedCell>
      )}
    />,
    <Column
      key="status"
      name="Status"
      cellRenderer={(row: number) => {
        const { ballotManifest, currentRoundStatus } = jurisdictions[row]
        if (!currentRoundStatus) {
          const { processing } = ballotManifest
          switch (processing && processing.status) {
            case 'ERRORED':
              return <PaddedCell>Manifest upload failed</PaddedCell>
            case 'PROCESSED':
              return <PaddedCell>Manifest received</PaddedCell>
            default:
              return <PaddedCell>No manifest uploaded</PaddedCell>
          }
        } else {
          const prettyStatus = {
            [JurisdictionRoundStatus.NOT_STARTED]: 'Not started',
            [JurisdictionRoundStatus.IN_PROGRESS]: 'In progress',
            [JurisdictionRoundStatus.COMPLETE]: 'Complete',
          }
          return (
            <PaddedCell>{prettyStatus[currentRoundStatus.status]}</PaddedCell>
          )
        }
      }}
    />,
    <Column
      key="audited"
      name="Total Audited"
      cellRenderer={(row: number) => {
        const { currentRoundStatus } = jurisdictions[row]
        return (
          <PaddedCell>
            {currentRoundStatus && currentRoundStatus.numBallotsAudited}
          </PaddedCell>
        )
      }}
    />,
    <Column
      key="remaining"
      name="Remaining in Round"
      cellRenderer={(row: number) => {
        const { currentRoundStatus } = jurisdictions[row]
        return (
          <PaddedCell>
            {currentRoundStatus &&
              currentRoundStatus.numBallotsSampled -
                currentRoundStatus.numBallotsAudited}
          </PaddedCell>
        )
      }}
    />,
  ]

  const containerRef = useRef<HTMLDivElement>(null)
  const [tableWidth, setTableWidth] = useState<number | undefined>()
  useLayoutEffect(() => {
    if (containerRef.current) {
      setTableWidth(containerRef.current.clientWidth)
    }
  }, [])
  const columnWidths = tableWidth
    ? Array(columns.length).fill(tableWidth / columns.length)
    : undefined

  return (
    <div>
      <H2Title>Audit Progress by Jurisdiction</H2Title>
      <div ref={containerRef}>
        <Table
          numRows={jurisdictions.length}
          defaultRowHeight={30}
          columnWidths={columnWidths}
          enableRowHeader={false}
          enableColumnResizing={false}
        >
          {columns}
        </Table>
      </div>
    </div>
  )
}

export default Progress
