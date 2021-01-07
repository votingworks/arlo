import React from 'react'
import { ReactQueryDevtools } from 'react-query/devtools'
import { QueryClientProvider, QueryClient } from 'react-query'
import { Redirect, Route, Switch } from 'react-router-dom'
import { toast } from 'react-toastify'
import styled from 'styled-components'
import {
  H3,
  Button,
  HTMLTable,
  Classes,
  H2,
  AnchorButton,
  Tag,
  H4,
  ButtonGroup,
  Alignment,
  Colors,
  Intent,
} from '@blueprintjs/core'
import { useForm } from 'react-hook-form'
import { useAuthDataContext } from '../UserContext'
import LinkButton from '../Atoms/LinkButton'
import { Wrapper, Inner } from '../Atoms/Wrapper'
import {
  useOrganizations,
  useOrganization,
  useCreateAuditAdmin,
  useElection,
  IAuditAdmin,
  IElection,
  useCreateOrganization,
} from './support-api'

const queryClient = new QueryClient(
  // Turn off query retries in test so we can mock effectively
  process.env.NODE_ENV === 'test'
    ? {
        defaultOptions: { queries: { retry: false } },
      }
    : {}
)

const SupportTools = () => {
  const auth = useAuthDataContext()
  if (!auth) return null // Still loading
  if (!auth.superadminUser) return <Redirect to="/" />

  return (
    <QueryClientProvider client={queryClient}>
      <Wrapper>
        <Inner>
          <div style={{ margin: '30px 0', width: '100%' }}>
            <Switch>
              <Route exact path="/support">
                <Organizations />
              </Route>
              <Route path="/support/orgs/:organizationId">
                {({ match }) => (
                  <Organization organizationId={match!.params.organizationId} />
                )}
              </Route>
              <Route path="/support/audits/:electionId">
                {({ match }) => <Audit electionId={match!.params.electionId} />}
              </Route>
            </Switch>
          </div>
        </Inner>
      </Wrapper>
      {process.env.NODE_ENV !== 'test' && (
        // Dev tools are automatically excluded from production, but we also
        // don't want them clogging up the DOM output in test
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  )
}

const Column = styled.div`
  width: 50%;
  padding-right: 30px;
`

const ButtonList = styled(ButtonGroup).attrs({
  vertical: true,
  minimal: true,
  large: true,
  alignText: Alignment.LEFT,
})`
  border: 1px solid ${Colors.LIGHT_GRAY3};
  width: 100%;
  .bp3-button {
    border-radius: 0;
    &:not(:first-child) {
      border-top: 1px solid ${Colors.LIGHT_GRAY3};
    }
  }
`

const Organizations = () => {
  const organizations = useOrganizations()
  const createOrganization = useCreateOrganization()

  const { register, handleSubmit, reset, formState } = useForm<{
    name: string
  }>()

  if (organizations.isLoading || organizations.isIdle) return null
  if (organizations.isError) {
    toast.error(organizations.error.message)
    return null
  }

  const onSubmitCreateOrganization = async ({ name }: { name: string }) => {
    try {
      await createOrganization.mutateAsync({ name })
      reset()
    } catch (error) {
      toast.error(error.message)
    }
  }

  return (
    <Column>
      <H2>Organizations</H2>
      <form
        style={{ display: 'flex' }}
        onSubmit={handleSubmit(onSubmitCreateOrganization)}
      >
        <input
          type="text"
          name="name"
          className={Classes.INPUT}
          placeholder="New organization name"
          ref={register}
          style={{ flexGrow: 1 }}
        />
        <Button
          type="submit"
          icon="insert"
          style={{ marginLeft: '20px' }}
          loading={formState.isSubmitting}
        >
          Create Organization
        </Button>
      </form>
      <ButtonList>
        {organizations.data.map(organization => (
          <LinkButton
            key={organization.id}
            to={`/support/orgs/${organization.id}`}
            intent={Intent.PRIMARY}
          >
            {organization.name}
          </LinkButton>
        ))}
      </ButtonList>
    </Column>
  )
}

const Table = styled(HTMLTable)`
  margin-top: 10px;
  width: 100%;
  table-layout: fixed;
  td:first-child {
    overflow: hidden;
    text-overflow: ellipsis;
  }
  td:last-child {
    width: 150px;
  }
  tr td {
    vertical-align: baseline;
  }
`

const Organization = ({ organizationId }: { organizationId: string }) => {
  const organization = useOrganization(organizationId)
  const createAuditAdmin = useCreateAuditAdmin()

  const { register, handleSubmit, reset, formState } = useForm<IAuditAdmin>()

  if (organization.isLoading || organization.isIdle) return null
  if (organization.isError) {
    toast.error(organization.error.message)
    return null
  }

  const onSubmitCreateAuditAdmin = async (auditAdmin: IAuditAdmin) => {
    try {
      await createAuditAdmin.mutateAsync({ organizationId, auditAdmin })
      reset()
    } catch (error) {
      toast.error(error.message)
    }
  }

  const { name, elections, auditAdmins } = organization.data

  return (
    <div style={{ width: '100%' }}>
      <H2>{name}</H2>
      <div style={{ display: 'flex', width: '100%' }}>
        <Column>
          <H3>Audits</H3>
          <ButtonList>
            {elections.map(election => (
              <LinkButton
                key={election.id}
                to={`/support/audits/${election.id}`}
                intent={Intent.PRIMARY}
              >
                {election.auditName}
              </LinkButton>
            ))}
          </ButtonList>
        </Column>
        <Column>
          <H3>Audit Admins</H3>
          <form
            style={{ display: 'flex' }}
            onSubmit={handleSubmit(onSubmitCreateAuditAdmin)}
          >
            <input
              type="text"
              name="email"
              className={Classes.INPUT}
              placeholder="New admin email"
              ref={register}
              style={{ flexGrow: 1 }}
            />
            <Button
              type="submit"
              icon="new-person"
              style={{ marginLeft: '20px' }}
              loading={formState.isSubmitting}
            >
              Create Audit Admin
            </Button>
          </form>
          <Table striped>
            <tbody>
              {auditAdmins.map(auditAdmin => (
                <tr key={auditAdmin.email}>
                  <td>{auditAdmin.email}</td>
                  <td>
                    <AnchorButton
                      icon="log-in"
                      style={{ marginLeft: '20px' }}
                      href={`/api/support/audit-admins/${auditAdmin.email}/login`}
                    >
                      Log in as
                    </AnchorButton>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Column>
      </div>
    </div>
  )
}

const prettyAuditType = (auditType: IElection['auditType']) =>
  ({
    BALLOT_POLLING: 'Ballot Polling',
    BALLOT_COMPARISON: 'Ballot Comparison',
    BATCH_COMPARISON: 'Batch Comparison',
  }[auditType])

const Audit = ({ electionId }: { electionId: string }) => {
  const election = useElection(electionId)

  if (election.isLoading || election.isIdle) return null
  if (election.isError) {
    toast.error(election.error.message)
    return null
  }

  const { auditName, auditType, jurisdictions } = election.data

  return (
    <Column>
      <H2>{auditName}</H2>
      <Tag large style={{ marginBottom: '15px' }}>
        {prettyAuditType(auditType)}
      </Tag>
      <H3>Jurisdictions</H3>
      {jurisdictions.map(jurisdiction => (
        <div key={jurisdiction.id} style={{ marginTop: '15px' }}>
          <H4>{jurisdiction.name}</H4>
          <Table striped>
            <tbody>
              {jurisdiction.jurisdictionAdmins.map(jurisdictionAdmin => (
                <tr key={jurisdictionAdmin.email}>
                  <td>{jurisdictionAdmin.email}</td>
                  <td>
                    <AnchorButton
                      icon="log-in"
                      style={{ marginLeft: '20px' }}
                      href={`/api/support/jurisdiction-admins/${jurisdictionAdmin.email}/login`}
                    >
                      Log in as
                    </AnchorButton>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      ))}
    </Column>
  )
}

export default SupportTools
