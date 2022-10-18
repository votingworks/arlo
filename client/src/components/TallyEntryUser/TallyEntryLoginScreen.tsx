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
  Classes,
} from '@blueprintjs/core'
import { useForm } from 'react-hook-form'
import { useMutation, useQueryClient } from 'react-query'
import { Inner, Wrapper } from '../Atoms/Wrapper'
import { ITallyEntryUser, IMember } from '../UserContext'
import { fetchApi } from '../../utils/api'

const useRequestCode = () => {
  const postRequestCode = async (body: { members: IMember[] }) =>
    fetchApi(`/auth/tallyentry/code`, {
      method: 'POST',
      body: JSON.stringify(body),
      headers: { 'Content-Type': 'application/json' },
    })

  const queryClient = useQueryClient()

  return useMutation(postRequestCode, {
    onSuccess: () => queryClient.invalidateQueries(['user']),
  })
}

const MemberFieldset = styled.fieldset`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  text-align: left;
  .${Classes.FORM_HELPER_TEXT} {
    height: 16px;
  }
`

interface ILoginStartFormValues {
  member1: IMember
  member2: IMember
}

const LoginStartForm: React.FC = () => {
  const { register, handleSubmit, errors, formState } = useForm<
    ILoginStartFormValues
  >()
  const requestCode = useRequestCode()

  const onSubmit = async (values: ILoginStartFormValues) => {
    const members: IMember[] = Object.values(values)
      .filter(member => member.name !== '')
      .map(member => ({
        name: member.name,
        affiliation: member.affiliation || null,
      }))
    try {
      await requestCode.mutateAsync({ members })
    } catch (error) {
      // Do nothing - errors toasted by queryClient
    }
  }

  const memberKeys = ['member1', 'member2'] as const
  return (
    <form>
      <H1 style={{ marginBottom: '35px' }}>Tally Entry Log In</H1>
      {memberKeys.map(memberKey => {
        const nameInputKey = `${memberKey}.name`
        const nameInputError = errors[memberKey]?.name
        const partySelectKey = `${memberKey}.affiliation`
        return (
          <MemberFieldset key={memberKey}>
            <FormGroup
              label="Name"
              labelFor={nameInputKey}
              helperText={nameInputError?.message || ' '} // Always render helper text to keep spacing consistent
              intent={nameInputError && 'danger'}
            >
              <InputGroup
                id={nameInputKey}
                name={nameInputKey}
                type="text"
                inputRef={register({
                  required: memberKey === 'member1' ? 'Enter your name' : false,
                })}
                intent={nameInputError && 'danger'}
              />
            </FormGroup>
            <FormGroup
              label="Party Affiliation"
              labelInfo="(if required)"
              labelFor={partySelectKey}
              helperText=" " // Always render helper text to keep spacing consistent
            >
              <HTMLSelect
                name={partySelectKey}
                id={partySelectKey}
                elementRef={register}
                fill
              >
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
      })}
      <Button
        onClick={handleSubmit(onSubmit)}
        large
        intent="primary"
        style={{ minWidth: '160px' }}
        loading={formState.isSubmitting}
      >
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
  padding-left: 20px; /* Account for extra letter-spacing on right */
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
      <p className={Classes.TEXT_LARGE}>
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

const AuditHeading = styled.div.attrs({ className: Classes.TEXT_MUTED })`
  margin-bottom: 10px;
  display: flex;
  justify-content: center;
`

export interface ITallyEntryLoginScreenProps {
  user: ITallyEntryUser
}

const TallyEntryLoginScreen: React.FC<ITallyEntryLoginScreenProps> = ({
  user,
}) => {
  const { jurisdictionName, auditName, loginCode } = user
  return (
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
  )
}

export default TallyEntryLoginScreen
