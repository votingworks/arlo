import React from 'react'
import {
  Colors,
  H1,
  H2,
  H3,
  InputGroup,
  FormGroup,
  HTMLSelect,
  Button,
  Card,
} from '@blueprintjs/core'
import styled from 'styled-components'
import {
  JurisdictionAdminStatusBox,
  StatusBar,
  AuditHeading,
} from './Atoms/StatusBox'
import Wrapper, { Inner } from './Atoms/Wrapper'

interface IAuditBoardLogin {
  auditName: string
  jurisdictionName: string
  loginCode: string | null
  loginConfirmedAt: string | null
}

const auditBoards = {
  initial: {
    auditName: 'Jonah Batch Test',
    jurisdictionName: 'Los Angeles County',
    loginCode: null,
    loginConfirmedAt: null,
  },
  requested: {
    auditName: 'Jonah Batch Test',
    jurisdictionName: 'Los Angeles County',
    loginCode: '879',
    loginConfirmedAt: null,
  },
  confirmed: {
    auditName: 'Jonah Batch Test',
    jurisdictionName: 'Los Angeles County',
    loginCode: '879',
    loginConfirmedAt: new Date().toISOString(),
  },
}

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

const LoginStartScreen: React.FC<{ onLoginClick: () => void }> = ({
  onLoginClick,
}) => {
  return (
    <form>
      <H1>Tally Entry Log In</H1>
      {/* <p className="bp3-text-large">Enter your names</p> */}
      <div
        style={{
          marginTop: '25px',
          // display: 'grid',
          // gridTemplateColumns: '1fr 1fr',
          // gap: '10px',
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
  )
}

interface ILoginCodeProps {
  loginCode: IAuditBoardLogin['loginCode']
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

const LoginCodeScreen: React.FC<ILoginCodeProps> = ({ loginCode }) => {
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

const AuditBoardLogin: React.FC = () => {
  const [requested, setRequested] = React.useState(false)
  const auditBoard: IAuditBoardLogin = requested
    ? auditBoards.requested
    : auditBoards.initial
  return (
    <Wrapper>
      <Inner flexDirection="column">
        <LogInPanel>
          <div
            style={{
              marginBottom: '10px',
              fontWeight: 400,
              display: 'flex',
              justifyContent: 'center',
            }}
            className="bp3-text-muted"
          >
            <AuditHeading
              auditName={auditBoard.auditName}
              jurisdictionName={auditBoard.jurisdictionName}
            />
          </div>
          {(() => {
            if (!auditBoard.loginCode) {
              return (
                <LoginStartScreen onLoginClick={() => setRequested(true)} />
              )
            }
            if (!auditBoard.loginConfirmedAt) {
              return <LoginCodeScreen loginCode={auditBoard.loginCode} />
            }
          })()}
        </LogInPanel>
      </Inner>
    </Wrapper>
  )
}

export default AuditBoardLogin
