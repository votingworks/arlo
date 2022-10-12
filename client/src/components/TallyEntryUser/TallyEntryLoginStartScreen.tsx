import React from 'react'
import styled from 'styled-components'
import { Card, FormGroup, InputGroup, HTMLSelect, H1, Button } from '@blueprintjs/core'
import { Inner, Wrapper } from '../Atoms/Wrapper'

export const LogInPanel = styled(Card).attrs({ elevation: 1 })`
  padding: 50px 40px;
  margin: 100px auto 0 auto;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  text-align: center;
  width: 520px;
  height: 430px;
`

const AuditHeadingStyled = styled.div.attrs({ className: 'bp3-text-muted' })`
  margin-bottom: 10px;
  display: flex;
  justify-content: center;
`

interface IAuditHeadingProps {
  jurisdictionName: string
  auditName: string
}

export const AuditHeading: React.FC<IAuditHeadingProps> = ({
  jurisdictionName,
  auditName,
}) => (
  <AuditHeadingStyled>
    {jurisdictionName} &mdash; {auditName}
  </AuditHeadingStyled>
)

const MemberFieldset = styled.fieldset`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  text-align: left;
  .bp3-form-helper-text {
    min-height: 10px;
  }
`

const MemberFields: React.FC = () => {
  return (
    <MemberFieldset>
      <FormGroup label="Name" helperText=" ">
        <InputGroup />
      </FormGroup>
      <FormGroup
        label="Party Affiliation"
        labelInfo="(if required)"
        helperText=" "
      >
        <HTMLSelect fill>
          <option value="" />
          <option value="DEM">Democrat</option>
          <option value="REP">Republican</option>
          <option value="LIB">Libertarian</option>
          <option value="IND">Independent/Unaffiliated</option>
          <option value="OTH">Other</option>
        </HTMLSelect>
      </FormGroup>
    </MemberFieldset>
  )
}

interface ITallyEntryLoginStartScreenProps {
  jurisdictionId: string
  jurisdictionName: string
  auditName: string
}

const TallyEntryLoginStartScreen: React.FC<ITallyEntryLoginStartScreenProps> = ({
  jurisdictionId,
  jurisdictionName,
  auditName,
}) => {
  return (
    <Wrapper>
      <Inner flexDirection="column">
        <LogInPanel>
          <AuditHeading
            jurisdictionName={jurisdictionName}
            auditName={auditName}
          />
          <form>
            <H1>Tally Entry Log In</H1>
            <div
              style={{
                marginTop: '25px',
              }}
            >
              <MemberFields />
              <MemberFields />
            </div>
            <Button
              onClick={onLoginClick}
              large
              intent="primary"
              style={{ minWidth: '160px' }}
            >
              Log in
            </Button>
          </form>
        </LogInPanel>
      </Inner>
    </Wrapper>
  )
}

export default TallyEntryLoginStartScreen
