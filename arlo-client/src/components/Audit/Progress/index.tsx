import React, { useState, useLayoutEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import styled from 'styled-components'
import { Table, Column, Cell } from '@blueprintjs/table'
import H2Title from '../../Atoms/H2Title'
import useJurisdictions, { JurisdictionRoundStatus } from '../useJurisdictions'
import FormButton from '../../Atoms/Form/FormButton'
import JurisdictionDetail from './JurisdictionDetail'

const Wrapper = styled.div`
  flex-grow: 1;
`

const PaddedCell = styled(Cell)`
  padding: 5px 5px 4px 5px;
`

interface IProps {
  refreshId: string
}

const Progress: React.FC<IProps> = ({ refreshId }: IProps) => {
  const { electionId } = useParams<{ electionId: string }>()
  const jurisdictions = useJurisdictions(electionId, refreshId)
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const [jurisdictionDetail, setJurisdictionDetail] = useState(jurisdictions[0])
  const openDetail = (e: React.FormEvent, index: number) => {
    setJurisdictionDetail(jurisdictions[index])
    setIsDetailOpen(true)
  }

  const columns = [
    <Column
      key="name"
      name="Jurisdiction Name"
      cellRenderer={(row: number) => (
        <PaddedCell>
          <FormButton
            size="sm"
            intent="primary"
            minimal
            onClick={e => openDetail(e, row)}
          >
            {jurisdictions[row].name}
          </FormButton>
        </PaddedCell>
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
    <Wrapper>
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
      <JurisdictionDetail
        isOpen={isDetailOpen}
        jurisdiction={jurisdictionDetail}
        electionId={electionId}
        handleClose={() => setIsDetailOpen(false)}
      />
    </Wrapper>
  )
}

export default Progress
