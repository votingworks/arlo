import React from 'react'
import styled from 'styled-components'
import {
  Card,
  FormGroup,
  InputGroup,
  HTMLSelect,
  H1,
  Button,
  Colors,
} from '@blueprintjs/core'
import { Inner, Wrapper } from '../Atoms/Wrapper'
import { ITallyEntryUser } from '../UserContext'

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

const LoginStartForm: React.FC = () => {
  return (
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
      <Button large intent="primary" style={{ minWidth: '160px' }}>
        Log in
      </Button>
    </form>
  )
}

interface ILoginCodeDisplayProps {
  loginCode: ITallyEntryUser['loginCode']
}

const LoginCode = styled.div`
  font-size: 90px;
  font-weight: 700;
  color: ${Colors.BLUE3};
  letter-spacing: 20px;
  padding-left: 20px; // Account for extra letter-spacing on right
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
`

const LoginCodeDisplay: React.FC<ILoginCodeDisplayProps> = ({ loginCode }) => {
  return (
    <>
      <H1 style={{ margin: 0 }}>Login Code</H1>
      <LoginCode>{loginCode}</LoginCode>
      <p className="bp3-text-large">
        Tell your login code to the person running your audit.
      </p>
    </>
  )
}

const LogInPanel = styled(Card).attrs({ elevation: 1 })`
  padding: 50px 40px;
  margin: 100px auto 0 auto;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  text-align: center;
  width: 520px;
  height: 430px;
`

const AuditHeading = styled.div.attrs({ className: 'bp3-text-muted' })`
  margin-bottom: 10px;
  display: flex;
  justify-content: center;
`

interface ITallyEntryLoginScreenProps {
  user: ITallyEntryUser
}

const TallyEntryLoginScreen: React.FC<ITallyEntryLoginScreenProps> = ({
  user,
}) => {
  const { jurisdictionName, auditName, loginCode } = user
  return (
    <Wrapper>
      <Inner flexDirection="column">
        <LogInPanel>
          <AuditHeading>
            {jurisdictionName} &mdash; {auditName}
          </AuditHeading>
          {loginCode === null ? (
            <LoginStartForm />
          ) : (
            <LoginCodeDisplay loginCode={loginCode} />
          )}
        </LogInPanel>
      </Inner>
    </Wrapper>
  )
}

export default TallyEntryLoginScreen
