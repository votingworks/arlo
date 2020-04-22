import React from 'react'
import styled from 'styled-components'
import { useParams } from 'react-router-dom'
import { H4, Callout } from '@blueprintjs/core'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'
import H2Title from '../../../Atoms/H2Title'
import useAuditSettings from '../useAuditSettings'
import useContestsApi from '../useContestsApi'
import { IContest } from '../../../../types'
import useParticipantsApi from '../useParticipantsApi'

const SettingsTable = styled.table`
  width: 100%;
  text-align: left;
  line-height: 30px;

  td:nth-child(even) {
    width: 50%;
  }
`
const ContestsTable = styled.table`
  margin: 50px 0;
  width: 100%;
  text-align: left;
  line-height: 30px;

  td,
  th {
    padding: 0 10px;
  }
  thead {
    background-color: #137cbd;
    color: #ffffff;
  }
  tr:nth-child(even) {
    background-color: #f5f8fa;
  }
`

interface IProps {
  locked: boolean
  prevStage: ISidebarMenuItem
}

const Review: React.FC<IProps> = ({ prevStage }: IProps) => {
  const { electionId } = useParams()
  const [{ electionName, randomSeed, riskLimit, online }] = useAuditSettings(
    electionId!
  )
  const participants = useParticipantsApi(electionId!)
  const [{ contests }] = useContestsApi(electionId!, true)
  const targetedContests = contests
    .filter(c => c.isTargeted === true)
    .map(c => ({
      ...c,
      jurisdictionIds: c.jurisdictionIds.map(j =>
        participants.length > 0 ? participants.find(p => p.id === j)!.name : ''
      ),
    }))
  const opportunisticContests = contests
    .filter(c => c.isTargeted === false)
    .map(c => ({
      ...c,
      jurisdictionIds: c.jurisdictionIds.map(j =>
        participants.length > 0 ? participants.find(p => p.id === j)!.name : ''
      ),
    }))
  return (
    <div>
      <H2Title>Review &amp; Launch</H2Title>
      <Callout intent="warning">
        Once the audit is started, the audit definition will no longer be
        editable. Please make sure this data is correct before launching the
        audit.
      </Callout>
      <br />
      <H4>Audit Settings</H4>
      <SettingsTable>
        <tr>
          <td>Election Name:</td>
          <td>{electionName}</td>
        </tr>
        <tr>
          <td>Risk Limit:</td>
          <td>{riskLimit}</td>
        </tr>
        <tr>
          <td>Random Seed:</td>
          <td>{randomSeed}</td>
        </tr>
        <tr>
          <td>Participating Jurisdictions:</td>
          <td>
            <a href="/link-to-jurisdictions-file">link</a>
          </td>
        </tr>
        <tr>
          <td>Audit Board Data Entry:</td>
          <td>{online ? 'Online' : 'Offline'}</td>
        </tr>
      </SettingsTable>
      <ContestsTable>
        <thead>
          <tr>
            <th>Target Contests</th>
            <th>Jurisdictions</th>
          </tr>
        </thead>
        <tbody>
          {targetedContests.map((c: IContest) => (
            <tr key={c.id}>
              <td>{c.name}</td>
              <td>{c.jurisdictionIds.join(', ')}</td>
            </tr>
          ))}
        </tbody>
      </ContestsTable>
      <ContestsTable>
        <thead>
          <tr>
            <th>Opportunistic Contests</th>
            <th>Jurisdictions</th>
          </tr>
        </thead>
        <tbody>
          {opportunisticContests.map((c: IContest) => (
            <tr key={c.id}>
              <td>{c.name}</td>
              <td>{c.jurisdictionIds.join(', ')}</td>
            </tr>
          ))}
        </tbody>
      </ContestsTable>
      <H4>Sample Size Options</H4>
      <FormButtonBar>
        <FormButton onClick={prevStage.activate}>Back</FormButton>
      </FormButtonBar>
    </div>
  )
}

export default Review
