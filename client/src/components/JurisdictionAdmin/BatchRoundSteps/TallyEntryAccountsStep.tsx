import React, { useState } from 'react'
import {
  H5,
  Button,
  InputGroup,
  Card,
  Icon,
  Text,
  Dialog,
  Classes,
  Colors,
  Callout,
  H3,
} from '@blueprintjs/core'
import { useMutation, useQueryClient, useQuery } from 'react-query'
import { useForm, Controller } from 'react-hook-form'
import styled from 'styled-components'
import { IJurisdiction, IMember } from '../../UserContext'
import { StepPanel, StepPanelColumn, StepActions } from '../../Atoms/Steps'
import LinkButton from '../../Atoms/LinkButton'
import { fetchApi, ApiError } from '../../../utils/api'
import AsyncButton from '../../Atoms/AsyncButton'
import CopyToClipboard from '../../Atoms/CopyToClipboard'
import { downloadTallyEntryLoginLinkPrintout } from '../generateSheets'
import { ButtonRow, Column, Row } from '../../Atoms/Layout'
import CodeInputAtom from '../../Atoms/CodeInput'

const useTurnOnTallyEntryAccounts = (
  electionId: string,
  jurisdictionId: string
) => {
  const postTurnOnTallyEntryAccounts = () =>
    fetchApi(
      `/auth/tallyentry/election/${electionId}/jurisdiction/${jurisdictionId}`,
      { method: 'POST' }
    )

  const queryClient = useQueryClient()

  return useMutation(postTurnOnTallyEntryAccounts, {
    onSuccess: () => {
      queryClient.invalidateQueries([
        'jurisdictions',
        jurisdictionId,
        'tallyEntryAccountStatus',
      ])
    },
  })
}

export interface ITallyEntryLoginRequest {
  tallyEntryUserId: string
  members: IMember[]
  loginConfirmedAt: string | null
}

export interface ITallyEntryAccountStatus {
  passphrase: string | null
  loginRequests: ITallyEntryLoginRequest[]
}

const useTallyEntryAccountStatus = (
  electionId: string,
  jurisdictionId: string
) =>
  useQuery<ITallyEntryAccountStatus>(
    ['jurisdictions', jurisdictionId, 'tallyEntryAccountStatus'],
    () =>
      fetchApi(
        `/auth/tallyentry/election/${electionId}/jurisdiction/${jurisdictionId}`
      ),
    { refetchInterval: status => (status?.passphrase ? 1000 : false) }
  )

const useConfirmTallyEntryLogin = (
  electionId: string,
  jurisdictionId: string
) => {
  const postConfirmTallyEntryLogin = (body: {
    tallyEntryUserId: string
    loginCode: string
  }) =>
    fetchApi(
      `/auth/tallyentry/election/${electionId}/jurisdiction/${jurisdictionId}/confirm`,
      {
        method: 'POST',
        body: JSON.stringify(body),
        headers: { 'Content-Type': 'application/json' },
      }
    )

  const queryClient = useQueryClient()

  return useMutation(postConfirmTallyEntryLogin, {
    onError: () => {
      // Do nothing - override default toast behavior.
      // We'll show the message in the form.
    },
    onSuccess: () => {
      queryClient.invalidateQueries([
        'jurisdictions',
        jurisdictionId,
        'tallyEntryAccountStatus',
      ])
    },
  })
}

const useRejectTallyEntryLogin = (
  electionId: string,
  jurisdictionId: string
) => {
  const postRejectTallyEntryLogin = (body: { tallyEntryUserId: string }) =>
    fetchApi(
      `/auth/tallyentry/election/${electionId}/jurisdiction/${jurisdictionId}/reject`,
      {
        method: 'POST',
        body: JSON.stringify(body),
        headers: { 'Content-Type': 'application/json' },
      }
    )

  const queryClient = useQueryClient()

  return useMutation(postRejectTallyEntryLogin, {
    onSuccess: () => {
      queryClient.invalidateQueries([
        'jurisdictions',
        jurisdictionId,
        'tallyEntryAccountStatus',
      ])
    },
  })
}

interface ITurnOnTallyEntryAccountsPromptProps {
  nextStepUrl: string
  jurisdiction: IJurisdiction
}

const TurnOnTallyEntryAccountsPrompt: React.FC<ITurnOnTallyEntryAccountsPromptProps> = ({
  nextStepUrl,
  jurisdiction,
}) => {
  const turnOnTallyEntryAccounts = useTurnOnTallyEntryAccounts(
    jurisdiction.election.id,
    jurisdiction.id
  )

  return (
    <StepPanel style={{ alignItems: 'center' }}>
      <div style={{ width: '450px' }}>
        <H5>Do you want to set up tally entry accounts?</H5>
        <p>
          If you want to have multiple people entering tallies at the same time,
          set up tally entry accounts for them. Otherwise, use your account to
          enter the tally for each batch you audit.
        </p>
        <ButtonRow>
          <LinkButton to={nextStepUrl}>Skip</LinkButton>
          <AsyncButton
            intent="primary"
            onClick={() => turnOnTallyEntryAccounts.mutateAsync()}
          >
            Set Up Tally Entry Accounts
          </AsyncButton>
        </ButtonRow>
      </div>
    </StepPanel>
  )
}

const CodeInput = styled(CodeInputAtom)`
  input {
    width: 70px;
    font-size: 50px;
    height: 80px;
  }
`

interface IConfirmTallyEntryLoginProps {
  jurisdiction: IJurisdiction
  loginRequest: ITallyEntryLoginRequest | null
  onClose: () => void
}

const ConfirmTallyEntryLoginModal: React.FC<IConfirmTallyEntryLoginProps> = ({
  jurisdiction,
  loginRequest,
  onClose,
}) => {
  const confirmTallyEntryLogin = useConfirmTallyEntryLogin(
    jurisdiction.election.id,
    jurisdiction.id
  )
  const {
    handleSubmit,
    errors,
    formState,
    setError,
    control,
    reset,
  } = useForm<{
    loginCode: string
  }>({ reValidateMode: 'onSubmit' })
  const [isConfirmed, setIsConfirmed] = useState(false)

  // If there's no login request, the modal is closed. We return a closed Dialog
  // to make the closing animation work (instead of unmounting the Dialog, which
  // would have no animation).
  if (!loginRequest) {
    return <Dialog isOpen={false} />
  }

  const { tallyEntryUserId, members } = loginRequest

  const onSubmit = async ({ loginCode }: { loginCode: string }) => {
    try {
      await confirmTallyEntryLogin.mutateAsync({
        tallyEntryUserId,
        loginCode,
      })
      setIsConfirmed(true)
      setTimeout(() => {
        onClose()
        setIsConfirmed(false)
      }, 1500)
    } catch (error) {
      if (error instanceof ApiError) {
        reset()
        setError('loginCode', { message: error.message })
      }
    }
  }

  const membersString = members.map(member => member.name).join(', ')
  const codeValidationMessage = 'Enter a 3-digit login code'

  return (
    <Dialog
      icon="key"
      title={`Confirm Login: ${membersString}`}
      isOpen
      onClose={onClose}
    >
      <form onSubmit={handleSubmit(onSubmit)}>
        <Column
          className={Classes.DIALOG_BODY}
          style={{ height: '120px' }}
          justifyContent="center"
        >
          {!isConfirmed ? (
            <Column alignItems="center">
              {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
              <label
                className={Classes.TEXT_LARGE}
                style={{ display: 'block', marginBottom: '15px' }}
                id="loginCodeLabel"
              >
                Enter the login code shown on their screen:
              </label>
              <Controller
                name="loginCode"
                control={control}
                defaultValue=""
                render={({ ref: _, ...props }) => (
                  <CodeInput
                    aria-labelledby="loginCodeLabel"
                    length={3}
                    {...props}
                  />
                )}
                rules={{
                  required: codeValidationMessage,
                  maxLength: {
                    value: 3,
                    message: codeValidationMessage,
                  },
                  minLength: {
                    value: 3,
                    message: codeValidationMessage,
                  },
                }}
              />
            </Column>
          ) : (
            <Row justifyContent="center">
              <Icon
                icon="tick-circle"
                iconSize={30}
                color={Colors.GREEN3}
                style={{ marginRight: '7px' }}
              />
              <H3 style={{ margin: 0 }}>Login Confirmed</H3>
            </Row>
          )}
        </Column>
        <div className={Classes.DIALOG_FOOTER}>
          <div
            className={Classes.DIALOG_FOOTER_ACTIONS}
            style={{ height: '40px', alignItems: 'center' }}
          >
            {errors.loginCode && (
              <Callout intent="danger">{errors.loginCode.message}</Callout>
            )}
            {!isConfirmed ? (
              <div style={{ flexShrink: 0 }}>
                <Button disabled={formState.isSubmitting} onClick={onClose}>
                  Cancel
                </Button>
                <Button
                  intent="primary"
                  type="submit"
                  loading={formState.isSubmitting}
                >
                  Confirm
                </Button>
              </div>
            ) : (
              <Button onClick={onClose}>Close</Button>
            )}
          </div>
        </div>
      </form>
    </Dialog>
  )
}

const LoginRequestList = styled.div`
  overflow-y: auto;
  padding: 1px; /* Account for Card border */
`

const LoginRequestItem = styled(Card)`
  display: flex;
  gap: 10px;
  justify-content: space-between;
  align-items: center;
  padding: 10px 5px 10px 15px; /* Leave room for the reject button */
  height: 56px; /* Height of buttons */
`

interface IManageTallyEntryAccountsProps {
  jurisdiction: IJurisdiction
  passphrase: string
  loginRequests: ITallyEntryLoginRequest[]
}

const ManageTallyEntryAccounts: React.FC<IManageTallyEntryAccountsProps> = ({
  jurisdiction,
  passphrase,
  loginRequests,
}) => {
  const loginLinkUrl = `${window.location.origin}/tallyentry/${passphrase}`
  const [
    confirmingLoginRequest,
    setConfirmingLoginRequest,
  ] = useState<ITallyEntryLoginRequest | null>(null)
  const rejectTallyEntryLogin = useRejectTallyEntryLogin(
    jurisdiction.election.id,
    jurisdiction.id
  )

  return (
    <StepPanel>
      <StepPanelColumn>
        <H5>Share Tally Entry Login Link</H5>
        <div style={{ marginBottom: '10px' }}>
          <InputGroup readOnly value={loginLinkUrl} fill />
        </div>
        <ButtonRow>
          <CopyToClipboard
            getText={() => ({ text: loginLinkUrl, format: 'text/plain' })}
            label="Copy Link"
          />
          <AsyncButton
            icon="download"
            intent="primary"
            onClick={() =>
              downloadTallyEntryLoginLinkPrintout(
                loginLinkUrl,
                jurisdiction.name,
                jurisdiction.election.auditName
              )
            }
          >
            Download Printout
          </AsyncButton>
        </ButtonRow>
      </StepPanelColumn>
      <StepPanelColumn>
        <H5>Confirm Tally Entry Accounts</H5>
        {loginRequests.length === 0 ? (
          <Card>
            <p>
              <strong>No tally entry accounts have logged in yet</strong>
            </p>
            <p>
              Once each tally entry account logs in, confirm their identity
              here.
            </p>
          </Card>
        ) : (
          <LoginRequestList>
            {loginRequests.map(loginRequest => (
              <LoginRequestItem key={loginRequest.tallyEntryUserId}>
                <div>
                  {loginRequest.members.map(member => (
                    <Text key={member.name}>{member.name}</Text>
                  ))}
                </div>
                {loginRequest.loginConfirmedAt ? (
                  <Row style={{ paddingRight: '10px' }}>
                    <Icon icon="tick" intent="success" />
                    <span style={{ marginLeft: '7px', color: Colors.GREEN2 }}>
                      Logged In
                    </span>
                  </Row>
                ) : (
                  <Row gap="5px">
                    <Button
                      icon="key"
                      intent="primary"
                      onClick={() => setConfirmingLoginRequest(loginRequest)}
                    >
                      Enter Login Code
                    </Button>
                    <AsyncButton
                      minimal
                      icon="cross"
                      intent="danger"
                      aria-label="Reject login request"
                      onClick={() =>
                        rejectTallyEntryLogin.mutateAsync({
                          tallyEntryUserId: loginRequest.tallyEntryUserId,
                        })
                      }
                    />
                  </Row>
                )}
              </LoginRequestItem>
            ))}
          </LoginRequestList>
        )}
      </StepPanelColumn>
      <ConfirmTallyEntryLoginModal
        jurisdiction={jurisdiction}
        loginRequest={confirmingLoginRequest}
        onClose={() => setConfirmingLoginRequest(null)}
      />
    </StepPanel>
  )
}

interface ITallyEntryAccountsStep {
  previousStepUrl: string
  nextStepUrl: string
  jurisdiction: IJurisdiction
}

const TallyEntryAccountsStep: React.FC<ITallyEntryAccountsStep> = ({
  nextStepUrl,
  previousStepUrl,
  jurisdiction,
}) => {
  const tallyEntryAccountStatusQuery = useTallyEntryAccountStatus(
    jurisdiction.election.id,
    jurisdiction.id
  )

  if (!tallyEntryAccountStatusQuery.isSuccess) return null // Still loading

  const { passphrase, loginRequests } = tallyEntryAccountStatusQuery.data

  return (
    <>
      {!passphrase ? (
        <TurnOnTallyEntryAccountsPrompt
          nextStepUrl={nextStepUrl}
          jurisdiction={jurisdiction}
        />
      ) : (
        <ManageTallyEntryAccounts
          jurisdiction={jurisdiction}
          passphrase={passphrase}
          loginRequests={loginRequests}
        />
      )}
      <StepActions
        left={
          <LinkButton to={previousStepUrl} icon="chevron-left">
            Back
          </LinkButton>
        }
        right={
          <LinkButton
            to={nextStepUrl}
            intent="primary"
            rightIcon="chevron-right"
          >
            Continue
          </LinkButton>
        }
      />
    </>
  )
}

export default TallyEntryAccountsStep
