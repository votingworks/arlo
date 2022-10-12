import React from 'react'
import {
  Colors,
  H1,
  InputGroup,
  FormGroup,
  HTMLSelect,
  Button,
  Card,
} from '@blueprintjs/core'
import styled from 'styled-components'
import { Inner } from '../Atoms/Wrapper'
import { ITallyEntryUser } from '../UserContext'

interface ILoginCodeProps {
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

const TallyEntryLogin: React.FC = () => {
  const
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
            Test County &mdash; General Election
            {/* {auditBoard.jurisdictionName} &mdash; {auditBoard.auditName} */}
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

export default TallyEntryLogin
