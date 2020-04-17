import React from 'react'
import styled from 'styled-components'
import { H4, Callout } from '@blueprintjs/core'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'
import H2Title from '../../../Atoms/H2Title'

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
          <td>name</td>
        </tr>
        <tr>
          <td>Risk Limit:</td>
          <td>10</td>
        </tr>
        <tr>
          <td>Random Seed:</td>
          <td>12345</td>
        </tr>
        <tr>
          <td>Participating Jurisdictions:</td>
          <td>
            <a href="/link-to-jurisdictions-file">link</a>
          </td>
        </tr>
        <tr>
          <td>Audit Board Data Entry:</td>
          <td>Online</td>
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
          <tr>
            <td>9-1-1 Bond Measure</td>
            <td>City One, City two, a bunch more cities</td>
          </tr>
          <tr>
            <td>9-1-1 Bond Measure</td>
            <td>City One, City two, a bunch more cities</td>
          </tr>
          <tr>
            <td>9-1-1 Bond Measure</td>
            <td>City One, City two, a bunch more cities</td>
          </tr>
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
          <tr>
            <td>9-1-1 Bond Measure</td>
            <td>City One, City two, a bunch more cities</td>
          </tr>
          <tr>
            <td>9-1-1 Bond Measure</td>
            <td>City One, City two, a bunch more cities</td>
          </tr>
          <tr>
            <td>9-1-1 Bond Measure</td>
            <td>City One, City two, a bunch more cities</td>
          </tr>
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
